"""
Print Queue und Job-Management fuer den Phomemo M110 Drucker.
"""

import time
import logging
from typing import Dict, Any

from config import MAX_RETRIES_PER_JOB
from .models import PrintJob

logger = logging.getLogger(__name__)


class QueueMixin:
    """Mixin fuer Print Queue und Job-Management."""

    def get_queue_status(self) -> Dict[str, Any]:
        """Gibt Queue-Status zurueck"""
        return {
            'size': self.print_queue.qsize(),
            'processor_running': self.queue_processor_running,
            'stats': {
                'total_jobs': self.stats['total_jobs'],
                'successful_jobs': self.stats['successful_jobs'],
                'failed_jobs': self.stats['failed_jobs'],
                'images_processed': self.stats['images_processed'],
                'text_jobs': self.stats['text_jobs']
            }
        }

    def queue_print_job(self, job_type: str, data: Dict[str, Any]) -> str:
        """Fuegt einen Print Job zur Queue hinzu"""
        job_id = f"{job_type}_{int(time.time() * 1000)}"
        job = PrintJob(
            job_id=job_id,
            job_type=job_type,
            data=data,
            timestamp=time.time(),
            max_retries=MAX_RETRIES_PER_JOB
        )

        self.print_queue.put(job)
        self.stats['total_jobs'] += 1
        logger.info(f"Queued job {job_id} of type {job_type}")
        return job_id

    def _process_print_queue(self):
        """Background Thread fuer Print Queue Processing - Placeholder"""
        while self.queue_processor_running:
            try:
                time.sleep(1)  # Simplified for now
            except Exception as e:
                logger.error(f"Queue processor error: {e}")
