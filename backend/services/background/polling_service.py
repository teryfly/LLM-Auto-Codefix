import asyncio
import logging
from typing import Dict, Callable, Any, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from config.config_models import AppConfig

logger = logging.getLogger("polling_service")

class PollingJob:
    def __init__(self, job_id: str, name: str, interval: int, callback: Callable, *args, **kwargs):
        self.job_id = job_id
        self.name = name
        self.interval = interval
        self.callback = callback
        self.args = args
        self.kwargs = kwargs
        self.created_at = datetime.utcnow()
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.run_count = 0
        self.error_count = 0
        self.last_error: Optional[str] = None

    async def run_once(self):
        """Execute the polling job once"""
        try:
            self.is_running = True
            self.last_run = datetime.utcnow()
            self.run_count += 1

            if asyncio.iscoroutinefunction(self.callback):
                await self.callback(*self.args, **self.kwargs)
            else:
                self.callback(*self.args, **self.kwargs)

            self.last_error = None

        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.error(f"Polling job {self.job_id} failed: {e}")
        finally:
            self.is_running = False
            self.next_run = datetime.utcnow() + timedelta(seconds=self.interval)

class PollingService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.jobs: Dict[str, PollingJob] = {}
        self.is_running = False
        self.main_task: Optional[asyncio.Task] = None

    def start(self):
        """Start the polling service"""
        if self.is_running:
            return

        self.is_running = True
        self.main_task = asyncio.create_task(self._run_polling_loop())
        logger.info("Polling service started")

    def stop(self):
        """Stop the polling service"""
        if not self.is_running:
            return

        self.is_running = False
        if self.main_task:
            self.main_task.cancel()

        # Cancel all running jobs
        for job in self.jobs.values():
            if job.task and not job.task.done():
                job.task.cancel()

        logger.info("Polling service stopped")

    def add_job(self, job_id: str, name: str, interval: int, callback: Callable, *args, **kwargs) -> str:
        """Add a new polling job"""
        if job_id in self.jobs:
            raise ValueError(f"Job {job_id} already exists")

        job = PollingJob(job_id, name, interval, callback, *args, **kwargs)
        job.next_run = datetime.utcnow() + timedelta(seconds=interval)
        self.jobs[job_id] = job

        logger.info(f"Added polling job {job_id}: {name} (interval: {interval}s)")
        return job_id

    def remove_job(self, job_id: str):
        """Remove a polling job"""
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Cancel the job if it's running
        if job.task and not job.task.done():
            job.task.cancel()

        del self.jobs[job_id]
        logger.info(f"Removed polling job {job_id}")

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a polling job"""
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        return {
            "job_id": job.job_id,
            "name": job.name,
            "interval": job.interval,
            "created_at": job.created_at.isoformat(),
            "last_run": job.last_run.isoformat() if job.last_run else None,
            "next_run": job.next_run.isoformat() if job.next_run else None,
            "is_running": job.is_running,
            "run_count": job.run_count,
            "error_count": job.error_count,
            "last_error": job.last_error
        }

    def list_jobs(self) -> Dict[str, Dict[str, Any]]:
        """List all polling jobs"""
        return {job_id: self.get_job_status(job_id) for job_id in self.jobs.keys()}

    async def _run_polling_loop(self):
        """Main polling loop"""
        try:
            while self.is_running:
                current_time = datetime.utcnow()

                # Check which jobs need to run
                for job in self.jobs.values():
                    if (job.next_run and current_time >= job.next_run and
                        not job.is_running and (not job.task or job.task.done())):

                        # Start the job
                        job.task = asyncio.create_task(job.run_once())

                # Sleep for a short interval before checking again
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("Polling loop cancelled")
        except Exception as e:
            logger.error(f"Polling loop error: {e}")
        finally:
            self.is_running = False