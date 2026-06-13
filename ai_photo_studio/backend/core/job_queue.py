"""
Async job queue with progress tracking and WebSocket broadcast.
Handles single and batch image processing jobs.
"""

import uuid
import time
import asyncio
import logging
import traceback
from enum import Enum
from typing import Callable, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """Represents a processing job."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    plugin: str = ""
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0  # 0-100
    message: str = ""
    input_files: list[str] = field(default_factory=list)
    output_files: list[str] = field(default_factory=list)
    params: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None
    is_batch: bool = False
    batch_total: int = 0
    batch_completed: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "plugin": self.plugin,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "input_files": self.input_files,
            "output_files": self.output_files,
            "params": self.params,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "is_batch": self.is_batch,
            "batch_total": self.batch_total,
            "batch_completed": self.batch_completed,
        }

    @property
    def elapsed_seconds(self) -> float:
        if self.started_at is None:
            return 0.0
        end = self.completed_at or time.time()
        return end - self.started_at


class JobQueue:
    """
    Async job queue with thread pool execution and WebSocket progress broadcast.
    """

    def __init__(self, max_workers: int = 2):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._jobs: dict[str, Job] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._ws_clients: list = []  # WebSocket connections for progress
        self._processing_task: Optional[asyncio.Task] = None
        self._running = False
        self._max_history = 100

    async def start(self):
        """Start the queue processor."""
        self._running = True
        self._processing_task = asyncio.create_task(self._process_loop())
        logger.info("Job queue started")

    async def stop(self):
        """Stop the queue processor."""
        self._running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        self._executor.shutdown(wait=False)
        logger.info("Job queue stopped")

    async def submit(
        self,
        plugin: str,
        input_files: list[str],
        params: dict,
        process_fn: Callable,
        is_batch: bool = False,
    ) -> Job:
        """
        Submit a new job to the queue.

        Args:
            plugin: Plugin name
            input_files: List of input file paths
            params: Processing parameters
            process_fn: The actual processing function
            is_batch: Whether this is a batch job

        Returns:
            The created Job object
        """
        job = Job(
            plugin=plugin,
            input_files=input_files,
            params=params,
            is_batch=is_batch,
            batch_total=len(input_files) if is_batch else 0,
        )
        self._jobs[job.id] = job
        await self._queue.put((job, process_fn))
        await self._broadcast_progress(job)
        logger.info("Job %s submitted (plugin: %s, files: %d)", job.id, plugin, len(input_files))
        return job

    async def cancel(self, job_id: str) -> bool:
        """Cancel a pending job."""
        job = self._jobs.get(job_id)
        if job and job.status == JobStatus.PENDING:
            job.status = JobStatus.CANCELLED
            job.completed_at = time.time()
            await self._broadcast_progress(job)
            return True
        return False

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        return self._jobs.get(job_id)

    def get_all_jobs(self, limit: int = 50, offset: int = 0) -> list[Job]:
        """Get all jobs, newest first."""
        jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
        return jobs[offset : offset + limit]

    def get_active_jobs(self) -> list[Job]:
        """Get currently running and pending jobs."""
        return [
            j for j in self._jobs.values() if j.status in (JobStatus.PENDING, JobStatus.RUNNING)
        ]

    async def _process_loop(self):
        """Main processing loop — pulls jobs from queue and executes them."""
        while self._running:
            try:
                job, process_fn = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            if job.status == JobStatus.CANCELLED:
                continue

            job.status = JobStatus.RUNNING
            job.started_at = time.time()
            job.message = "Processing..."
            await self._broadcast_progress(job)

            try:
                # Create a progress callback for this job
                async def progress_cb(pct: float, msg: str = ""):
                    job.progress = pct
                    if msg:
                        job.message = msg
                    await self._broadcast_progress(job)

                # Run in thread pool to not block the event loop
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self._executor,
                    lambda: process_fn(
                        job.input_files,
                        job.params,
                        lambda p, m="": asyncio.run_coroutine_threadsafe(progress_cb(p, m), loop),
                    ),
                )

                job.output_files = result if isinstance(result, list) else [result]
                job.status = JobStatus.COMPLETED
                job.progress = 100.0
                job.message = "Completed"
                job.completed_at = time.time()
                logger.info("Job %s completed in %.1f s", job.id, job.elapsed_seconds)

            except Exception as e:
                job.status = JobStatus.FAILED
                job.error = str(e)
                job.message = f"Failed: {e}"
                job.completed_at = time.time()
                logger.error("Job %s failed: %s\n%s", job.id, e, traceback.format_exc())

            await self._broadcast_progress(job)
            self._trim_history()

    def register_ws_client(self, ws):
        """Register a WebSocket connection for progress updates."""
        self._ws_clients.append(ws)

    def unregister_ws_client(self, ws):
        """Remove a WebSocket connection."""
        if ws in self._ws_clients:
            self._ws_clients.remove(ws)

    async def _broadcast_progress(self, job: Job):
        """Send job progress to all connected WebSocket clients."""
        message = {
            "type": "job_progress",
            "job": job.to_dict(),
        }
        disconnected = []
        for ws in self._ws_clients:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self._ws_clients.remove(ws)

    def _trim_history(self):
        """Remove old completed/failed jobs to prevent memory bloat."""
        if len(self._jobs) <= self._max_history:
            return
        completed = sorted(
            [
                j
                for j in self._jobs.values()
                if j.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)
            ],
            key=lambda j: j.completed_at or 0,
        )
        while len(self._jobs) > self._max_history and completed:
            old = completed.pop(0)
            del self._jobs[old.id]


# Global singleton
_job_queue: Optional[JobQueue] = None


def get_job_queue() -> JobQueue:
    """Get or create the global job queue."""
    global _job_queue
    if _job_queue is None:
        _job_queue = JobQueue()
    return _job_queue
