import asyncio
import io
import os
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient
from api.main import app
from api.models import JobStatus
from api import job_store
from api.routers.jobs import _read_upload
from api.pipeline_runner import run_pipeline


FLAGS = {"MOCK_TRANSCRIPTION": "true", "MOCK_VISION": "true", "MOCK_GENERATION": "true"}


class UploadBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(os.environ, FLAGS, clear=True))
        self.enterContext(patch("api.job_store._blob_client", side_effect=AssertionError("cloud forbidden")))

    def test_size_rejected_before_job_creation(self):
        with TestClient(app) as client, patch("api.routers.jobs._MAX_UPLOAD_MB", 0), patch("api.routers.jobs.job_store.create_job") as create:
            response = client.post("/api/jobs", files={"file": ("demo.mp4", b"x", "video/mp4")})
            self.assertEqual(response.status_code, 413)
            create.assert_not_called()

    def test_unknown_size_bounded_read(self):
        file = UploadFile(io.BytesIO(b"x" * 1048577), filename="demo.mp4")
        with patch("api.routers.jobs._MAX_UPLOAD_MB", 1):
            with self.assertRaises(HTTPException) as exc:
                asyncio.run(_read_upload(file, False))
            self.assertEqual(exc.exception.status_code, 413)

    def test_valid_size_unknown(self):
        file = UploadFile(io.BytesIO(b"hello"), filename="demo.mp4")
        self.assertEqual(asyncio.run(_read_upload(file, False)), b"hello")

    def test_invalid_id_never_reaches_store(self):
        with TestClient(app) as client, patch("api.routers.jobs.job_store.get_job") as get:
            for route in ("/api/jobs/not-a-uuid", "/api/jobs/not-a-uuid/result"):
                self.assertEqual(client.get(route).status_code, 404)
            get.assert_not_called()

    def test_unicode_control_filename_rejected(self):
        with TestClient(app) as client, patch("api.routers.jobs.job_store.create_job") as create:
            response = client.post("/api/jobs", files={"file": ("demo\u202e.mp4", b"x", "video/mp4")})
            self.assertEqual(response.status_code, 400)
            create.assert_not_called()

    def test_pipeline_failure_sanitized(self):
        state = job_store.create_job("demo.mp4", in_memory=True)
        with patch("api.pipeline_runner.transcribe_file", side_effect=RuntimeError("synthetic-private-marker")):
            run_pipeline(state.job_id)
        with TestClient(app) as client:
            status = client.get("/api/jobs/" + state.job_id)
            result = client.get("/api/jobs/" + state.job_id + "/result")
            self.assertEqual(status.json()["status"], "failed")
            self.assertEqual(status.json()["error"], "Pipeline failed.")
            self.assertEqual(result.status_code, 422)
            self.assertNotIn("synthetic-private-marker", result.text)
            self.assertEqual(job_store.get_job(state.job_id).status, JobStatus.FAILED)

    def test_start_failure_is_generic(self):
        with TestClient(app) as client, patch("api.routers.jobs.threading") as threads:
            threads.Thread.return_value.start.side_effect = RuntimeError("synthetic-private-marker")
            response = client.post("/api/jobs", files={"file": ("demo.mp4", b"x", "video/mp4")})
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("synthetic-private-marker", response.text)
