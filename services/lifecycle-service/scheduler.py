#!/usr/bin/env python3
"""
Scheduler per il Lifecycle Service
Esegue valutazioni automatiche del lifecycle in base a schedule configurato
"""

import asyncio
import schedule
import time
import logging
import os
from datetime import datetime
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

# Configurazione
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://cosplayradar:dev_password_123@localhost:5432/cosplayradar_dev"
)
CONFIG_PATH = os.getenv(
    "LIFECYCLE_CONFIG_PATH", 
    str(Path(__file__).parent / "config" / "lifecycle_rules.json")
)
SCHEDULE_INTERVAL_HOURS = int(os.getenv("SCHEDULE_INTERVAL_HOURS", 24))

class LifecycleScheduler:
    """Scheduler per esecuzione automatica del lifecycle"""
    
    def __init__(self):
        self.lifecycle_engine = None
        self.running = False
        logger.info(f"🕐 Scheduler inizializzato - Intervallo: {SCHEDULE_INTERVAL_HOURS} ore")
    
    async def initialize(self):
        """Inizializza il lifecycle engine"""
        try:
            self.lifecycle_engine = SeriesLifecycleEngine(DATABASE_URL, CONFIG_PATH)
            await self.lifecycle_engine.repository.ensure_schema()
            logger.info("✅ Lifecycle engine inizializzato")
        except Exception as e:
            logger.error(f"❌ Errore inizializzazione: {e}")
            raise
    
    async def run_scheduled_evaluation(self):
        """Esegue una valutazione schedulata"""
        if not self.lifecycle_engine:
            logger.error("❌ Lifecycle engine non inizializzato")
            return
        
        try:
            logger.info("🔄 Avvio valutazione schedulata...")
            start_time = datetime.now()
            
            results = await self.lifecycle_engine.run_lifecycle_evaluation()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            if results["success"]:
                logger.info(f"✅ Valutazione schedulata completata in {execution_time:.2f}s")
                logger.info(f"📊 Serie valutate: {results['series_evaluated']}")
                logger.info(f"📊 Decisioni prese: {results['decisions_made']}")
                logger.info(f"📦 Serie archiviate: {results['archived_count']}")
                logger.info(f"✅ Serie mantenute attive: {results['kept_active_count']}")
                
                if results.get("errors"):
                    logger.warning(f"⚠️  Errori durante valutazione: {len(results['errors'])}")
                    for error in results["errors"]:
                        logger.warning(f"  • {error}")
                
                # Log statistiche post-valutazione
                await self._log_post_evaluation_stats()
                
            else:
                logger.error(f"❌ Valutazione schedulata fallita: {results.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"❌ Errore durante valutazione schedulata: {e}")
    
    async def _log_post_evaluation_stats(self):
        """Log delle statistiche dopo la valutazione"""
        try:
            stats = await self.lifecycle_engine.get_lifecycle_statistics()
            stages = stats.get("lifecycle_stages", {})
            
            logger.info("📊 Statistiche post-valutazione:")
            logger.info(f"  • Total: {stages.get('total_series', 0)}")
            logger.info(f"  • Active: {stages.get('active_tracking', 0)}")
            logger.info(f"  • Grace: {stages.get('grace_period', 0)}")
            logger.info(f"  • Archived: {stages.get('archived', 0)}")
            
        except Exception as e:
            logger.warning(f"⚠️  Errore recupero statistiche post-valutazione: {e}")
    
    def schedule_jobs(self):
        """Configura i job schedulati"""
        # Job principale ogni X ore
        schedule.every(SCHEDULE_INTERVAL_HOURS).hours.do(
            lambda: asyncio.create_task(self.run_scheduled_evaluation())
        )
        
        # Job di health check ogni ora
        schedule.every().hour.do(
            lambda: asyncio.create_task(self._health_check())
        )
        
        # Job di statistiche quotidiano
        schedule.every().day.at("06:00").do(
            lambda: asyncio.create_task(self._daily_stats())
        )
        
        logger.info("📅 Job schedulati configurati:")
        logger.info(f"  • Valutazione lifecycle: ogni {SCHEDULE_INTERVAL_HOURS} ore")
        logger.info(f"  • Health check: ogni ora")
        logger.info(f"  • Statistiche giornaliere: 06:00")
    
    async def _health_check(self):
        """Health check periodico"""
        try:
            if self.lifecycle_engine:
                health = await self.lifecycle_engine.repository.health_check()
                if health["database_connected"]:
                    logger.debug("💓 Health check OK")
                else:
                    logger.error(f"❌ Health check fallito: {health.get('error', 'Unknown')}")
        except Exception as e:
            logger.error(f"❌ Errore health check: {e}")
    
    async def _daily_stats(self):
        """Log statistiche giornaliere"""
        try:
            if self.lifecycle_engine:
                stats = await self.lifecycle_engine.get_lifecycle_statistics()
                
                logger.info("📊 REPORT GIORNALIERO LIFECYCLE:")
                logger.info("=" * 40)
                
                stages = stats.get("lifecycle_stages", {})
                logger.info(f"📁 Serie totali: {stages.get('total_series', 0)}")
                logger.info(f"✅ Attive: {stages.get('active_tracking', 0)}")
                logger.info(f"⏰ In grazia: {stages.get('grace_period', 0)}")
                logger.info(f"📦 Archiviate: {stages.get('archived', 0)}")
                
                temporal = stats.get("temporal", {})
                logger.info(f"📈 Valutate oggi: {temporal.get('evaluated_today', 0)}")
                logger.info(f"📦 Archiviate settimana: {temporal.get('archived_this_week', 0)}")
                
        except Exception as e:
            logger.error(f"❌ Errore statistiche giornaliere: {e}")
    
    async def run(self):
        """Avvia il scheduler"""
        logger.info("🚀 Avvio Lifecycle Scheduler")
        
        # Inizializza
        await self.initialize()
        
        # Configura job
        self.schedule_jobs()
        
        # Esegui una valutazione iniziale
        logger.info("🔄 Esecuzione valutazione iniziale...")
        await self.run_scheduled_evaluation()
        
        # Loop principale
        self.running = True
        logger.info("⏰ Scheduler in esecuzione...")
        
        try:
            while self.running:
                schedule.run_pending()
                await asyncio.sleep(60)  # Check ogni minuto
                
        except KeyboardInterrupt:
            logger.info("⏹️  Scheduler interrotto dall'utente")
        except Exception as e:
            logger.error(f"❌ Errore nel loop scheduler: {e}")
        finally:
            self.running = False
            logger.info("🛑 Scheduler terminato")

async def main():
    """Main del scheduler"""
    scheduler = LifecycleScheduler()
    await scheduler.run()

if __name__ == "__main__":
    asyncio.run(main())
