#!/usr/bin/env python3
"""
Test del Lifecycle Service
Verifica che tutti i componenti funzionino correttamente
"""

import asyncio
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.lifecycle_engine import SeriesLifecycleEngine
from src.core.rules_manager import LifecycleRulesManager
from src.core.decision_maker import LifecycleDecisionMaker
from src.database.lifecycle_repository import LifecycleRepository

DATABASE_URL = "postgresql://cosplayradar:dev_password_123@localhost:5432/cosplayradar_dev"
CONFIG_PATH = str(Path(__file__).parent / "config" / "lifecycle_rules.json")

async def test_database_connection():
    """Test connessione database"""
    logger.info("🧪 Test connessione database...")
    
    try:
        repo = LifecycleRepository(DATABASE_URL)
        health = await repo.health_check()
        
        if health["database_connected"]:
            logger.info(f"✅ Database connesso - {health['total_series']} serie trovate")
            return True
        else:
            logger.error(f"❌ Database non connesso: {health.get('error', 'Unknown')}")
            return False
    except Exception as e:
        logger.error(f"❌ Errore test database: {e}")
        return False

async def test_rules_manager():
    """Test rules manager"""
    logger.info("🧪 Test Rules Manager...")
    
    try:
        rules = LifecycleRulesManager(CONFIG_PATH)
        
        # Test configurazione
        grace_days = rules.get_grace_period_days()
        thresholds = rules.get_thresholds()
        weights = rules.get_scoring_weights()
        
        logger.info(f"✅ Periodo grazia: {grace_days} giorni")
        logger.info(f"✅ Soglia keep_active: {thresholds['keep_active']['min_composite_score']}")
        logger.info(f"✅ Peso popularity: {weights['popularity']}")
        
        # Test validazione
        validation = rules.validate_config()
        if validation["valid"]:
            logger.info("✅ Configurazione valida")
        else:
            logger.warning(f"⚠️  Problemi configurazione: {validation['issues']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore test rules manager: {e}")
        return False

async def test_decision_maker():
    """Test decision maker"""
    logger.info("🧪 Test Decision Maker...")
    
    try:
        rules = LifecycleRulesManager(CONFIG_PATH)
        decision_maker = LifecycleDecisionMaker(rules)
        
        # Test con dati mock
        test_series = {
            'id': 1,
            'title': 'Test Series',
            'popularity': 75,
            'favourites': 150,
            'trending': 45,
            'character_count': 3,
            'avg_character_trending': 60,
            'max_character_trending': 85,
            'days_in_grace': 30
        }
        
        decision = await decision_maker.make_lifecycle_decision(test_series)
        
        logger.info(f"✅ Decisione: {decision['action']}")
        logger.info(f"✅ Score: {decision['composite_score']}")
        logger.info(f"✅ Motivo: {decision['reason']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore test decision maker: {e}")
        return False

async def test_repository_operations():
    """Test operazioni repository"""
    logger.info("🧪 Test Repository Operations...")
    
    try:
        repo = LifecycleRepository(DATABASE_URL)
        
        # Test schema
        await repo.ensure_schema()
        logger.info("✅ Schema verificato/creato")
        
        # Test statistiche
        stats = await repo.get_lifecycle_statistics()
        stages = stats.get("lifecycle_stages", {})
        
        logger.info(f"✅ Statistiche recuperate:")
        logger.info(f"  • Total: {stages.get('total_series', 0)}")
        logger.info(f"  • Grace: {stages.get('grace_period', 0)}")
        logger.info(f"  • Active: {stages.get('active_tracking', 0)}")
        logger.info(f"  • Archived: {stages.get('archived', 0)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore test repository: {e}")
        return False

async def test_lifecycle_engine():
    """Test completo del lifecycle engine"""
    logger.info("🧪 Test Lifecycle Engine...")
    
    try:
        engine = SeriesLifecycleEngine(DATABASE_URL, CONFIG_PATH)
        
        # Test inizializzazione
        await engine.repository.ensure_schema()
        logger.info("✅ Engine inizializzato")
        
        # Test statistiche
        stats = await engine.get_lifecycle_statistics()
        if stats:
            logger.info("✅ Statistiche recuperate")
        
        # Test valutazione (solo preparazione, non esecuzione completa)
        logger.info("✅ Engine pronto per valutazione completa")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore test lifecycle engine: {e}")
        return False

async def run_full_test():
    """Esegue tutti i test"""
    logger.info("🚀 Avvio test completo Lifecycle Service")
    print("=" * 60)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Rules Manager", test_rules_manager),
        ("Decision Maker", test_decision_maker),
        ("Repository Operations", test_repository_operations),
        ("Lifecycle Engine", test_lifecycle_engine),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            success = await test_func()
            if success:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 RISULTATI TEST: {passed}/{total} passati")
    
    if passed == total:
        print("🎉 Tutti i test sono passati! Lifecycle Service pronto.")
        return True
    else:
        print("⚠️  Alcuni test sono falliti. Verificare la configurazione.")
        return False

async def test_api_simulation():
    """Simula le chiamate API principali"""
    logger.info("🧪 Test simulazione API...")
    
    try:
        engine = SeriesLifecycleEngine(DATABASE_URL, CONFIG_PATH)
        await engine.repository.ensure_schema()
        
        # Simula /health
        health = await engine.repository.health_check()
        logger.info(f"✅ API /health: {health['database_connected']}")
        
        # Simula /stats
        stats = await engine.get_lifecycle_statistics()
        logger.info(f"✅ API /stats: {len(stats)} sezioni statistiche")
        
        # Simula /evaluate (senza esecuzione completa)
        logger.info("✅ API /evaluate: Pronto per esecuzione")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore test API: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        logger.info("🌐 Test simulazione API")
        success = asyncio.run(test_api_simulation())
    else:
        logger.info("🧪 Test completo del servizio")
        success = asyncio.run(run_full_test())
    
    if success:
        logger.info("🎉 Test completati con successo!")
        sys.exit(0)
    else:
        logger.error("❌ Test falliti!")
        sys.exit(1)
