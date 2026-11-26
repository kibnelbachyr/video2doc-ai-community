"""
job_store.py
------------
Thin persistence layer for job state using Azure Blob Storage.

Layout inside the 'jobs' container:
  {job_id}/state.json   – JobState as JSON
  {job_id}/{filename}   – uploaded video file (temp during processing)
  {job_id}/result.md    – generated Markdown (written when status == done)
"""

import os
import threading
from datetime import datetime, timezone
from uuid import uuid4

from azure.storage.blob import BlobServiceClient

from api.models import JobState, JobStatus, JobStep

_CONTAINER = "jobs"

# In-memory job state store — used when MOCK_TRANSCRIPTION + MOCK_VISION are
# both true so the API runs without any Azure credentials.
_MEM_STORE: dict[str, JobState] = {}
_MEM_RESULTS: dict[str, str] = {}
_MEM_LOCK = threading.RLock()
_MAX_MEMORY_JOBS = 32
_MAX_RESULT_BYTES = 20 * 1024 * 1024


def save_mock_result(job_id: str, markdown: str) -> None:
    if len(markdown.encode('utf-8')) > _MAX_RESULT_BYTES:
        raise ValueError('Result exceeds local size limit')
    with _MEM_LOCK:
        if job_id not in _MEM_STORE:
            raise KeyError(job_id)
        _MEM_RESULTS[job_id] = markdown


def get_mock_result(job_id: str) -> str | None:
    with _MEM_LOCK:
        return _MEM_RESULTS.get(job_id)


def _blob_client() -> BlobServiceClient:
    return BlobServiceClient.from_connection_string(
        os.environ["AZURE_STORAGE_CONNECTION_STRING"]
    )


# ── Job lifecycle ─────────────────────────────────────────────────────────────

def create_job(video_filename: str, *, in_memory: bool = False) -> JobState:
    now = datetime.now(timezone.utc)
    state = JobState(
        job_id=str(uuid4()),
        status=JobStatus.PENDING,
        step=JobStep.UPLOADING,
        video_filename=video_filename,
        created_at=now,
        updated_at=now,
    )
    if in_memory:
        with _MEM_LOCK:
            if len(_MEM_STORE) >= _MAX_MEMORY_JOBS:
                terminal = next((rid for rid, item in _MEM_STORE.items() if item.status in (JobStatus.DONE, JobStatus.FAILED)), None)
                if terminal is None:
                    raise RuntimeError('Local job history full')
                _MEM_STORE.pop(terminal)
                _MEM_RESULTS.pop(terminal, None)
            _MEM_STORE[state.job_id] = state.model_copy(deep=True)
    else:
        _write_state(state)
    return state


def get_job(job_id: str) -> JobState:
    with _MEM_LOCK:
        if job_id in _MEM_STORE:
            return _MEM_STORE[job_id].model_copy(deep=True)
    if (os.environ.get("MOCK_TRANSCRIPTION", "false").lower() == "true"
            and os.environ.get("MOCK_VISION", "false").lower() == "true"):
        raise KeyError(job_id)
    data = (
        _blob_client()
        .get_blob_client(_CONTAINER, f"{job_id}/state.json")
        .download_blob()
        .readall()
    )
    return JobState.model_validate_json(data)


def update_job(job_id: str, **kwargs) -> JobState:
    state = get_job(job_id)
    for key, value in kwargs.items():
        setattr(state, key, value)
    state.updated_at = datetime.now(timezone.utc)
    with _MEM_LOCK:
        if job_id in _MEM_STORE:
            _MEM_STORE[job_id] = state.model_copy(deep=True)
            return state
    _write_state(state)
    return state


def _write_state(state: JobState) -> None:
    (
        _blob_client()
        .get_blob_client(_CONTAINER, f"{state.job_id}/state.json")
        .upload_blob(state.model_dump_json(), overwrite=True)
    )


# ── Video / result blobs ──────────────────────────────────────────────────────

def upload_video(job_id: str, video_bytes: bytes, filename: str) -> None:
    (
        _blob_client()
        .get_blob_client(_CONTAINER, f"{job_id}/{filename}")
        .upload_blob(video_bytes, overwrite=True)
    )


def download_video(job_id: str, filename: str, local_path: str) -> None:
    data = (
        _blob_client()
        .get_blob_client(_CONTAINER, f"{job_id}/{filename}")
        .download_blob()
        .readall()
    )
    with open(local_path, "wb") as f:
        f.write(data)


def save_result(job_id: str, markdown: str) -> None:
    if len(markdown.encode('utf-8')) > _MAX_RESULT_BYTES:
        raise ValueError('Result exceeds size limit')
    (
        _blob_client()
        .get_blob_client(_CONTAINER, f"{job_id}/result.md")
        .upload_blob(markdown.encode("utf-8"), overwrite=True)
    )


def get_result(job_id: str) -> str:
    return (
        _blob_client()
        .get_blob_client(_CONTAINER, f"{job_id}/result.md")
        .download_blob()
        .readall()
        .decode("utf-8")
    )
