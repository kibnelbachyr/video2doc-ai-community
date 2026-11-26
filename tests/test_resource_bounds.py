import io
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from api.main import app
from api import job_store
from api.models import JobStatus
from api.routers import jobs
from src.extract_frames import extract_frames
from src.generate_docs import embed_frame_images
from src.transcribe import _extract_wav
import pipeline


class ResourceBoundsTests(unittest.TestCase):
    def test_invalid_sampling_rate(self):
        for rate in ("0", "61", "-1", "invalid"):
            with patch.dict(os.environ, {"MOCK_VISION": "false", "FRAMES_PER_MINUTE": rate}):
                with tempfile.TemporaryDirectory() as root:
                    with self.assertRaises(ValueError):
                        extract_frames("unused.mp4", root)

    def test_frame_timeout_and_local_protocol(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {"MOCK_VISION": "false", "FRAMES_PER_MINUTE": "12"}):
            with patch("src.extract_frames.subprocess.run", side_effect=subprocess.TimeoutExpired("ffmpeg", 120)) as run:
                with self.assertRaises(subprocess.TimeoutExpired):
                    extract_frames("unused.mp4", root)
                self.assertEqual(run.call_args.kwargs["timeout"], 120)
                self.assertIn("file,pipe", run.call_args.args[0])
                self.assertIn("121", run.call_args.args[0])

    def test_audio_timeout(self):
        with patch("src.transcribe.subprocess.run", side_effect=subprocess.TimeoutExpired("ffmpeg", 120)) as run:
            with self.assertRaises(subprocess.TimeoutExpired):
                _extract_wav("unused.mp4", "unused.wav")
            self.assertEqual(run.call_args.kwargs["timeout"], 120)

    def test_existing_frame_rejected_before_subprocess(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {"MOCK_VISION": "false", "FRAMES_PER_MINUTE": "12"}):
            pathlib.Path(root, "frame_000001.png").write_bytes(b"old")
            with patch("src.extract_frames.subprocess.run") as run:
                with self.assertRaises(ValueError):
                    extract_frames("unused.mp4", root)
                run.assert_not_called()

    def test_invalid_frame_image_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            pathlib.Path(root, "frame_000001.png").write_bytes(b"not PNG")
            with self.assertRaises(ValueError):
                embed_frame_images("![x](frame_000001.png)", root)

    def test_cli_failure_preserves_parent(self):
        with tempfile.TemporaryDirectory() as root:
            parent = pathlib.Path(root, "frames")
            parent.mkdir()
            marker = parent / "keep.txt"
            marker.write_text("keep")
            video = pathlib.Path(root, "demo.mp4")
            video.touch()
            with patch.dict(os.environ, {"MOCK_TRANSCRIPTION": "true", "MOCK_VISION": "false", "MOCK_GENERATION": "true"}, clear=True):
                with patch.object(sys, "argv", ["pipeline.py", "--video", str(video), "--frames", str(parent), "--output", str(pathlib.Path(root, "out.md"))]):
                    with patch("pipeline.extract_frames", side_effect=RuntimeError("synthetic failure")):
                        with self.assertRaises(RuntimeError):
                            pipeline.main()
            self.assertEqual(list(parent.iterdir()), [marker])

    def test_admission_rejects_without_creating_job(self):
        self.assertTrue(jobs._JOB_SLOTS.acquire(blocking=False))
        self.assertTrue(jobs._JOB_SLOTS.acquire(blocking=False))
        try:
            with TestClient(app) as client, patch("api.routers.jobs.job_store.create_job") as create:
                response = client.post("/api/jobs", files={"file": ("demo.mp4", b"x", "video/mp4")})
                self.assertEqual(response.status_code, 429)
                create.assert_not_called()
        finally:
            jobs._JOB_SLOTS.release()
            jobs._JOB_SLOTS.release()

    def test_terminal_eviction_removes_result(self):
        with patch.dict(job_store._MEM_STORE, {}, clear=True), patch.dict(job_store._MEM_RESULTS, {}, clear=True):
            with patch.object(job_store, "_MAX_MEMORY_JOBS", 1):
                first = job_store.create_job("one.mp4", in_memory=True)
                job_store.save_mock_result(first.job_id, "synthetic")
                job_store.update_job(first.job_id, status=JobStatus.DONE)
                second = job_store.create_job("two.mp4", in_memory=True)
                self.assertNotIn(first.job_id, job_store._MEM_STORE)
                self.assertIsNone(job_store.get_mock_result(first.job_id))
                self.assertIn(second.job_id, job_store._MEM_STORE)

    def test_active_job_not_evicted(self):
        with patch.dict(job_store._MEM_STORE, {}, clear=True), patch.dict(job_store._MEM_RESULTS, {}, clear=True):
            with patch.object(job_store, "_MAX_MEMORY_JOBS", 1):
                first = job_store.create_job("one.mp4", in_memory=True)
                with self.assertRaises(RuntimeError):
                    job_store.create_job("two.mp4", in_memory=True)
                self.assertIn(first.job_id, job_store._MEM_STORE)
