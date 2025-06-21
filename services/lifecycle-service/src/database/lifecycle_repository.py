"""
Lifecycle Repository - Database operations per il lifecycle service
Gestisce tutte le operazioni database per il lifecycle delle serie
"""

import asyncio
import asyncpg
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)

class LifecycleStage(Enum):
    """Stages del lifecycle delle serie"""
    UPCOMING = "upcoming"
    GRACE_PERIOD = "grace_period"
    EXTENDED_GRACE = "extended_grace"
    ACTIVE_TRACKING = "active_tracking"
    ARCHIVED = "archived"
    READY_FOR_DELETION = "ready_for_deletion"

class LifecycleRepository:
    """Repository per operazioni database del lifecycle"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        logger.info("🗄️  Lifecycle Repository inizializzato")
    
    async def get_connection(self):
        """Ottieni connessione al database"""
        return await asyncpg.connect(self.database_url)
    
    async def ensure_schema(self):
        """Assicura che lo schema del database sia aggiornato"""
        conn = await self.get_connection()
        
        try:
            # Verifica se le colonne lifecycle esistono
            result = await conn.fetchval('''
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'anilist_media' 
                  AND column_name = 'lifecycle_stage'
            ''')
            
            if result == 0:
                logger.warning("⚠️  Schema lifecycle non trovato, creazione necessaria")
                await self._create_lifecycle_schema(conn)
            else:
                logger.info("✅ Schema lifecycle già presente")
                
        finally:
            await conn.close()
    
    async def _create_lifecycle_schema(self, conn):
        """Crea lo schema necessario per il lifecycle"""
        lifecycle_columns = [
            "ALTER TABLE anilist_media ADD COLUMN IF NOT EXISTS lifecycle_stage VARCHAR(50) DEFAULT 'unknown'",
            "ALTER TABLE anilist_media ADD COLUMN IF NOT EXISTS grace_period_start TIMESTAMP",
            "ALTER TABLE anilist_media ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP",
            "ALTER TABLE anilist_media ADD COLUMN IF NOT EXISTS lifecycle_notes TEXT",
            "ALTER TABLE anilist_media ADD COLUMN IF NOT EXISTS last_evaluation_at TIMESTAMP DEFAULT NOW()",
            "ALTER TABLE anilist_media ADD COLUMN IF NOT EXISTS evaluation_score DECIMAL(10,2)",
        ]
        
        for sql in lifecycle_columns:
            await conn.execute(sql)
            logger.info(f"✅ Schema: {sql}")
    
    async def get_series_by_lifecycle_stage(self, stage: LifecycleStage, limit: int = 50) -> List[Dict]:
        """Ottieni serie per stage del lifecycle"""
        conn = await self.get_connection()
        
        try:
            series = await conn.fetch('''
                SELECT 
                    am.id, am.anilist_id, am.title, am.status,
                    am.lifecycle_stage, am.grace_period_start, am.archived_at,
                    am.popularity, am.favourites, am.trending,
                    am.created_at, am.updated_at,
                    am.evaluation_score, am.last_evaluation_at,
                    am.lifecycle_notes,
                    COUNT(DISTINCT c.id) as character_count,
                    AVG(COALESCE(c.trending_score, 0)) as avg_character_trending,
                    MAX(COALESCE(c.trending_score, 0)) as max_character_trending
                FROM anilist_media am
                LEFT JOIN characters c ON c.series ILIKE '%' || am.title || '%'
                WHERE am.lifecycle_stage = $1
                GROUP BY am.id, am.anilist_id, am.title, am.status, 
                         am.lifecycle_stage, am.grace_period_start, am.archived_at,
                         am.popularity, am.favourites, am.trending,
                         am.created_at, am.updated_at,
                         am.evaluation_score, am.last_evaluation_at,
                         am.lifecycle_notes
                ORDER BY am.updated_at DESC
                LIMIT $2
            ''', stage.value, limit)
            
            return [dict(row) for row in series]
            
        finally:
            await conn.close()
    
    async def get_expired_grace_period_series(self, grace_days: int = 42) -> List[Dict]:
        """Ottieni serie con periodo di grazia scaduto"""
        conn = await self.get_connection()
        
        try:
            series = await conn.fetch('''
                SELECT 
                    am.id, am.anilist_id, am.title, am.status,
                    am.lifecycle_stage, am.grace_period_start, am.archived_at,
                    am.popularity, am.favourites, am.trending,
                    am.evaluation_score, am.last_evaluation_at,
                    COUNT(DISTINCT c.id) as character_count,
                    AVG(COALESCE(c.trending_score, 0)) as avg_character_trending,
                    MAX(COALESCE(c.trending_score, 0)) as max_character_trending,
                    EXTRACT(DAYS FROM NOW() - am.grace_period_start) as days_in_grace
                FROM anilist_media am
                LEFT JOIN characters c ON c.series ILIKE '%' || am.title || '%'
                WHERE am.lifecycle_stage IN ('grace_period', 'extended_grace')
                  AND am.grace_period_start IS NOT NULL
                  AND am.grace_period_start < NOW() - INTERVAL '%s days'
                GROUP BY am.id, am.anilist_id, am.title, am.status, 
                         am.lifecycle_stage, am.grace_period_start, am.archived_at,
                         am.popularity, am.favourites, am.trending,
                         am.evaluation_score, am.last_evaluation_at
                ORDER BY am.grace_period_start ASC
            ''' % grace_days)
            
            return [dict(row) for row in series]
            
        finally:
            await conn.close()
    
    async def get_series_requiring_status_update(self, limit: int = 50) -> List[Dict]:
        """Ottieni serie che potrebbero aver cambiato status"""
        conn = await self.get_connection()
        
        try:
            series = await conn.fetch('''
                SELECT 
                    id, anilist_id, title, status, 
                    created_at, updated_at, lifecycle_stage
                FROM anilist_media
                WHERE (
                    -- Serie NOT_YET_RELEASED che potrebbero essere iniziate
                    (status = 'NOT_YET_RELEASED' AND lifecycle_stage = 'upcoming')
                    OR
                    -- Serie non valutate di recente
                    (last_evaluation_at IS NULL OR last_evaluation_at < NOW() - INTERVAL '7 days')
                    OR
                    -- Serie in grace period da valutare
                    (lifecycle_stage IN ('grace_period', 'extended_grace'))
                )
                ORDER BY COALESCE(last_evaluation_at, '1970-01-01'::timestamp) ASC
                LIMIT $1
            ''', limit)
            
            return [dict(row) for row in series]
            
        finally:
            await conn.close()
    
    async def update_series_lifecycle_stage(self, series_id: int, stage: LifecycleStage, 
                                          evaluation_score: Optional[float] = None,
                                          notes: Optional[str] = None):
        """Aggiorna lo stage del lifecycle di una serie"""
        conn = await self.get_connection()
        
        try:
            # Prepara i parametri per l'update
            params = [series_id, stage.value]
            set_clauses = [
                "lifecycle_stage = $2",
                "last_evaluation_at = NOW()",
                "updated_at = NOW()"
            ]
            
            param_count = 3
            
            if evaluation_score is not None:
                set_clauses.append(f"evaluation_score = ${param_count}")
                params.append(evaluation_score)
                param_count += 1
            
            if notes:
                set_clauses.append(f"lifecycle_notes = ${param_count}")
                params.append(notes)
                param_count += 1
            
            # Campi speciali per stage specifici
            if stage == LifecycleStage.GRACE_PERIOD:
                set_clauses.append("grace_period_start = NOW()")
            elif stage == LifecycleStage.EXTENDED_GRACE:
                set_clauses.append("grace_period_start = NOW()")
            elif stage == LifecycleStage.ARCHIVED:
                set_clauses.append("archived_at = NOW()")
            
            query = f'''
                UPDATE anilist_media 
                SET {', '.join(set_clauses)}
                WHERE id = $1
                RETURNING id, title, lifecycle_stage, evaluation_score
            '''
            
            result = await conn.fetchrow(query, *params)
            
            if result:
                logger.info(f"📊 Serie {result['id']} ({result['title']}): {result['lifecycle_stage']}")
                return dict(result)
            else:
                logger.warning(f"⚠️  Serie {series_id} non trovata per aggiornamento")
                return None
            
        finally:
            await conn.close()
    
    async def get_lifecycle_statistics(self) -> Dict[str, Any]:
        """Ottieni statistiche complete del lifecycle"""
        conn = await self.get_connection()
        
        try:
            # Statistiche base per stage
            base_stats = await conn.fetchrow('''
                SELECT 
                    COUNT(*) as total_series,
                    COUNT(*) FILTER (WHERE lifecycle_stage = 'upcoming') as upcoming,
                    COUNT(*) FILTER (WHERE lifecycle_stage = 'grace_period') as grace_period,
                    COUNT(*) FILTER (WHERE lifecycle_stage = 'extended_grace') as extended_grace,
                    COUNT(*) FILTER (WHERE lifecycle_stage = 'active_tracking') as active_tracking,
                    COUNT(*) FILTER (WHERE lifecycle_stage = 'archived') as archived,
                    COUNT(*) FILTER (WHERE lifecycle_stage = 'ready_for_deletion') as ready_for_deletion,
                    COUNT(*) FILTER (WHERE lifecycle_stage = 'unknown') as unknown_stage
                FROM anilist_media
            ''')
            
            # Statistiche per status AniList
            status_stats = await conn.fetchrow('''
                SELECT 
                    COUNT(*) FILTER (WHERE status = 'NOT_YET_RELEASED') as not_yet_released,
                    COUNT(*) FILTER (WHERE status = 'RELEASING') as currently_releasing,
                    COUNT(*) FILTER (WHERE status = 'FINISHED') as finished,
                    COUNT(*) FILTER (WHERE status = 'CANCELLED') as cancelled
                FROM anilist_media
            ''')
            
            # Statistiche temporali
            time_stats = await conn.fetchrow('''
                SELECT 
                    COUNT(*) FILTER (WHERE grace_period_start > NOW() - INTERVAL '7 days') as new_in_grace_week,
                    COUNT(*) FILTER (WHERE archived_at > NOW() - INTERVAL '7 days') as archived_this_week,
                    COUNT(*) FILTER (WHERE last_evaluation_at > NOW() - INTERVAL '24 hours') as evaluated_today,
                    AVG(evaluation_score) FILTER (WHERE evaluation_score IS NOT NULL) as avg_evaluation_score,
                    MIN(grace_period_start) as oldest_grace_period,
                    MAX(archived_at) as most_recent_archive
                FROM anilist_media
            ''')
            
            # Statistiche performance
            perf_stats = await conn.fetchrow('''
                SELECT 
                    AVG(COALESCE(popularity, 0)) as avg_popularity,
                    AVG(COALESCE(favourites, 0)) as avg_favourites,
                    AVG(COALESCE(trending, 0)) as avg_trending,
                    COUNT(*) FILTER (WHERE popularity > 50) as high_popularity_count,
                    COUNT(*) FILTER (WHERE favourites > 100) as high_favourites_count,
                    COUNT(*) FILTER (WHERE evaluation_score > 50) as high_score_count
                FROM anilist_media
                WHERE lifecycle_stage IN ('grace_period', 'extended_grace', 'active_tracking')
            ''')
            
            return {
                'lifecycle_stages': dict(base_stats),
                'anilist_status': dict(status_stats),
                'temporal': dict(time_stats),
                'performance': dict(perf_stats),
                'generated_at': datetime.now().isoformat()
            }
            
        finally:
            await conn.close()
    
    async def cleanup_old_archived_series(self, days_threshold: int = 90) -> int:
        """Marca per cancellazione le serie archiviate da troppo tempo"""
        conn = await self.get_connection()
        
        try:
            result = await conn.execute('''
                UPDATE anilist_media 
                SET lifecycle_stage = 'ready_for_deletion',
                    updated_at = NOW(),
                    lifecycle_notes = COALESCE(lifecycle_notes, '') || 
                                    '; Auto-marked for deletion after ' || $1 || ' days'
                WHERE lifecycle_stage = 'archived'
                  AND archived_at IS NOT NULL
                  AND archived_at < NOW() - INTERVAL '%s days'
            ''' % days_threshold, days_threshold)
            
            # Estrai il numero di righe aggiornate
            rows_updated = int(result.split()[-1]) if result.startswith('UPDATE') else 0
            
            if rows_updated > 0:
                logger.info(f"🗑️  Marcate {rows_updated} serie per cancellazione")
            
            return rows_updated
            
        finally:
            await conn.close()
    
    async def get_series_by_id(self, series_id: int) -> Optional[Dict]:
        """Ottieni una serie specifica per ID"""
        conn = await self.get_connection()
        
        try:
            series = await conn.fetchrow('''
                SELECT 
                    am.id, am.anilist_id, am.title, am.status,
                    am.lifecycle_stage, am.grace_period_start, am.archived_at,
                    am.popularity, am.favourites, am.trending,
                    am.created_at, am.updated_at,
                    am.evaluation_score, am.last_evaluation_at,
                    am.lifecycle_notes,
                    COUNT(DISTINCT c.id) as character_count,
                    AVG(COALESCE(c.trending_score, 0)) as avg_character_trending,
                    MAX(COALESCE(c.trending_score, 0)) as max_character_trending
                FROM anilist_media am
                LEFT JOIN characters c ON c.series ILIKE '%' || am.title || '%'
                WHERE am.id = $1
                GROUP BY am.id, am.anilist_id, am.title, am.status, 
                         am.lifecycle_stage, am.grace_period_start, am.archived_at,
                         am.popularity, am.favourites, am.trending,
                         am.created_at, am.updated_at,
                         am.evaluation_score, am.last_evaluation_at,
                         am.lifecycle_notes
            ''', series_id)
            
            return dict(series) if series else None
            
        finally:
            await conn.close()
    
    async def get_series_by_lifecycle_stage_with_id(self, series_id: int) -> List[Dict]:
        """Wrapper per compatibilità con decision_maker"""
        series = await self.get_series_by_id(series_id)
        return [series] if series else []
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica la salute del database e delle connessioni"""
        try:
            conn = await self.get_connection()
            
            # Test query semplice
            start_time = datetime.now()
            result = await conn.fetchval('SELECT COUNT(*) FROM anilist_media')
            query_time = (datetime.now() - start_time).total_seconds()
            
            await conn.close()
            
            return {
                'database_connected': True,
                'query_time_seconds': query_time,
                'total_series': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Health check fallito: {e}")
            return {
                'database_connected': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
