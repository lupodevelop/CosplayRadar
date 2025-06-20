"""
Scheduler for the CosplayRadar Scraper
Handles 24-hour periodic execution and background job management
"""

import logging
import os
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any
import json

from main import CosplayRadarScraper

logger = logging.getLogger(__name__)


class ScraperScheduler:
    def __init__(self):
        """Initialize the scheduler with configuration"""
        self.scraper = None
        self.is_running = False
        self.last_run = None
        self.next_run = None
        self.run_count = 0

        # Load schedule configuration
        self.interval_hours = int(os.getenv('SCHEDULE_INTERVAL_HOURS', '24'))
        self.run_at_time = os.getenv('SCHEDULE_RUN_AT_TIME')  # Format: "HH:MM"
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.retry_delay_minutes = int(os.getenv('RETRY_DELAY_MINUTES', '30'))

        logger.info(
            f"Scheduler initialized - interval: {
                self.interval_hours}h, run_at: {
                self.run_at_time}")

    def _initialize_scraper(self) -> bool:
        """Initialize the scraper instance"""
        try:
            if not self.scraper:
                self.scraper = CosplayRadarScraper()
                logger.info("Scraper instance initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize scraper: {e}")
            return False

    def run_scraping_job(self) -> Dict[str, Any]:
        """Execute a single scraping job with error handling and retries"""
        job_start = datetime.now()
        logger.info(f"Starting scheduled scraping job #{self.run_count + 1}")

        if not self._initialize_scraper():
            return {
                'success': False,
                'error': 'Failed to initialize scraper',
                'timestamp': job_start.isoformat()
            }

        results = None
        last_error = None

        # Retry logic
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"Scraping attempt {attempt + 1}/{self.max_retries}")
                results = self.scraper.run_scraping_cycle()

                if results and not results.get('errors'):
                    # Successful run
                    self.last_run = job_start
                    self.run_count += 1

                    logger.info(f"✅ Scraping job completed successfully")
                    logger.info(
                        f"Summary: {
                            results['posts_scraped']} posts, " f"{
                            results['characters_found']} characters found, " f"{
                            results['characters_created']} created, " f"{
                            results['characters_updated']} updated")

                    return {
                        'success': True,
                        'results': results,
                        'attempt': attempt + 1,
                        'timestamp': job_start.isoformat(),
                        'duration': (
                            datetime.now() - job_start).total_seconds()}
                else:
                    # Partial success or errors
                    last_error = f"Scraping completed with errors: {
                        results.get(
                            'errors', [])}"
                    logger.warning(last_error)

                    if attempt < self.max_retries - 1:
                        logger.info(
                            f"Retrying in {
                                self.retry_delay_minutes} minutes...")
                        time.sleep(self.retry_delay_minutes * 60)

            except Exception as e:
                last_error = str(e)
                logger.error(f"Scraping attempt {attempt + 1} failed: {e}")

                if attempt < self.max_retries - 1:
                    logger.info(
                        f"Retrying in {
                            self.retry_delay_minutes} minutes...")
                    time.sleep(self.retry_delay_minutes * 60)

        # All attempts failed
        logger.error(f"❌ All {self.max_retries} scraping attempts failed")
        return {
            'success': False,
            'error': last_error,
            'attempts': self.max_retries,
            'timestamp': job_start.isoformat(),
            'duration': (datetime.now() - job_start).total_seconds()
        }

    def setup_schedule(self):
        """Setup the scheduled job"""
        if self.run_at_time:
            # Schedule at specific time daily
            try:
                schedule.every().day.at(
                    self.run_at_time).do(
                    self.run_scraping_job)
                logger.info(f"Scheduled daily job at {self.run_at_time}")

                # Calculate next run time
                now = datetime.now()
                today_at_time = datetime.strptime(
                    f"{now.date()} {self.run_at_time}", "%Y-%m-%d %H:%M")

                if today_at_time > now:
                    self.next_run = today_at_time
                else:
                    self.next_run = today_at_time + timedelta(days=1)

            except ValueError as e:
                logger.error(f"Invalid time format '{self.run_at_time}': {e}")
                logger.info("Falling back to interval-based scheduling")
                self._setup_interval_schedule()
        else:
            # Schedule based on interval
            self._setup_interval_schedule()

    def _setup_interval_schedule(self):
        """Setup interval-based scheduling"""
        schedule.every(self.interval_hours).hours.do(self.run_scraping_job)
        logger.info(f"Scheduled job every {self.interval_hours} hours")

        # Calculate next run time
        self.next_run = datetime.now() + timedelta(hours=self.interval_hours)

    def run_scheduler(self):
        """Run the scheduler in blocking mode"""
        logger.info("🚀 Starting CosplayRadar Scheduler")

        self.setup_schedule()
        self.is_running = True

        # Run immediately if enabled
        if os.getenv('RUN_IMMEDIATELY', 'false').lower() == 'true':
            logger.info("Running initial scraping job immediately...")
            self.run_scraping_job()

        logger.info(f"⏰ Next scheduled run: {self.next_run}")
        logger.info("Scheduler running... Press Ctrl+C to stop")

        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logger.info("🛑 Scheduler stopped by user")
            self.is_running = False

    def run_scheduler_background(self) -> threading.Thread:
        """Run the scheduler in background thread"""
        def scheduler_worker():
            self.run_scheduler()

        thread = threading.Thread(target=scheduler_worker, daemon=True)
        thread.start()
        logger.info("Scheduler started in background thread")
        return thread

    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            'is_running': self.is_running,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'run_count': self.run_count,
            'interval_hours': self.interval_hours,
            'run_at_time': self.run_at_time,
            'pending_jobs': len(schedule.jobs)
        }

    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("Scheduler stopped and jobs cleared")


