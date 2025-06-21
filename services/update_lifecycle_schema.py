#!/usr/bin/env python3
"""
Database Schema Update per Series Lifecycle Management
Aggiunge le colonne necessarie per gestire il ciclo di vita delle serie
"""

import asyncio
import asyncpg
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://cosplayradar:dev_password_123@localhost:5432/cosplayradar_dev"

async def update_schema():
    """Aggiorna lo schema del database per il lifecycle management"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        logger.info("🔧 Aggiornamento schema database per lifecycle management...")
        
        # Aggiungi colonne per lifecycle management
        lifecycle_columns = [
            "ALTER TABLE anilist_media ADD COLUMN IF NOT EXISTS lifecycle_stage VARCHAR(50) DEFAULT 'unknown'",
            "ALTER TABLE anilist_media ADD COLUMN IF NOT EXISTS grace_period_start TIMESTAMP",
            "ALTER TABLE anilist_media ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP",
            "ALTER TABLE anilist_media ADD COLUMN IF NOT EXISTS lifecycle_notes TEXT",
            "ALTER TABLE anilist_media ADD COLUMN IF NOT EXISTS last_evaluation_at TIMESTAMP DEFAULT NOW()",
            "ALTER TABLE anilist_media ADD COLUMN IF NOT EXISTS evaluation_score DECIMAL(10,2)",
        ]
        
        for sql in lifecycle_columns:
            try:
                await conn.execute(sql)
                logger.info(f"✅ Eseguito: {sql}")
            except Exception as e:
                logger.warning(f"⚠️  Possibile colonna già esistente: {e}")
        
        # Crea indici per performance
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_anilist_media_lifecycle_stage ON anilist_media(lifecycle_stage)",
            "CREATE INDEX IF NOT EXISTS idx_anilist_media_grace_period ON anilist_media(grace_period_start) WHERE grace_period_start IS NOT NULL",
            "CREATE INDEX IF NOT EXISTS idx_anilist_media_archived ON anilist_media(archived_at) WHERE archived_at IS NOT NULL",
            "CREATE INDEX IF NOT EXISTS idx_anilist_media_evaluation ON anilist_media(last_evaluation_at, evaluation_score)",
        ]
        
        for sql in indices:
            try:
                await conn.execute(sql)
                logger.info(f"✅ Indice creato: {sql}")
            except Exception as e:
                logger.warning(f"⚠️  Indice già esistente o errore: {e}")
        
        # Inizializza i dati esistenti
        logger.info("🔄 Inizializzazione dati esistenti...")
        
        # Serie NOT_YET_RELEASED → upcoming
        await conn.execute('''
            UPDATE anilist_media 
            SET lifecycle_stage = 'upcoming'
            WHERE status = 'NOT_YET_RELEASED' AND lifecycle_stage = 'unknown'
        ''')
        
        # Serie RELEASING con data recente → grace_period
        await conn.execute('''
            UPDATE anilist_media 
            SET lifecycle_stage = 'grace_period',
                grace_period_start = COALESCE(start_date::timestamp, created_at, NOW() - INTERVAL '30 days')
            WHERE status = 'RELEASING' 
              AND lifecycle_stage = 'unknown'
              AND (start_date IS NULL OR start_date >= CURRENT_DATE - INTERVAL '60 days')
        ''')
        
        # Serie RELEASING più vecchie → active_tracking
        await conn.execute('''
            UPDATE anilist_media 
            SET lifecycle_stage = 'active_tracking'
            WHERE status = 'RELEASING' 
              AND lifecycle_stage = 'unknown'
              AND start_date < CURRENT_DATE - INTERVAL '60 days'
        ''')
        
        # Serie FINISHED → archived
        await conn.execute('''
            UPDATE anilist_media 
            SET lifecycle_stage = 'archived',
                archived_at = COALESCE(end_date::timestamp, updated_at, NOW())
            WHERE status = 'FINISHED' AND lifecycle_stage = 'unknown'
        ''')
        
        # Verifica risultati
        stats = await conn.fetchrow('''
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE lifecycle_stage = 'upcoming') as upcoming,
                COUNT(*) FILTER (WHERE lifecycle_stage = 'grace_period') as grace_period,
                COUNT(*) FILTER (WHERE lifecycle_stage = 'active_tracking') as active_tracking,
                COUNT(*) FILTER (WHERE lifecycle_stage = 'archived') as archived,
                COUNT(*) FILTER (WHERE lifecycle_stage = 'unknown') as unknown
            FROM anilist_media
        ''')
        
        logger.info("📊 Statistiche dopo inizializzazione:")
        for key, value in dict(stats).items():
            logger.info(f"  • {key}: {value}")
        
        logger.info("✅ Schema aggiornato con successo!")
        
    except Exception as e:
        logger.error(f"❌ Errore aggiornamento schema: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(update_schema())
