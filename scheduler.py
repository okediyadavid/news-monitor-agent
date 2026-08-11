"""
Scheduler module for news monitoring agent.
Handles automated scheduling of news source checks using APScheduler.
"""

import logging
from typing import Callable, Optional
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import signal
import sys

logger = logging.getLogger(__name__)


class NewsScheduler:
    """Scheduler for automated news monitoring."""
    
    def __init__(self, check_interval_hours: int = 6):
        """
        Initialize the news scheduler.
        
        Args:
            check_interval_hours: Interval between checks in hours
        """
        self.check_interval_hours = check_interval_hours
        self.scheduler = BackgroundScheduler()
        self.job_id = "news_monitor_job"
        self.is_running = False
        self.check_function: Optional[Callable] = None
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Add event listeners
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
    
    def set_check_function(self, func: Callable) -> None:
        """
        Set the function to execute for each check.
        
        Args:
            func: Function to call for each scheduled check
        """
        self.check_function = func
        logger.info("Check function set")
    
    def start(self) -> None:
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        if not self.check_function:
            raise ValueError("Check function not set. Call set_check_function() first.")
        
        try:
            # Add the job
            self.scheduler.add_job(
                self.check_function,
                trigger=IntervalTrigger(hours=self.check_interval_hours),
                id=self.job_id,
                name='News Monitor Check',
                replace_existing=True
            )
            
            # Start the scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info(f"Scheduler started with {self.check_interval_hours} hour interval")
            logger.info(f"Next run scheduled for: {self.get_next_run_time()}")
            
            # Run the check immediately on startup
            logger.info("Running initial check...")
            self.check_function()
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the scheduler."""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        try:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    def pause(self) -> None:
        """Pause the scheduler."""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        try:
            self.scheduler.pause_job(self.job_id)
            logger.info("Scheduler paused")
        except Exception as e:
            logger.error(f"Error pausing scheduler: {e}")
    
    def resume(self) -> None:
        """Resume the scheduler."""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        try:
            self.scheduler.resume_job(self.job_id)
            logger.info("Scheduler resumed")
            logger.info(f"Next run scheduled for: {self.get_next_run_time()}")
        except Exception as e:
            logger.error(f"Error resuming scheduler: {e}")
    
    def run_now(self) -> None:
        """Trigger an immediate check."""
        if not self.check_function:
            logger.error("Check function not set")
            return
        
        logger.info("Triggering immediate check...")
        try:
            self.check_function()
        except Exception as e:
            logger.error(f"Error running immediate check: {e}")
    
    def get_next_run_time(self) -> Optional[datetime]:
        """
        Get the next scheduled run time.
        
        Returns:
            Next run datetime or None
        """
        try:
            job = self.scheduler.get_job(self.job_id)
            if job:
                return job.next_run_time
            return None
        except Exception as e:
            logger.error(f"Error getting next run time: {e}")
            return None
    
    def modify_interval(self, hours: int) -> None:
        """
        Modify the check interval.
        
        Args:
            hours: New interval in hours
        """
        try:
            self.check_interval_hours = hours
            self.scheduler.remove_job(self.job_id)
            self.scheduler.add_job(
                self.check_function,
                trigger=IntervalTrigger(hours=hours),
                id=self.job_id,
                name='News Monitor Check',
                replace_existing=True
            )
            logger.info(f"Interval modified to {hours} hours")
            logger.info(f"Next run scheduled for: {self.get_next_run_time()}")
        except Exception as e:
            logger.error(f"Error modifying interval: {e}")
    
    def get_job_info(self) -> dict:
        """
        Get information about the scheduled job.
        
        Returns:
            Dictionary with job information
        """
        try:
            job = self.scheduler.get_job(self.job_id)
            if job:
                return {
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time,
                    'trigger': str(job.trigger)
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting job info: {e}")
            return {}
    
    def _job_executed_listener(self, event) -> None:
        """
        Listener for job execution events.
        
        Args:
            event: APScheduler event
        """
        if event.exception:
            logger.error(f"Job {event.job_id} failed: {event.exception}")
        else:
            logger.info(f"Job {event.job_id} executed successfully")
    
    def _signal_handler(self, signum, frame) -> None:
        """
        Handle shutdown signals gracefully.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


class ManualScheduler:
    """Manual scheduler for testing and one-off runs."""
    
    def __init__(self):
        """Initialize manual scheduler."""
        self.check_function: Optional[Callable] = None
    
    def set_check_function(self, func: Callable) -> None:
        """
        Set the function to execute.
        
        Args:
            func: Function to call
        """
        self.check_function = func
        logger.info("Check function set")
    
    def run_once(self) -> None:
        """Run the check function once."""
        if not self.check_function:
            raise ValueError("Check function not set. Call set_check_function() first.")
        
        logger.info("Running manual check...")
        try:
            self.check_function()
            logger.info("Manual check completed")
        except Exception as e:
            logger.error(f"Error running manual check: {e}")
            raise