def create_health_check_server():
    """Create a simple HTTP server for health checks"""
    from http.server import HTTPServer, BaseHTTPRequestHandler

    scheduler_instance = None

    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/health':
                status = {
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'service': 'cosplayradar-scraper'
                }

                if scheduler_instance:
                    status.update(scheduler_instance.get_status())

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(status).encode())

            elif self.path == '/trigger':
                # Manual trigger endpoint
                if scheduler_instance and scheduler_instance.scraper:
                    try:
                        result = scheduler_instance.run_scraping_job()
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode())
                    except Exception as e:
                        self.send_response(500)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(
                            {'error': str(e)}).encode())
                else:
                    self.send_response(503)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(
                        {'error': 'Scheduler not ready'}).encode())
            else:
                self.send_response(404)
                self.end_headers()

    port = int(os.getenv('HEALTH_CHECK_PORT', '8080'))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)

    def set_scheduler(scheduler):
        nonlocal scheduler_instance
        scheduler_instance = scheduler

    server.set_scheduler = set_scheduler
    return server


def main():
    """Main entry point for the scheduler"""
    from dotenv import load_dotenv
    load_dotenv()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scheduler.log'),
            logging.StreamHandler()
        ]
    )

    # Create scheduler
    scheduler = ScraperScheduler()

    # Start health check server if enabled
    health_server = None
    if os.getenv('ENABLE_HEALTH_CHECK', 'true').lower() == 'true':
        health_server = create_health_check_server()
        health_server.set_scheduler(scheduler)

        # Start health check server in background
        import threading
        health_thread = threading.Thread(
            target=health_server.serve_forever, daemon=True)
        health_thread.start()

        port = int(os.getenv('HEALTH_CHECK_PORT', '8080'))
        logger.info(f"Health check server started on port {port}")
        logger.info(f"Health check: http://localhost:{port}/health")
        logger.info(f"Manual trigger: http://localhost:{port}/trigger")

    try:
        # Run scheduler
        scheduler.run_scheduler()

    except Exception as e:
        logger.error(f"Fatal error in scheduler: {e}")

    finally:
        if health_server:
            health_server.shutdown()
        logger.info("Scheduler shutdown complete")


if __name__ == "__main__":
    main()
