"""Exercise real local media decoding on generated, non-customer content."""
import base64
import os
import pathlib
import subprocess
import tempfile
import unittest
import wave
from unittest.mock import patch

from src.extract_frames import extract_frames
from src.generate_docs import embed_frame_images
from src.timestamps import format_timestamp
from src.transcribe import _extract_wav, _wav_chunks


class SyntheticMediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = pathlib.Path(cls.temp.name)
        cls.video = cls.root / "synthetic.mp4"
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "testsrc=size=160x96:rate=5",
                "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000",
                "-t", "3", "-c:v", "mpeg4", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-threads", "1", str(cls.video),
            ],
            check=True, timeout=30, capture_output=True,
        )

    def test_extract_real_frames_and_embed(self):
        frames_dir = self.root / "frames"
        with patch.dict(os.environ, {"MOCK_VISION": "false", "FRAMES_PER_MINUTE": "60"}, clear=True):
            frames = extract_frames(str(self.video), str(frames_dir))
        self.assertEqual(len(frames), 3)
        self.assertEqual([frame["timestamp"] for frame in frames], [0.0, 1.0, 2.0])
        first = frames[0]
        png = pathlib.Path(first["path"]).read_bytes()
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        markdown = f'![Synthetic frame]({first["filename"]})\n![Missing](frame_999999.png)'
        rendered = embed_frame_images(markdown, str(frames_dir))
        self.assertIn(base64.b64encode(png).decode("ascii"), rendered)
        self.assertNotIn("frame_999999.png", rendered)

    def test_extract_audio_and_chunk(self):
        wav = self.root / "synthetic.wav"
        _extract_wav(str(self.video), str(wav))
        with wave.open(str(wav), "rb") as decoded:
            self.assertEqual(decoded.getframerate(), 16000)
            self.assertEqual(decoded.getnchannels(), 1)
            self.assertEqual(decoded.getsampwidth(), 2)
            self.assertGreater(decoded.getnframes(), 40000)
        chunks = _wav_chunks(str(wav))
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0][0], 0.0)
        self.assertTrue(chunks[0][1].startswith(b"RIFF"))

    def test_timestamp_format(self):
        for seconds, expected in [(0, "00:00"), (1, "00:01"), (60, "01:00"), (125.4, "02:05"), (-2, "00:00")]:
            with self.subTest(seconds=seconds):
                self.assertEqual(format_timestamp(seconds), expected)
