"""
Lifecycle Engine - Core del servizio lifecycle
Gestisce il ciclo di vita completo delle serie anime/manga
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import json
from pathlib import Path

from .decision_maker import LifecycleDecisionMaker
from .rules_manager import LifecycleRulesManager
from ..database.lifecycle_repository import LifecycleRepository

logger = logging.getLogger(__name__)

class LifecycleStage(Enum):
    """Stages del lifecycle delle serie"""
    UPCOMING = "upcoming"
    GRACE_PERIOD = "grace_period"
    EXTENDED_GRACE = "extended_grace"
    ACTIVE_TRACKING = "active_tracking"
    ARCHIVED = "archived"
    READY_FOR_DELETION = "ready_for_deletion"

class SeriesLifecycleEngine:
    """Engine principale per la gestione del lifecycle delle serie"""
    
    def __init__(self, database_url: str, config_path: Optional[str] = None):
        self.database_url = database_url
        self.repository = LifecycleRepository(database_url)
        self.rules_manager = LifecycleRulesManager(config_path)
        self.decision_maker = LifecycleDecisionMaker(self.rules_manager)
        
        # Metriche di esecuzione
        self.execution_stats = {
            'last_run': None,
            'series_evaluated': 0,
            'decisions_made': 0,
            'archived_count': 0,
            'kept_active_count': 0,
            'errors': []
        }
        
        logger.info("🚀 Lifecycle Engine inizializzato")
    
    async def run_lifecycle_evaluation(self) -> Dict[str, Any]:
        """Esegue una valutazione completa del lifecycle"""
        start_time = datetime.now()
        logger.info("🔄 Avvio valutazione lifecycle completa")
        
        try:
            # Reset statistiche
            self.execution_stats = {
                'last_run': start_time,
                'series_evaluated': 0,
                'decisions_made': 0,
                'archived_count': 0,
                'kept_active_count': 0,
                'errors': []
            }
            
            # 1. Aggiorna status delle serie da AniList
            await self._update_series_status()
            
            # 2. Valuta serie nel periodo di grazia
            grace_results = await self._evaluate_grace_period_series()
            
            # 3. Pulizia serie archiviate vecchie
            cleanup_results = await self._cleanup_old_series()
            
            # 4. Genera report finale
            execution_time = (datetime.now() - start_time).total_seconds()
            
            results = {
                'success': True,
                'execution_time_seconds': execution_time,
                'timestamp': start_time.isoformat(),
                'series_evaluated': self.execution_stats['series_evaluated'],
                'decisions_made': self.execution_stats['decisions_made'],
                'archived_count': self.execution_stats['archived_count'],
                'kept_active_count': self.execution_stats['kept_active_count'],
                'grace_period_results': grace_results,
                'cleanup_results': cleanup_results,
                'errors': self.execution_stats['errors']
            }
            
            logger.info(f"✅ Lifecycle evaluation completata in {execution_time:.2f}s")
            return results
            
        except Exception as e:
            logger.error(f"❌ Errore durante lifecycle evaluation: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': start_time.isoformat(),
                'execution_time_seconds': (datetime.now() - start_time).total_seconds()
            }
    
    async def _update_series_status(self):
        """Aggiorna lo status delle serie che potrebbero essere cambiate"""
        logger.info("📡 Aggiornamento status serie...")
        
        # Ottieni serie che potrebbero aver cambiato status
        series_to_check = await self.repository.get_series_requiring_status_update()
        
        for series in series_to_check:
            try:
                # Logica per determinare se una serie è passata da NOT_YET_RELEASED a RELEASING
                if (series['status'] == 'NOT_YET_RELEASED' and 
                    series.get('start_date') and 
                    series['start_date'] <= datetime.now().date()):
                    
                    # Aggiorna a RELEASING e imposta grace period
                    await self.repository.update_series_lifecycle_stage(
                        series['id'], 
                        LifecycleStage.GRACE_PERIOD,
                        notes="Auto-transition: NOT_YET_RELEASED → RELEASING"
                    )
                    
                    logger.info(f"📺 {series['title']}: Iniziato periodo di grazia")
                    
            except Exception as e:
                error_msg = f"Errore aggiornamento {series['title']}: {e}"
                logger.error(error_msg)
                self.execution_stats['errors'].append(error_msg)
    
    async def _evaluate_grace_period_series(self) -> Dict[str, Any]:
        """Valuta le serie nel periodo di grazia"""
        logger.info("⏰ Valutazione serie in periodo di grazia...")
        
        grace_days = self.rules_manager.get_grace_period_days()
        series_list = await self.repository.get_expired_grace_period_series(grace_days)
        
        decisions = []
        for series in series_list:
            try:
                # Usa il decision maker per decidere
                decision = await self.decision_maker.make_lifecycle_decision(series)
                
                # Applica la decisione
                await self._apply_decision(series, decision)
                
                decisions.append({
                    'series_id': series['id'],
                    'title': series['title'],
                    'decision': decision['action'],
                    'reason': decision['reason'],
                    'score': decision['composite_score']
                })
                
                self.execution_stats['series_evaluated'] += 1
                self.execution_stats['decisions_made'] += 1
                
                if decision['action'] == 'ARCHIVE':
                    self.execution_stats['archived_count'] += 1
                elif decision['action'] == 'KEEP_ACTIVE':
                    self.execution_stats['kept_active_count'] += 1
                
            except Exception as e:
                error_msg = f"Errore valutazione {series['title']}: {e}"
                logger.error(error_msg)
                self.execution_stats['errors'].append(error_msg)
        
        return {
            'evaluated_series': len(series_list),
            'decisions': decisions
        }
    
    async def _apply_decision(self, series: Dict, decision: Dict):
        """Applica una decisione del lifecycle"""
        action = decision['action']
        
        if action == 'KEEP_ACTIVE':
            await self.repository.update_series_lifecycle_stage(
                series['id'],
                LifecycleStage.ACTIVE_TRACKING,
                evaluation_score=decision['composite_score'],
                notes=decision['reason']
            )
            logger.info(f"✅ {series['title']}: Mantenuto in tracking attivo")
            
        elif action == 'EXTEND_GRACE':
            await self.repository.update_series_lifecycle_stage(
                series['id'],
                LifecycleStage.EXTENDED_GRACE,
                evaluation_score=decision['composite_score'],
                notes=decision['reason']
            )
            logger.info(f"⏳ {series['title']}: Esteso periodo di grazia")
            
        elif action == 'ARCHIVE':
            await self.repository.update_series_lifecycle_stage(
                series['id'],
                LifecycleStage.ARCHIVED,
                evaluation_score=decision['composite_score'],
                notes=decision['reason']
            )
            logger.info(f"📦 {series['title']}: Archiviato")
    
    async def _cleanup_old_series(self) -> Dict[str, Any]:
        """Pulizia serie archiviate troppo vecchie"""
        logger.info("🗑️  Pulizia serie archiviate...")
        
        cleanup_days = self.rules_manager.get_cleanup_days()
        cleaned_count = await self.repository.cleanup_old_archived_series(cleanup_days)
        
        return {
            'cleaned_series': cleaned_count,
            'cleanup_threshold_days': cleanup_days
        }
    
    async def get_lifecycle_statistics(self) -> Dict[str, Any]:
        """Ottieni statistiche complete del lifecycle"""
        stats = await self.repository.get_lifecycle_statistics()
        
        # Aggiungi statistiche di esecuzione
        stats['execution_stats'] = self.execution_stats
        stats['rules_config'] = self.rules_manager.get_current_config()
        
        return stats
    
    async def force_archive_series(self, series_id: int, reason: str = "Manual archive") -> bool:
        """Forza l'archiviazione di una serie specifica"""
        try:
            await self.repository.update_series_lifecycle_stage(
                series_id,
                LifecycleStage.ARCHIVED,
                notes=f"Manual archive: {reason}"
            )
            logger.info(f"📦 Serie {series_id} archiviata manualmente: {reason}")
            return True
        except Exception as e:
            logger.error(f"❌ Errore archiviazione manuale serie {series_id}: {e}")
            return False
    
    async def restore_series(self, series_id: int, reason: str = "Manual restore") -> bool:
        """Ripristina una serie dall'archivio"""
        try:
            await self.repository.update_series_lifecycle_stage(
                series_id,
                LifecycleStage.ACTIVE_TRACKING,
                notes=f"Manual restore: {reason}"
            )
            logger.info(f"🔄 Serie {series_id} ripristinata: {reason}")
            return True
        except Exception as e:
            logger.error(f"❌ Errore ripristino serie {series_id}: {e}")
            return False
