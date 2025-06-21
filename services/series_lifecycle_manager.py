#!/usr/bin/env python3
"""
Series Lifecycle Manager for CosplayRadar
Gestisce il ciclo di vita delle serie da "in uscita" a "pubblicate" a "archiviate"

Strategy:
1. Serie NOT_YET_RELEASED → RELEASING (quando escono)
2. Periodo di grazia di 6-8 settimane dopo release
3. Valutazione trend/popolarità per decidere se mantenere o archiviare
4. Rotazione intelligente per mantenere database efficiente
"""

import asyncio
import logging
import asyncpg
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SeriesStatus(Enum):
    """Status delle serie nel nostro sistema"""
    NOT_YET_RELEASED = "NOT_YET_RELEASED"
    RELEASING = "RELEASING" 
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"  # Nostro status per serie rimosse dal tracking attivo

class LifecycleDecision(Enum):
    """Decisioni del lifecycle manager"""
    KEEP_ACTIVE = "KEEP_ACTIVE"        # Mantieni tracking attivo
    ARCHIVE = "ARCHIVE"                # Archivia (rimuovi da trending)
    EXTEND_GRACE = "EXTEND_GRACE"      # Estendi periodo di grazia

class SeriesLifecycleManager:
    """Gestisce il ciclo di vita delle serie anime/manga"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        
        # Configurazione periodi (in giorni)
        self.GRACE_PERIOD_DAYS = 42  # 6 settimane
        self.EXTENDED_GRACE_DAYS = 28  # 4 settimane aggiuntive
        
        # Soglie per decisioni intelligenti
        self.MIN_TRENDING_SCORE = 50.0
        self.MIN_POPULARITY_SCORE = 30.0
        self.MIN_FAVOURITES = 100
        self.TRENDING_GROWTH_THRESHOLD = 1.2  # 20% crescita
        
    async def update_series_status(self):
        """Aggiorna lo status delle serie da AniList"""
        conn = await asyncpg.connect(self.database_url)
        
        try:
            logger.info("🔄 Aggiornamento status serie da AniList...")
            
            # Query per serie che potrebbero aver cambiato status
            series_to_check = await conn.fetch('''
                SELECT am.id, am.anilist_id, am.title, am.status, am.start_date, am.updated_at
                FROM anilist_media am
                WHERE am.status IN ('NOT_YET_RELEASED', 'RELEASING')
                   OR (am.updated_at < NOW() - INTERVAL '7 days')
                ORDER BY am.updated_at ASC
                LIMIT 50
            ''')
            
            logger.info(f"📊 Controllando {len(series_to_check)} serie per aggiornamenti status")
            
            # Qui integreresti le chiamate AniList per verificare status attuale
            # Per ora mockup della logica
            
            status_changes = 0
            for series in series_to_check:
                # Simulazione: serie che hanno superato la data di inizio diventano RELEASING
                if (series['status'] == 'NOT_YET_RELEASED' and 
                    series['start_date'] and 
                    series['start_date'] <= datetime.now().date()):
                    
                    await conn.execute('''
                        UPDATE anilist_media 
                        SET status = 'RELEASING', 
                            updated_at = NOW(),
                            lifecycle_stage = 'grace_period',
                            grace_period_start = NOW()
                        WHERE id = $1
                    ''', series['id'])
                    
                    status_changes += 1
                    logger.info(f"📺 {series['title']}: NOT_YET_RELEASED → RELEASING")
            
            logger.info(f"✅ Aggiornati {status_changes} status di serie")
            
        finally:
            await conn.close()
    
    async def evaluate_grace_period_series(self) -> List[Dict[str, Any]]:
        """Valuta le serie nel periodo di grazia per decidere il destino"""
        conn = await asyncpg.connect(self.database_url)
        
        try:
            # Serie che hanno completato il periodo di grazia
            grace_period_expired = await conn.fetch('''
                SELECT 
                    am.id, am.anilist_id, am.title, am.status,
                    am.grace_period_start, am.lifecycle_stage,
                    am.popularity, am.favourites, am.trending,
                    COUNT(DISTINCT c.id) as character_count,
                    AVG(COALESCE(c.trending_score, 0)) as avg_character_trending,
                    MAX(COALESCE(c.trending_score, 0)) as max_character_trending
                FROM anilist_media am
                LEFT JOIN characters c ON c.series ILIKE '%' || am.title || '%'
                WHERE am.lifecycle_stage = 'grace_period'
                  AND am.grace_period_start < NOW() - INTERVAL '{} days'
                GROUP BY am.id, am.anilist_id, am.title, am.status, 
                         am.grace_period_start, am.lifecycle_stage,
                         am.popularity, am.favourites, am.trending
                ORDER BY am.grace_period_start ASC
            '''.format(self.GRACE_PERIOD_DAYS))
            
            logger.info(f"⏰ Valutando {len(grace_period_expired)} serie con periodo di grazia scaduto")
            
            decisions = []
            for series in grace_period_expired:
                decision = await self._make_lifecycle_decision(series)
                decisions.append({
                    'series': series,
                    'decision': decision,
                    'reason': self._get_decision_reason(series, decision)
                })
                
                # Applica la decisione
                await self._apply_lifecycle_decision(conn, series, decision)
            
            return decisions
            
        finally:
            await conn.close()
    
    async def _make_lifecycle_decision(self, series: Dict) -> LifecycleDecision:
        """Prende una decisione intelligente sul destino della serie"""
        
        # Metriche della serie
        popularity = series.get('popularity', 0) or 0
        favourites = series.get('favourites', 0) or 0
        trending = series.get('trending', 0) or 0
        character_count = series.get('character_count', 0) or 0
        avg_char_trending = series.get('avg_character_trending', 0) or 0
        max_char_trending = series.get('max_character_trending', 0) or 0
        
        # Score composito per decisione
        composite_score = (
            (popularity * 0.3) +
            (favourites * 0.2) +
            (trending * 0.2) +
            (character_count * 5) +  # Bonus per avere personaggi
            (avg_char_trending * 0.2) +
            (max_char_trending * 0.1)
        )
        
        logger.info(f"📊 {series['title']}: composite_score={composite_score:.1f}")
        
        # Logica di decisione
        if composite_score >= self.MIN_TRENDING_SCORE:
            if (popularity >= self.MIN_POPULARITY_SCORE or 
                favourites >= self.MIN_FAVOURITES or
                max_char_trending >= 70):
                return LifecycleDecision.KEEP_ACTIVE
        
        # Controllo per estensione grazia
        if (composite_score >= self.MIN_TRENDING_SCORE * 0.7 and
            (popularity > 0 or trending > 0 or character_count > 0)):
            return LifecycleDecision.EXTEND_GRACE
        
        # Default: archivia
        return LifecycleDecision.ARCHIVE
    
    def _get_decision_reason(self, series: Dict, decision: LifecycleDecision) -> str:
        """Genera una spiegazione della decisione presa"""
        if decision == LifecycleDecision.KEEP_ACTIVE:
            return f"Alta performance: pop={series.get('popularity', 0)}, fav={series.get('favourites', 0)}, chars={series.get('character_count', 0)}"
        elif decision == LifecycleDecision.EXTEND_GRACE:
            return f"Performance moderata, estendo grazia per monitoraggio"
        else:
            return f"Performance insufficiente per mantenere tracking attivo"
    
    async def _apply_lifecycle_decision(self, conn, series: Dict, decision: LifecycleDecision):
        """Applica la decisione presa al database"""
        
        if decision == LifecycleDecision.KEEP_ACTIVE:
            await conn.execute('''
                UPDATE anilist_media 
                SET lifecycle_stage = 'active_tracking',
                    updated_at = NOW()
                WHERE id = $1
            ''', series['id'])
            logger.info(f"✅ {series['title']}: Mantenuto in tracking attivo")
            
        elif decision == LifecycleDecision.EXTEND_GRACE:
            await conn.execute('''
                UPDATE anilist_media 
                SET lifecycle_stage = 'extended_grace',
                    grace_period_start = NOW(),
                    updated_at = NOW()
                WHERE id = $1
            ''', series['id'])
            logger.info(f"⏳ {series['title']}: Esteso periodo di grazia")
            
        elif decision == LifecycleDecision.ARCHIVE:
            await conn.execute('''
                UPDATE anilist_media 
                SET lifecycle_stage = 'archived',
                    archived_at = NOW(),
                    updated_at = NOW()
                WHERE id = $1
            ''', series['id'])
            logger.info(f"📦 {series['title']}: Archiviato (rimosso da trending attivo)")
    
    async def cleanup_old_archived_series(self, days_to_keep: int = 90):
        """Pulisce definitivamente le serie archiviate da troppo tempo"""
        conn = await asyncpg.connect(self.database_url)
        
        try:
            # Serie archiviate da più di X giorni
            old_archived = await conn.fetch('''
                SELECT id, title, archived_at
                FROM anilist_media
                WHERE lifecycle_stage = 'archived'
                  AND archived_at < NOW() - INTERVAL '{} days'
            '''.format(days_to_keep))
            
            if old_archived:
                logger.info(f"🗑️  Pulizia {len(old_archived)} serie archiviate da più di {days_to_keep} giorni")
                
                # Opzione 1: Cancellazione fisica (attenzione!)
                # await conn.execute('''
                #     DELETE FROM anilist_media 
                #     WHERE lifecycle_stage = 'archived'
                #       AND archived_at < NOW() - INTERVAL '{} days'
                # '''.format(days_to_keep))
                
                # Opzione 2: Marcatura per pulizia definitiva
                await conn.execute('''
                    UPDATE anilist_media 
                    SET lifecycle_stage = 'ready_for_deletion'
                    WHERE lifecycle_stage = 'archived'
                      AND archived_at < NOW() - INTERVAL '{} days'
                '''.format(days_to_keep))
                
                logger.info(f"✅ Marcate {len(old_archived)} serie per cancellazione definitiva")
        
        finally:
            await conn.close()
    
    async def get_lifecycle_statistics(self) -> Dict[str, Any]:
        """Ottieni statistiche del lifecycle management"""
        conn = await asyncpg.connect(self.database_url)
        
        try:
            stats = await conn.fetchrow('''
                SELECT 
                    COUNT(*) FILTER (WHERE lifecycle_stage = 'grace_period') as in_grace_period,
                    COUNT(*) FILTER (WHERE lifecycle_stage = 'extended_grace') as extended_grace,
                    COUNT(*) FILTER (WHERE lifecycle_stage = 'active_tracking') as active_tracking,
                    COUNT(*) FILTER (WHERE lifecycle_stage = 'archived') as archived,
                    COUNT(*) FILTER (WHERE lifecycle_stage = 'ready_for_deletion') as ready_for_deletion,
                    COUNT(*) FILTER (WHERE status = 'NOT_YET_RELEASED') as upcoming,
                    COUNT(*) FILTER (WHERE status = 'RELEASING') as currently_airing
                FROM anilist_media
            ''')
            
            return dict(stats)
            
        finally:
            await conn.close()

async def main():
    """Test del sistema di lifecycle management"""
    DATABASE_URL = "postgresql://cosplayradar:dev_password_123@localhost:5432/cosplayradar_dev"
    
    manager = SeriesLifecycleManager(DATABASE_URL)
    
    logger.info("🚀 Avvio Series Lifecycle Management")
    
    # 1. Aggiorna status delle serie
    await manager.update_series_status()
    
    # 2. Valuta serie nel periodo di grazia
    decisions = await manager.evaluate_grace_period_series()
    
    if decisions:
        logger.info(f"\n📋 Decisioni prese per {len(decisions)} serie:")
        for decision_info in decisions:
            series = decision_info['series']
            decision = decision_info['decision']
            reason = decision_info['reason']
            logger.info(f"  • {series['title']}: {decision.value} - {reason}")
    
    # 3. Pulizia serie archiviate vecchie
    await manager.cleanup_old_archived_series(days_to_keep=90)
    
    # 4. Statistiche finali
    stats = await manager.get_lifecycle_statistics()
    logger.info(f"\n📊 Statistiche Lifecycle:")
    for key, value in stats.items():
        logger.info(f"  • {key}: {value}")
    
    logger.info("✅ Lifecycle management completato")

if __name__ == "__main__":
    asyncio.run(main())
