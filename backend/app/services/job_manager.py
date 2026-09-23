"""
Job Manager for asynchronous and background execution of AnalysisPipeline runs.
Manages job submission, background thread execution, queue management,
and status synchronization with the SQLite database.
"""

import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional

from backend.app.db.session import SessionLocal
from backend.app.db.models import AnalysisRun
from backend.app.services.pipeline import AnalysisPipeline

logger = logging.getLogger(__name__)


class JobManager:
    """
    Background worker pool managing asynchronous pipeline execution.
    Maintains clean database sessions per worker thread.
    """

    def __init__(self, max_workers: int = 2):
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="pipeline-job")
        self._active_jobs: Dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def submit_job(self, case_id: str, run_id: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Submits an analysis run to the background thread pool.
        """
        with self._lock:
            if run_id in self._active_jobs:
                logger.warning(f"Run {run_id} is already submitted or executing.")
                return False
            stop_event = threading.Event()
            self._active_jobs[run_id] = stop_event

        self.executor.submit(self._run_job_wrapper, case_id, run_id, config or {}, stop_event)
        return True

    def is_running(self, run_id: str) -> bool:
        """Checks if a job is currently active in memory."""
        with self._lock:
            return run_id in self._active_jobs

    def cancel_job(self, run_id: str) -> bool:
        """Signals cancellation to an active job."""
        with self._lock:
            if run_id in self._active_jobs:
                self._active_jobs[run_id].set()
                return True
        return False

    def _run_job_wrapper(
        self,
        case_id: str,
        run_id: str,
        config: Dict[str, Any],
        stop_event: threading.Event,
    ):
        """
        Thread target executing the pipeline with a dedicated DB session.
        """
        logger.info(f"Starting background execution for run {run_id} (case: {case_id})")
        from backend.app.db.session import init_db
        init_db()
        db = SessionLocal()
        try:
            pipeline = AnalysisPipeline(
                case_id=case_id,
                run_id=run_id,
                config=config,
                db_session=db,
            )
            pipeline.execute()
            logger.info(f"Successfully completed background run {run_id}")
        except Exception as exc:
            logger.exception(f"Background run {run_id} failed with error: {exc}")
        finally:
            try:
                db.close()
            except Exception:
                pass
            with self._lock:
                self._active_jobs.pop(run_id, None)


job_manager = JobManager()

