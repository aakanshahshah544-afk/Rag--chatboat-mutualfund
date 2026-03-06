"""
Phase 5: Data Update Scheduler

- Runs daily at configured time
- Re-scrapes Groww pages
- Updates raw data
- Regenerates structured JSON
- Rebuilds embeddings
- Updates last_updated timestamp
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataScheduler:
    """Scheduler for daily data updates"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        
        self.run_hour = int(os.getenv("SCHEDULER_RUN_HOUR", "2"))
        self.run_minute = int(os.getenv("SCHEDULER_RUN_MINUTE", "0"))
    
    def update_data(self):
        """Run complete data update pipeline"""
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info("Starting scheduled data update...")
        logger.info("=" * 60)
        
        try:
            logger.info("Step 1: Scraping Groww pages...")
            from phase1_scraper import GrowwScraper
            scraper = GrowwScraper()
            scraper.run()
            logger.info("[OK] Scraping complete")
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            return False
        
        try:
            logger.info("Step 2: Processing data...")
            from phase2_processing import DataProcessor
            processor = DataProcessor()
            processor.run()
            logger.info("[OK] Processing complete")
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return False
        
        try:
            logger.info("Step 3: Rebuilding embeddings...")
            from phase3_rag import EmbeddingManager
            embeddings = EmbeddingManager(load_existing=False)
            embeddings.run()
            logger.info("[OK] Embeddings rebuilt")
            
        except Exception as e:
            logger.error(f"Embedding rebuild failed: {e}")
            return False
        
        try:
            import phase4_backend.main as backend
            if hasattr(backend, 'rag_chain') and backend.rag_chain is not None:
                logger.info("Reloading RAG chain in backend...")
                backend.rag_chain = None
            
        except Exception as e:
            logger.warning(f"Could not reload backend: {e}")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 60)
        logger.info(f"Data update completed successfully in {elapsed:.1f} seconds")
        logger.info(f"Next scheduled run: {self.run_hour:02d}:{self.run_minute:02d}")
        logger.info("=" * 60)
        
        return True
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        trigger = CronTrigger(
            day_of_week='mon',
            hour=self.run_hour,
            minute=self.run_minute
        )
        
        self.scheduler.add_job(
            self.update_data,
            trigger=trigger,
            id='data_update',
            name='Daily Data Update',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info(f"Scheduler started. Will run every Monday at {self.run_hour:02d}:{self.run_minute:02d}")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Scheduler stopped")
    
    def run_now(self):
        """Run data update immediately"""
        logger.info("Running manual data update...")
        return self.update_data()
    
    def get_next_run_time(self):
        """Get next scheduled run time"""
        jobs = self.scheduler.get_jobs()
        if jobs:
            return jobs[0].next_run_time
        return None
    
    def get_status(self):
        """Get scheduler status"""
        return {
            "is_running": self.is_running,
            "scheduled_time": f"{self.run_hour:02d}:{self.run_minute:02d}",
            "next_run": str(self.get_next_run_time()) if self.is_running else None
        }


def run_scheduler():
    """Run scheduler as standalone process"""
    scheduler = DataScheduler()
    
    print("=" * 60)
    print("Groww RAG Chatbot - Data Scheduler")
    print("=" * 60)
    print(f"Scheduled update every Monday at: {scheduler.run_hour:02d}:{scheduler.run_minute:02d}")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    scheduler.start()
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nShutting down scheduler...")
        scheduler.stop()
        print("Scheduler stopped")


def run_update_now():
    """Run data update immediately (for manual triggering)"""
    scheduler = DataScheduler()
    success = scheduler.run_now()
    
    if success:
        print("\n[OK] Data update completed successfully")
    else:
        print("\n[FAIL] Data update failed - check logs for details")
    
    return success


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Groww RAG Data Scheduler")
    parser.add_argument("--now", action="store_true", help="Run update immediately")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon (scheduled)")
    
    args = parser.parse_args()
    
    if args.now:
        run_update_now()
    elif args.daemon:
        run_scheduler()
    else:
        print("Groww RAG Data Scheduler")
        print("-" * 40)
        print("Options:")
        print("  --now     Run update immediately")
        print("  --daemon  Run as daemon (scheduled)")
        print("\nExample:")
        print("  python -m phase5_scheduler.scheduler --now")
        print("  python -m phase5_scheduler.scheduler --daemon")
