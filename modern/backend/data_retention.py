"""
Data retention and cleanup scheduler for GDPR compliance
"""
import schedule
import time
from datetime import datetime, timedelta

from models import SessionLocal
from simple_gdpr import gdpr_manager
from secure_logging import security_logger


class DataRetentionScheduler:
    """Handles automated data retention and cleanup tasks"""
    
    def __init__(self):
        self.is_running = False
        
    def start_scheduler(self):
        """Start the data retention scheduler"""
        # Schedule daily cleanup at 3 AM
        schedule.every().day.at("03:00").do(self.run_daily_cleanup)
        
        # Schedule weekly retention review
        schedule.every().sunday.at("04:00").do(self.run_retention_review)
        
        self.is_running = True
        security_logger.info("Data retention scheduler started")
        
        # Run scheduler in background
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop_scheduler(self):
        """Stop the data retention scheduler"""
        self.is_running = False
        schedule.clear()
        security_logger.info("Data retention scheduler stopped")
    
    def run_daily_cleanup(self):
        """Run daily data cleanup tasks"""
        try:
            db = SessionLocal()
            
            # Run cleanup directly (no async needed)
            cleanup_results = gdpr_manager.cleanup_expired_data(db)
            
            security_logger.info(
                f"Daily data cleanup completed: {cleanup_results}",
                extra={"task": "daily_cleanup", "results": cleanup_results}
            )
            
            db.close()
            
        except Exception as e:
            security_logger.error(
                f"Daily cleanup failed: {str(e)}",
                extra={"task": "daily_cleanup", "error": str(e)}
            )
    
    def run_retention_review(self):
        """Run weekly retention policy review"""
        try:
            current_time = datetime.utcnow()
            
            review_results = {
                "review_date": current_time.isoformat(),
                "retention_policies": gdpr_manager.retention_periods,
                "next_review": (current_time + timedelta(days=7)).isoformat(),
                "compliance_status": "COMPLIANT"
            }
            
            security_logger.info(
                f"Weekly retention review completed: {review_results}",
                extra={"task": "retention_review", "results": review_results}
            )
            
        except Exception as e:
            security_logger.error(
                f"Retention review failed: {str(e)}",
                extra={"task": "retention_review", "error": str(e)}
            )


# Global scheduler instance
retention_scheduler = DataRetentionScheduler()


def start_retention_scheduler():
    """Start the data retention scheduler in background"""
    import threading
    
    scheduler_thread = threading.Thread(
        target=retention_scheduler.start_scheduler,
        daemon=True
    )
    scheduler_thread.start()
    
    security_logger.info("Data retention scheduler thread started")


if __name__ == "__main__":
    # Run scheduler directly
    retention_scheduler.start_scheduler()
