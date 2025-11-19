"""
Worker pool manager - manages multiple worker threads
"""
import threading
import logging
from typing import List
from src.common.constants import MAX_WORKER_THREADS
from src.core.worker import Worker

logger = logging.getLogger(__name__)


class WorkerPool:
    """Manages a pool of worker threads"""
    
    def __init__(self, num_workers: int = MAX_WORKER_THREADS):
        """
        Initialize worker pool
        
        Args:
            num_workers: Number of worker threads to create
        """
        self.num_workers = num_workers
        self.workers: List[Worker] = []
        self.running = False
    
    def start(self) -> None:
        """Start all worker threads"""
        if self.running:
            logger.warning("Worker pool already running")
            return
        
        self.running = True
        
        for i in range(self.num_workers):
            worker = Worker(worker_id=i)
            worker.start()
            self.workers.append(worker)
            logger.info(f"Started worker {i+1}/{self.num_workers}")
        
        logger.info(f"Worker pool started with {self.num_workers} threads")
    
    def stop(self) -> None:
        """Stop all worker threads"""
        self.running = False
        
        for i, worker in enumerate(self.workers):
            worker.stop()
            logger.info(f"Stopped worker {i+1}/{self.num_workers}")
        
        self.workers.clear()
        logger.info("Worker pool stopped")


# Global worker pool instance
_worker_pool_instance = None
_pool_lock = threading.Lock()


def get_worker_pool(num_workers: int = MAX_WORKER_THREADS) -> WorkerPool:
    """Get or create global worker pool instance"""
    global _worker_pool_instance
    
    if _worker_pool_instance is None:
        with _pool_lock:
            if _worker_pool_instance is None:
                _worker_pool_instance = WorkerPool(num_workers=num_workers)
                logger.info(f"WorkerPool singleton created with {num_workers} workers")
    
    return _worker_pool_instance
