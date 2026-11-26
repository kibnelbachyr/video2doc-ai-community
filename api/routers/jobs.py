"""
routers/jobs.py
---------------
REST endpoints for the video-to-documentation pipeline.

  POST   /api/jobs                – upload a video, start the pipeline
  GET    /api/jobs/{job_id}       – poll job status
  GET    /api/jobs/{job_id}/result – fetch the generated Markdown
"""

import os
import threading
import unicodedata
from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import PlainTextResponse

from api import job_store
from api.models import JobStatus, STEP_LABELS
from api.pipeline_runner import run_pipeline, get_mock_result

router = APIRouter()

_MAX_UPLOAD_MB = 500
_READ_CHUNK = 1024 * 1024
_JOB_SLOTS = threading.BoundedSemaphore(2)


def _run_admitted(job_id: str) -> None:
    try:
        run_pipeline(job_id)
    finally:
        _JOB_SLOTS.release()


def _valid_job_id(value: str) -> bool:
    try:
        return str(UUID(value)) == value
    except (ValueError, TypeError, AttributeError):
        return False


async def _read_upload(file: UploadFile, mock: bool) -> bytes:
    limit = _MAX_UPLOAD_MB * 1024 * 1024
    if file.size is not None and file.size > limit:
        raise HTTPException(413, detail="File exceeds maximum upload size.")
    if mock and file.size is not None:
        return b""
    data = bytearray()
    total = 0
    while True:
        chunk = await file.read(min(_READ_CHUNK, limit - total + 1))
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise HTTPException(413, detail="File exceeds maximum upload size.")
        if not mock:
            data.extend(chunk)
    return bytes(data)
_ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".wmv"}


@router.post("/jobs", status_code=202)
async def create_job(file: UploadFile = File(...)):
    try:
        return await _create_job(file)
    finally:
        await file.close()


async def _create_job(file: UploadFile):
    """
    Upload a video file and immediately start the documentation pipeline.

    In full mock mode (MOCK_TRANSCRIPTION + MOCK_VISION both true) the file
    bytes are discarded immediately — only the filename is used — so this
    works with any tiny placeholder file and avoids proxy size limits.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    # Keep the client filename a single path component on Windows and POSIX.
    if ("/" in file.filename or "\\" in file.filename or ":" in file.filename
            or any(unicodedata.category(char).startswith('C') for char in file.filename)
            or file.filename != file.filename.strip()
            or len(file.filename.encode('utf-8')) > 200):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type.",
        )

    full_mock = (
        os.environ.get("MOCK_TRANSCRIPTION", "false").lower() == "true"
        and os.environ.get("MOCK_VISION", "false").lower() == "true"
    )

    if not _JOB_SLOTS.acquire(blocking=False):
        raise HTTPException(429, detail='Job capacity reached; retry later.')
    started = False
    try:
        result = await _start_job(file, full_mock)
        started = True
        return result
    finally:
        if not started:
            _JOB_SLOTS.release()


async def _start_job(file: UploadFile, full_mock: bool):
    video_bytes = await _read_upload(file, full_mock)
    if not full_mock and not video_bytes:
        raise HTTPException(400, detail="Empty video upload.")
    state = None
    try:
        state = job_store.create_job(file.filename, in_memory=full_mock)
        if not full_mock:
            job_store.upload_video(state.job_id, video_bytes, file.filename)
        threading.Thread(target=_run_admitted, args=(state.job_id,), daemon=True).start()
    except Exception:
        if state is not None:
            try:
                job_store.update_job(state.job_id, status=JobStatus.FAILED, error="Job initialization failed.")
            except Exception:
                pass
        raise HTTPException(503, detail="Could not start job.") from None

    return {
        "job_id": state.job_id,
        "status": state.status,
        "message": "Processing started. Poll /api/jobs/{job_id} for progress.",
    }


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Return the current status and step for a job."""
    if not _valid_job_id(job_id):
        raise HTTPException(status_code=404, detail="Job not found.")
    try:
        state = job_store.get_job(job_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found.")

    return {
        "job_id":     state.job_id,
        "status":     state.status,
        "step":       state.step,
        "step_label": STEP_LABELS.get(state.step, "") if state.step else "",
        "error":      "Pipeline failed." if state.status == JobStatus.FAILED else None,
        "created_at": state.created_at.isoformat(),
        "updated_at": state.updated_at.isoformat(),
        "result_url": f"/api/jobs/{job_id}/result" if state.status == JobStatus.DONE else None,
    }


@router.get("/jobs/{job_id}/result", response_class=PlainTextResponse)
async def get_job_result(job_id: str):
    """Return the generated Markdown document for a completed job."""
    if not _valid_job_id(job_id):
        raise HTTPException(status_code=404, detail="Job not found.")
    try:
        state = job_store.get_job(job_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found.")

    if state.status == JobStatus.FAILED:
        raise HTTPException(status_code=422, detail="Pipeline failed.")

    if state.status != JobStatus.DONE:
        raise HTTPException(
            status_code=409,
            detail=f"Job is not finished yet. Current status: {state.status}",
        )

    # Try in-memory cache first (mock mode), then fall back to Blob Storage.
    mock_md = get_mock_result(job_id)
    if mock_md is not None:
        return mock_md
    if (os.environ.get("MOCK_TRANSCRIPTION", "false").lower() == "true"
            and os.environ.get("MOCK_VISION", "false").lower() == "true"):
        raise HTTPException(status_code=500, detail="Mock result not found.")
    try:
        return job_store.get_result(job_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Result blob not found.")
