"""Contract tests without GPU/models: run in an environment with FastAPI + httpx."""
import base64
import io
import json
import threading
import unittest
import wave
from unittest.mock import patch

from fastapi.testclient import TestClient
import server


def wav(channels=1, seconds=1):
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setparams((channels, 2, 16000, 0, "NONE", "not compressed"))
        audio.writeframes(b"\0\0" * 16000 * channels * seconds)
    return output.getvalue()


class FakeEngine:
    voice = "ef_dora"
    stt_model = "small"

    def transcribe(self, data):
        return {"text": "Quiero café"}

    def speech(self, parts, cancelled):
        for _ in parts:
            yield server.frame({"pcm": base64.b64encode(b"\0\0" * 100).decode(), "sample_rate": 24000})
        yield server.frame({"done": True})


class ServiceTests(unittest.TestCase):
    def test_long_spanish_text_is_split_without_loss(self):
        text = "Puedes tomar un café en el cuarto piso. " + "Una recomendación con información verificada " * 20
        parts = list(server.text_segments(text))
        self.assertGreater(len(parts), 2)
        self.assertTrue(all(len(part) <= 160 for part in parts))
        self.assertEqual(" ".join(parts), text.strip())
        with self.assertRaises(ValueError):
            list(server.text_segments("x" * 161))

    def test_invalid_and_truncated_wav_rejected(self):
        server.validate_wav(wav())
        for data in (wav(channels=2), wav(seconds=16), wav()[:-2], b"garbage"):
            with self.assertRaises(ValueError):
                server.validate_wav(data)

    def test_service_warmup_health_transcription_and_framed_stream(self):
        with patch.object(server, "Engine", FakeEngine), TestClient(server.app) as client:
            self.assertEqual(client.get("/health").json()["status"], "ready")
            self.assertEqual(client.post("/transcribe", content=wav()).json()["text"], "Quiero café")
            self.assertEqual(client.post("/transcribe", content=b"bad").status_code, 400)
            self.assertEqual(client.post("/transcribe", content=b"x" * 1_000_001).status_code, 413)
            result = client.post("/speech", json={"text": "Hola. Bienvenido."})
            self.assertEqual(result.status_code, 200)
            frames = [json.loads(line) for line in result.iter_lines()]
            self.assertEqual(len(frames), 3)
            self.assertTrue(frames[-1]["done"])
            self.assertEqual(client.post("/speech", json={"text": "  "}).status_code, 400)
            self.assertEqual(client.post("/speech", json={"text": "x" * 2001}).status_code, 422)

    def test_busy_engine_returns_503_before_audio_headers(self):
        engine = server.Engine.__new__(server.Engine)
        engine.lock = threading.Lock()
        engine.lock.acquire()
        with patch.object(server, "Engine", return_value=engine), TestClient(server.app) as client:
            response = client.post("/speech", json={"text": "Hola"})
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.headers["retry-after"], "1")
            self.assertEqual(client.post("/transcribe", content=wav()).status_code, 503)

    def test_cancelled_generator_releases_gpu_slot(self):
        engine = server.Engine.__new__(server.Engine)
        engine.lock = threading.Lock()
        cancelled = threading.Event()
        cancelled.set()
        self.assertEqual(list(engine.speech(["Hola"], cancelled)), [])
        self.assertFalse(engine.lock.locked())


if __name__ == "__main__":
    unittest.main()
