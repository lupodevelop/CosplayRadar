"""
API Routes per il Lifecycle Service
Espone endpoint HTTP per la gestione del lifecycle delle serie
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Pydantic models per le richieste
class ArchiveRequest(BaseModel):
    reason: Optional[str] = "Manual archive via API"

class RestoreRequest(BaseModel):
    reason: Optional[str] = "Manual restore via API"

class ConfigUpdateRequest(BaseModel):
    config: Dict[str, Any]

def create_lifecycle_api(lifecycle_engine) -> FastAPI:
    """Crea l'app FastAPI per il lifecycle service"""
    
    app = FastAPI(
        title="CosplayRadar Lifecycle Service",
        description="Servizio per la gestione del ciclo di vita delle serie anime/manga",
        version="1.0.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health")
    async def health_check():
        """Health check del servizio"""
        try:
            db_health = await lifecycle_engine.repository.health_check()
            
            return {
                "status": "healthy" if db_health["database_connected"] else "unhealthy",
                "service": "lifecycle-service",
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
                "database": db_health
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
    
    @app.get("/stats")
    async def get_statistics():
        """Ottieni statistiche complete del lifecycle"""
        try:
            stats = await lifecycle_engine.get_lifecycle_statistics()
            return {
                "success": True,
                "data": stats
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/evaluate")
    async def run_lifecycle_evaluation(background_tasks: BackgroundTasks):
        """Esegui valutazione completa del lifecycle"""
        try:
            # Esegui in background per non bloccare la risposta
            background_tasks.add_task(lifecycle_engine.run_lifecycle_evaluation)
            
            return {
                "success": True,
                "message": "Lifecycle evaluation started in background",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error starting lifecycle evaluation: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/evaluate/status")
    async def get_evaluation_status():
        """Ottieni lo status dell'ultima valutazione"""
        try:
            return {
                "success": True,
                "data": lifecycle_engine.execution_stats
            }
        except Exception as e:
            logger.error(f"Error getting evaluation status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/archive/{series_id}")
    async def archive_series(series_id: int, request: ArchiveRequest):
        """Archivia manualmente una serie specifica"""
        try:
            success = await lifecycle_engine.force_archive_series(series_id, request.reason)
            
            if success:
                return {
                    "success": True,
                    "message": f"Series {series_id} archived successfully",
                    "reason": request.reason
                }
            else:
                raise HTTPException(status_code=404, detail=f"Series {series_id} not found or archive failed")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error archiving series {series_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/restore/{series_id}")
    async def restore_series(series_id: int, request: RestoreRequest):
        """Ripristina una serie dall'archivio"""
        try:
            success = await lifecycle_engine.restore_series(series_id, request.reason)
            
            if success:
                return {
                    "success": True,
                    "message": f"Series {series_id} restored successfully",
                    "reason": request.reason
                }
            else:
                raise HTTPException(status_code=404, detail=f"Series {series_id} not found or restore failed")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error restoring series {series_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/series/{series_id}")
    async def get_series_info(series_id: int):
        """Ottieni informazioni dettagliate su una serie"""
        try:
            series = await lifecycle_engine.repository.get_series_by_id(series_id)
            
            if not series:
                raise HTTPException(status_code=404, detail=f"Series {series_id} not found")
            
            return {
                "success": True,
                "data": series
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting series {series_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/series/{series_id}/evaluate")
    async def evaluate_single_series(series_id: int):
        """Valuta una singola serie (per test/debug)"""
        try:
            result = await lifecycle_engine.decision_maker.evaluate_single_series(
                series_id, lifecycle_engine.repository
            )
            
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            logger.error(f"Error evaluating series {series_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/series/stage/{stage}")
    async def get_series_by_stage(stage: str, limit: int = 50):
        """Ottieni serie per stage del lifecycle"""
        try:
            from ..core.lifecycle_engine import LifecycleStage
            
            # Valida lo stage
            try:
                lifecycle_stage = LifecycleStage(stage)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid stage '{stage}'. Valid stages: {[s.value for s in LifecycleStage]}"
                )
            
            series = await lifecycle_engine.repository.get_series_by_lifecycle_stage(lifecycle_stage, limit)
            
            return {
                "success": True,
                "data": {
                    "stage": stage,
                    "count": len(series),
                    "series": series
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting series by stage {stage}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/config")
    async def get_current_config():
        """Ottieni la configurazione corrente"""
        try:
            config = lifecycle_engine.rules_manager.get_current_config()
            validation = lifecycle_engine.rules_manager.validate_config()
            
            return {
                "success": True,
                "data": {
                    "config": config,
                    "validation": validation
                }
            }
        except Exception as e:
            logger.error(f"Error getting config: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/config")
    async def update_config(request: ConfigUpdateRequest):
        """Aggiorna la configurazione del lifecycle"""
        try:
            success = lifecycle_engine.rules_manager.update_config(request.config)
            
            if success:
                validation = lifecycle_engine.rules_manager.validate_config()
                return {
                    "success": True,
                    "message": "Configuration updated successfully",
                    "validation": validation
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to update configuration")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/cleanup")
    async def run_cleanup(days_threshold: int = 90):
        """Esegui pulizia manuale delle serie archiviate"""
        try:
            cleaned_count = await lifecycle_engine.repository.cleanup_old_archived_series(days_threshold)
            
            return {
                "success": True,
                "message": f"Cleanup completed: {cleaned_count} series marked for deletion",
                "cleaned_count": cleaned_count,
                "days_threshold": days_threshold
            }
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/rules/{rule_type}")
    async def get_rule_explanation(rule_type: str):
        """Ottieni spiegazione di una regola specifica"""
        try:
            explanation = lifecycle_engine.rules_manager.get_rule_explanation(rule_type)
            
            return {
                "success": True,
                "data": {
                    "rule_type": rule_type,
                    "explanation": explanation
                }
            }
        except Exception as e:
            logger.error(f"Error getting rule explanation: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/debug/grace-expired")
    async def debug_grace_expired(grace_days: int = 42):
        """Debug: mostra serie con periodo di grazia scaduto"""
        try:
            series = await lifecycle_engine.repository.get_expired_grace_period_series(grace_days)
            
            return {
                "success": True,
                "data": {
                    "grace_days_threshold": grace_days,
                    "expired_count": len(series),
                    "series": series
                }
            }
        except Exception as e:
            logger.error(f"Error getting grace expired series: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return app


def create_app():
    """
    Crea l'app FastAPI per test senza lifecycle engine
    Utile per test di base dell'applicazione
    """
    app = FastAPI(
        title="CosplayRadar Lifecycle Service",
        description="Servizio per la gestione del ciclo di vita delle serie anime/manga",
        version="1.0.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health")
    async def health_check():
        """Health check semplificato per test"""
        return {
            "status": "healthy",
            "service": "lifecycle-service",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {"connected": False, "message": "Test mode - no DB"}
        }
    
    return app
