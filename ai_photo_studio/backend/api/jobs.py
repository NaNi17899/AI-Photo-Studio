"""
Job management API endpoints.
"""

import os
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from backend.core.job_queue import get_job_queue
from backend.core.plugin_registry import get_plugin_registry
from backend.storage.file_manager import get_file_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class JobSubmitRequest(BaseModel):
    plugin: str
    file_ids: list[str]
    params: dict = {}
    is_batch: bool = False


class JobSubmitResponse(BaseModel):
    job_id: str
    status: str
    message: str


@router.post("", response_model=JobSubmitResponse)
async def submit_job(request: JobSubmitRequest):
    """Submit a new processing job."""
    registry = get_plugin_registry()
    plugin = registry.get(request.plugin)
    if not plugin:
        raise HTTPException(400, f"Unknown plugin: {request.plugin}")

    # Resolve file IDs to paths
    fm = get_file_manager()
    input_paths = []
    for fid in request.file_ids:
        path = fm.get_upload_path(fid)
        if not path:
            raise HTTPException(404, f"File not found: {fid}")
        input_paths.append(path)

    # Validate params
    validated_params = plugin.validate_params(request.params)

    # Create the processing function
    def process_fn(inputs, params, progress_cb):
        return plugin.process(inputs, params, progress_cb)

    # Submit to queue
    queue = get_job_queue()
    job = await queue.submit(
        plugin=request.plugin,
        input_files=input_paths,
        params=validated_params,
        process_fn=process_fn,
        is_batch=request.is_batch or len(input_paths) > 1,
    )

    return JobSubmitResponse(
        job_id=job.id,
        status=job.status.value,
        message=f"Job submitted for {request.plugin}",
    )


@router.get("/{job_id}")
async def get_job(job_id: str):
    """Get job status and result."""
    queue = get_job_queue()
    job = queue.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job.to_dict()


@router.get("")
async def list_jobs(limit: int = 50, offset: int = 0, status: Optional[str] = None):
    """List all jobs with optional status filter."""
    queue = get_job_queue()
    jobs = queue.get_all_jobs(limit=limit, offset=offset)
    if status:
        jobs = [j for j in jobs if j.status.value == status]
    return {"jobs": [j.to_dict() for j in jobs], "total": len(jobs)}


@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a pending job."""
    queue = get_job_queue()
    success = await queue.cancel(job_id)
    if not success:
        raise HTTPException(400, "Job cannot be cancelled (may already be running)")
    return {"message": "Job cancelled"}


@router.get("/{job_id}/output/{filename}")
async def get_job_output(job_id: str, filename: str):
    """Download a job output file."""
    queue = get_job_queue()
    job = queue.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    # Find the output file
    for output_path in job.output_files:
        if os.path.basename(output_path) == filename:
            if os.path.exists(output_path):
                return FileResponse(output_path)
    raise HTTPException(404, "Output file not found")


@router.get("/active/list")
async def list_active_jobs():
    """List currently active (running/pending) jobs."""
    queue = get_job_queue()
    active = queue.get_active_jobs()
    return {"jobs": [j.to_dict() for j in active]}
