#!/usr/bin/env python3
"""
Main entry point per il Lifecycle Service
Servizio per la gestione del ciclo di vita delle serie anime/manga
"""

import asyncio
import logging
import uvicorn
import os
from pathlib import Path
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.lifecycle_engine import SeriesLifecycleEngine
from src.api.routes import create_lifecycle_api

# Configurazione
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://cosplayradar:dev_password_123@localhost:5432/cosplayradar_dev"
)
CONFIG_PATH = os.getenv(
    "LIFECYCLE_CONFIG_PATH", 
    str(Path(__file__).parent / "config" / "lifecycle_rules.json")
)
PORT = int(os.getenv("PORT", 8001))
HOST = os.getenv("HOST", "0.0.0.0")

async def main():
    """Main function del lifecycle service"""
    logger.info("🚀 Avvio Lifecycle Service")
    
    try:
        # Inizializza il lifecycle engine
        logger.info(f"📡 Connessione database: {DATABASE_URL}")
        logger.info(f"📋 Config path: {CONFIG_PATH}")
        
        lifecycle_engine = SeriesLifecycleEngine(DATABASE_URL, CONFIG_PATH)
        
        # Verifica schema database
        await lifecycle_engine.repository.ensure_schema()
        
        # Crea l'app FastAPI
        app = create_lifecycle_api(lifecycle_engine)
        
        # Health check iniziale
        health = await lifecycle_engine.repository.health_check()
        if health["database_connected"]:
            logger.info("✅ Database connesso correttamente")
        else:
            logger.error(f"❌ Problema database: {health.get('error', 'Unknown')}")
            return
        
        # Avvia il server
        logger.info(f"🌐 Avvio server su {HOST}:{PORT}")
        
        config = uvicorn.Config(
            app=app,
            host=HOST,
            port=PORT,
            log_level="info",
            access_log=True
        )
        
        server = uvicorn.Server(config)
        await server.serve()
        
    except Exception as e:
        logger.error(f"❌ Errore avvio servizio: {e}")
        raise

def run_manual_evaluation():
    """Esegue una valutazione manuale (per test/cron)"""
    async def evaluate():
        try:
            lifecycle_engine = SeriesLifecycleEngine(DATABASE_URL, CONFIG_PATH)
            await lifecycle_engine.repository.ensure_schema()
            
            logger.info("🔄 Esecuzione valutazione manuale...")
            results = await lifecycle_engine.run_lifecycle_evaluation()
            
            if results["success"]:
                logger.info(f"✅ Valutazione completata in {results['execution_time_seconds']:.2f}s")
                logger.info(f"📊 Serie valutate: {results['series_evaluated']}")
                logger.info(f"📊 Decisioni prese: {results['decisions_made']}")
                logger.info(f"📦 Serie archiviate: {results['archived_count']}")
                logger.info(f"✅ Serie mantenute attive: {results['kept_active_count']}")
                
                if results.get("errors"):
                    logger.warning(f"⚠️  Errori durante valutazione: {len(results['errors'])}")
                    for error in results["errors"]:
                        logger.warning(f"  • {error}")
            else:
                logger.error(f"❌ Valutazione fallita: {results.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"❌ Errore durante valutazione manuale: {e}")
            raise
    
    asyncio.run(evaluate())

def show_statistics():
    """Mostra statistiche correnti (per debug)"""
    async def get_stats():
        try:
            lifecycle_engine = SeriesLifecycleEngine(DATABASE_URL, CONFIG_PATH)
            stats = await lifecycle_engine.get_lifecycle_statistics()
            
            print("\n📊 STATISTICHE LIFECYCLE SERVICE")
            print("=" * 50)
            
            # Lifecycle stages
            stages = stats.get("lifecycle_stages", {})
            print(f"📁 Total Series: {stages.get('total_series', 0)}")
            print(f"🆕 Upcoming: {stages.get('upcoming', 0)}")
            print(f"⏰ Grace Period: {stages.get('grace_period', 0)}")
            print(f"⏳ Extended Grace: {stages.get('extended_grace', 0)}")
            print(f"✅ Active Tracking: {stages.get('active_tracking', 0)}")
            print(f"📦 Archived: {stages.get('archived', 0)}")
            print(f"🗑️  Ready for Deletion: {stages.get('ready_for_deletion', 0)}")
            
            # AniList status
            anilist_status = stats.get("anilist_status", {})
            print(f"\n📺 ANILIST STATUS:")
            print(f"🔜 Not Yet Released: {anilist_status.get('not_yet_released', 0)}")
            print(f"📡 Currently Releasing: {anilist_status.get('currently_releasing', 0)}")
            print(f"✅ Finished: {anilist_status.get('finished', 0)}")
            print(f"❌ Cancelled: {anilist_status.get('cancelled', 0)}")
            
            # Performance
            perf = stats.get("performance", {})
            print(f"\n📈 PERFORMANCE METRICS:")
            print(f"📊 Avg Popularity: {perf.get('avg_popularity', 0) or 0:.1f}")
            print(f"⭐ Avg Favourites: {perf.get('avg_favourites', 0) or 0:.1f}")
            print(f"🔥 Avg Trending: {perf.get('avg_trending', 0) or 0:.1f}")
            print(f"🎯 High Score Count: {perf.get('high_score_count', 0) or 0}")
            
        except Exception as e:
            logger.error(f"❌ Errore durante recupero statistiche: {e}")
            raise
    
    asyncio.run(get_stats())

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "evaluate":
            logger.info("🔄 Modalità valutazione manuale")
            run_manual_evaluation()
        elif command == "stats":
            logger.info("📊 Modalità visualizzazione statistiche")
            show_statistics()
        elif command == "server":
            logger.info("🌐 Modalità server")
            asyncio.run(main())
        else:
            print("❌ Comando non riconosciuto")
            print("📖 Comandi disponibili:")
            print("  • python main.py server    - Avvia il server API")
            print("  • python main.py evaluate  - Esegui valutazione manuale")
            print("  • python main.py stats     - Mostra statistiche")
    else:
        # Default: avvia il server
        asyncio.run(main())
