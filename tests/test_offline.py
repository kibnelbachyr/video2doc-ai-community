"""Synthetic offline regression tests; no actual video, cloud account or model."""
import os
import pathlib
import socket
import sys
import tempfile
import time
import unittest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from api.main import app
from src.generate_docs import generate_documentation
import pipeline

FLAGS = {"MOCK_TRANSCRIPTION": "true", "MOCK_VISION": "true", "MOCK_GENERATION": "true"}


class OfflineTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(os.environ, FLAGS, clear=True))
        self.enterContext(patch.object(socket.socket, "connect", side_effect=AssertionError("network forbidden")))
        self.enterContext(patch.object(socket.socket, "connect_ex", side_effect=AssertionError("network forbidden")))
        self.enterContext(patch("api.job_store._blob_client", side_effect=AssertionError("Blob forbidden")))

    def test_generation_is_fixed_and_labelled(self):
        with patch("src.generate_docs.AzureOpenAI", side_effect=AssertionError("model forbidden")):
            first = generate_documentation("one", "image one")
            self.assertEqual(first, generate_documentation("two", "image two"))
        self.assertIn("MOCK OUTPUT", first)
        for heading in ("Tutorial", "How-to Guide", "Reference", "Explanation"):
            self.assertIn("## " + heading, first)

    def test_cli_no_media_or_credentials(self):
        with tempfile.TemporaryDirectory() as root:
            p = pathlib.Path(root)
            frames = p / "frames"
            frames.mkdir()
            marker = frames / "keep.txt"
            marker.write_text("keep")
            output = p / "out.md"
            with patch.object(sys, "argv", ["pipeline.py", "--video", str(p / "absent.mp4"), "--output", str(output), "--frames", str(frames)]):
                pipeline.main()
            self.assertIn("MOCK OUTPUT", output.read_text())
            self.assertEqual(marker.read_text(), "keep")

    def test_cli_rejects_upload(self):
        with tempfile.TemporaryDirectory() as root:
            output = pathlib.Path(root) / "out.md"
            with patch.object(sys, "argv", ["pipeline.py", "--video", "absent.mp4", "--output", str(output), "--upload"]):
                with self.assertRaises(SystemExit) as exc:
                    pipeline.main()
            self.assertEqual(exc.exception.code, 2)
            self.assertFalse(output.exists())

    def test_api_completes_and_returns_result(self):
        with TestClient(app) as client:
            response = client.post("/api/jobs", files={"file": ("synthetic.mp4", b"not a video", "video/mp4")})
            self.assertEqual(response.status_code, 202)
            rid = response.json()["job_id"]
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                state = client.get("/api/jobs/" + rid).json()
                if state["status"] in ("done", "failed"):
                    break
                time.sleep(0.02)
            self.assertEqual(state["status"], "done", state)
            result = client.get("/api/jobs/" + rid + "/result")
            self.assertEqual(result.status_code, 200)
            self.assertIn("MOCK OUTPUT", result.text)
            self.assertEqual(client.get("/api/jobs/unknown").status_code, 404)
            self.assertEqual(client.get("/api/jobs/unknown/result").status_code, 404)

    def test_api_rejects_path_like_filename(self):
        with TestClient(app) as client:
            with patch("api.routers.jobs.job_store.create_job", side_effect=AssertionError("must reject before state creation")):
                for name in ("../escape.mp4", "/tmp/escape.mp4", "C:escape.mp4"):
                    response = client.post("/api/jobs", files={"file": (name, b"placeholder", "video/mp4")})
                    self.assertEqual(response.status_code, 400, name)

    def test_live_dispatch_uses_sdk_stub(self):
        with patch.dict(os.environ, {"MOCK_GENERATION": "false", "AZURE_OPENAI_ENDPOINT": "https://example.invalid", "AZURE_OPENAI_KEY": "test-only"}):
            with patch("src.generate_docs.AzureOpenAI") as constructor:
                response = MagicMock()
                response.choices[0].message.content = "stubbed live output"
                constructor.return_value.chat.completions.create.return_value = response
                self.assertEqual(generate_documentation("transcript", "vision"), "stubbed live output")
                constructor.assert_called_once()
                constructor.return_value.chat.completions.create.assert_called_once()


if __name__ == "__main__":
    unittest.main()
