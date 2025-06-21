"""
Series Lifecycle Repository
Gestisce le operazioni database per il lifecycle delle serie
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

class SeriesLifecycleRepository:
    """Repository per operazioni lifecycle delle serie"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
    
    async def get_connection(self):
        """Ottieni connessione database"""
        return await asyncpg.connect(self.database_url)
    
    async def get_series_by_lifecycle_stage(self, stage: LifecycleStage, limit: int = 50) -> List[Dict]:
        """Ottieni serie per stage del lifecycle"""
        conn = await self.get_connection()
        
        try:
            series = await conn.fetch('''
                SELECT 
                    am.id, am.anilist_id, am.title, am.status,
                    am.lifecycle_stage, am.grace_period_start, am.archived_at,
                    am.popularity, am.favourites, am.trending,
                    am.start_date, am.end_date, am.created_at, am.updated_at,
                    am.evaluation_score, am.last_evaluation_at,
                    COUNT(DISTINCT c.id) as character_count,
                    AVG(COALESCE(c.trending_score, 0)) as avg_character_trending,
                    MAX(COALESCE(c.trending_score, 0)) as max_character_trending
                FROM anilist_media am
                LEFT JOIN characters c ON c.series ILIKE '%' || am.title || '%'
                WHERE am.lifecycle_stage = $1
                GROUP BY am.id, am.anilist_id, am.title, am.status, 
                         am.lifecycle_stage, am.grace_period_start, am.archived_at,
                         am.popularity, am.favourites, am.trending,
                         am.start_date, am.end_date, am.created_at, am.updated_at,
                         am.evaluation_score, am.last_evaluation_at
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
                    COUNT(DISTINCT c.id) as character_count,
                    AVG(COALESCE(c.trending_score, 0)) as avg_character_trending,
                    MAX(COALESCE(c.trending_score, 0)) as max_character_trending,
                    EXTRACT(DAYS FROM NOW() - am.grace_period_start) as days_in_grace
                FROM anilist_media am
                LEFT JOIN characters c ON c.series ILIKE '%' || am.title || '%'
                WHERE am.lifecycle_stage IN ('grace_period', 'extended_grace')
                  AND am.grace_period_start < NOW() - INTERVAL '{} days'
                GROUP BY am.id, am.anilist_id, am.title, am.status, 
                         am.lifecycle_stage, am.grace_period_start, am.archived_at,
                         am.popularity, am.favourites, am.trending
                ORDER BY am.grace_period_start ASC
            '''.format(grace_days))
            
            return [dict(row) for row in series]
            
        finally:
            await conn.close()
    
    async def update_series_lifecycle_stage(self, series_id: int, stage: LifecycleStage, 
                                          evaluation_score: Optional[float] = None,
                                          notes: Optional[str] = None):
        """Aggiorna lo stage del lifecycle di una serie"""
        conn = await self.get_connection()
        
        try:
            update_fields = {
                'lifecycle_stage': stage.value,
                'last_evaluation_at': 'NOW()',
                'updated_at': 'NOW()'
            }
            
            if evaluation_score is not None:
                update_fields['evaluation_score'] = evaluation_score
            
            if notes:
                update_fields['lifecycle_notes'] = notes
            
            # Campi speciali per stage specifici
            if stage == LifecycleStage.GRACE_PERIOD:
                update_fields['grace_period_start'] = 'NOW()'
            elif stage == LifecycleStage.EXTENDED_GRACE:
                update_fields['grace_period_start'] = 'NOW()'
            elif stage == LifecycleStage.ARCHIVED:
                update_fields['archived_at'] = 'NOW()'
            
            # Costruisci query dinamicamente
            set_clauses = []
            values = [series_id]
            param_count = 2
            
            for field, value in update_fields.items():
                if value == 'NOW()':
                    set_clauses.append(f"{field} = NOW()")
                else:
                    set_clauses.append(f"{field} = ${param_count}")
                    values.append(value)
                    param_count += 1
            
            query = f'''
                UPDATE anilist_media 
                SET {', '.join(set_clauses)}
                WHERE id = $1
                RETURNING id, title, lifecycle_stage
            '''
            
            result = await conn.fetchrow(query, *values)
            return dict(result) if result else None
            
        finally:
            await conn.close()
    
    async def get_lifecycle_statistics(self) -> Dict[str, Any]:
        """Ottieni statistiche complete del lifecycle"""
        conn = await self.get_connection()
        
        try:
            # Statistiche base
            base_stats = await conn.fetchrow('''
                SELECT 
                    COUNT(*) as total_series,
                    COUNT(*) FILTER (WHERE lifecycle_stage = 'upcoming') as upcoming,
                    COUNT(*) FILTER (WHERE lifecycle_stage = 'grace_period') as grace_period,
                    COUNT(*) FILTER (WHERE lifecycle_stage = 'extended_grace') as extended_grace,
                    COUNT(*) FILTER (WHERE lifecycle_stage = 'active_tracking') as active_tracking,
                    COUNT(*) FILTER (WHERE lifecycle_stage = 'archived') as archived,
                    COUNT(*) FILTER (WHERE lifecycle_stage = 'ready_for_deletion') as ready_for_deletion,
                    COUNT(*) FILTER (WHERE status = 'NOT_YET_RELEASED') as not_yet_released,
                    COUNT(*) FILTER (WHERE status = 'RELEASING') as currently_releasing,
                    COUNT(*) FILTER (WHERE status = 'FINISHED') as finished
                FROM anilist_media
            ''')
            
            # Statistiche temporali
            time_stats = await conn.fetchrow('''
                SELECT 
                    COUNT(*) FILTER (WHERE grace_period_start > NOW() - INTERVAL '7 days') as new_in_grace_week,
                    COUNT(*) FILTER (WHERE archived_at > NOW() - INTERVAL '7 days') as archived_this_week,
                    COUNT(*) FILTER (WHERE last_evaluation_at > NOW() - INTERVAL '24 hours') as evaluated_today,
                    AVG(evaluation_score) FILTER (WHERE evaluation_score IS NOT NULL) as avg_evaluation_score
                FROM anilist_media
            ''')
            
            # Statistiche performance
            perf_stats = await conn.fetchrow('''
                SELECT 
                    AVG(popularity) as avg_popularity,
                    AVG(favourites) as avg_favourites,
                    AVG(trending) as avg_trending,
                    COUNT(*) FILTER (WHERE popularity > 50) as high_popularity_count,
                    COUNT(*) FILTER (WHERE favourites > 100) as high_favourites_count
                FROM anilist_media
                WHERE lifecycle_stage IN ('grace_period', 'extended_grace', 'active_tracking')
            ''')
            
            return {
                'base': dict(base_stats),
                'temporal': dict(time_stats),
                'performance': dict(perf_stats),
                'generated_at': datetime.now().isoformat()
            }
            
        finally:
            await conn.close()
    
    async def get_series_requiring_status_update(self, limit: int = 50) -> List[Dict]:
        """Ottieni serie che potrebbero aver cambiato status su AniList"""
        conn = await self.get_connection()
        
        try:
            series = await conn.fetch('''
                SELECT id, anilist_id, title, status, start_date, end_date, updated_at
                FROM anilist_media
                WHERE (
                    -- Serie NOT_YET_RELEASED che potrebbero essere iniziate
                    (status = 'NOT_YET_RELEASED' AND start_date <= CURRENT_DATE)
                    OR
                    -- Serie non aggiornate da più di una settimana
                    (updated_at < NOW() - INTERVAL '7 days')
                    OR
                    -- Serie RELEASING che potrebbero essere finite
                    (status = 'RELEASING' AND end_date IS NOT NULL AND end_date <= CURRENT_DATE)
                )
                ORDER BY updated_at ASC
                LIMIT $1
            ''', limit)
            
            return [dict(row) for row in series]
            
        finally:
            await conn.close()
    
    async def cleanup_old_archived_series(self, days_threshold: int = 90) -> int:
        """Marca per cancellazione le serie archiviate da troppo tempo"""
        conn = await self.get_connection()
        
        try:
            result = await conn.execute('''
                UPDATE anilist_media 
                SET lifecycle_stage = 'ready_for_deletion',
                    updated_at = NOW()
                WHERE lifecycle_stage = 'archived'
                  AND archived_at < NOW() - INTERVAL '{} days'
            '''.format(days_threshold))
            
            # Estrai il numero di righe aggiornate dal risultato
            return int(result.split()[-1]) if result.startswith('UPDATE') else 0
            
        finally:
            await conn.close()
    
    async def get_series_performance_history(self, series_id: int, days: int = 30) -> List[Dict]:
        """Ottieni cronologia performance di una serie (se abbiamo snapshot)"""
        conn = await self.get_connection()
        
        try:
            # Verifica se abbiamo snapshot per questa serie
            snapshots = await conn.fetch('''
                SELECT 
                    snapshot_date,
                    popularity,
                    favourites,
                    trending,
                    created_at
                FROM anilist_trending_media_snapshots
                WHERE anilist_id = (
                    SELECT anilist_id FROM anilist_media WHERE id = $1
                )
                AND snapshot_date >= CURRENT_DATE - INTERVAL '{} days'
                ORDER BY snapshot_date DESC
            '''.format(days), series_id)
            
            return [dict(row) for row in snapshots]
            
        finally:
            await conn.close()
