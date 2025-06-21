#!/usr/bin/env python3
"""
Test rapido per verificare l'importazione e l'inizializzazione dei moduli
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loguru import logger

def test_imports():
    """Test delle importazioni dei moduli"""
    logger.info("🧪 Test importazioni moduli...")
    
    try:
        from src.core.lifecycle_engine import LifecycleEngine
        logger.info("✅ LifecycleEngine importato")
    except Exception as e:
        logger.error(f"❌ Errore importazione LifecycleEngine: {e}")
        return False
    
    try:
        from src.core.decision_maker import DecisionMaker
        logger.info("✅ DecisionMaker importato")
    except Exception as e:
        logger.error(f"❌ Errore importazione DecisionMaker: {e}")
        return False
    
    try:
        from src.core.rules_manager import RulesManager
        logger.info("✅ RulesManager importato")
    except Exception as e:
        logger.error(f"❌ Errore importazione RulesManager: {e}")
        return False
    
    try:
        from src.database.lifecycle_repository import LifecycleRepository
        logger.info("✅ LifecycleRepository importato")
    except Exception as e:
        logger.error(f"❌ Errore importazione LifecycleRepository: {e}")
        return False
    
    try:
        from src.api.routes import create_app
        logger.info("✅ FastAPI app importata")
    except Exception as e:
        logger.error(f"❌ Errore importazione FastAPI app: {e}")
        return False
    
    return True

def test_app_creation():
    """Test creazione app FastAPI"""
    logger.info("🧪 Test creazione app FastAPI...")
    
    try:
        from src.api.routes import create_app
        app = create_app()
        logger.info("✅ App FastAPI creata con successo")
        
        # Test che ci siano le routes
        routes = [route.path for route in app.routes]
        expected_routes = ["/health", "/stats", "/config", "/evaluate", "/archive", "/restore"]
        
        for expected_route in expected_routes:
            if any(expected_route in route for route in routes):
                logger.info(f"✅ Route {expected_route} trovata")
            else:
                logger.warning(f"⚠️  Route {expected_route} non trovata")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore creazione app: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Test rapido lifecycle-service")
    
    success = True
    
    # Test importazioni
    if not test_imports():
        success = False
    
    # Test creazione app
    if not test_app_creation():
        success = False
    
    if success:
        logger.info("🎉 Tutti i test rapidi passati!")
    else:
        logger.error("❌ Alcuni test sono falliti!")
    
    sys.exit(0 if success else 1)
