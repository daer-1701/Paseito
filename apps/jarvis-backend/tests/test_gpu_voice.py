import base64
import io
import json
import os
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from jarvis import bootstrap, voice
from jarvis.store import connect


class GPUVoiceTests(unittest.TestCase):
    def test_proxy_yields_before_reading_full_response_and_closes_on_cancel(self):
        class Response:
            headers = type("Headers", (), {"get_content_type": lambda _: "application/x-ndjson"})()
            closed = False
            reads = 0

            def __enter__(self): return self
            def __exit__(self, *_): self.closed = True
            def read1(self, size):
                self.reads += 1
                if self.reads == 1: return b'{"pcm":"AAA=","sample_rate":24000}\n'
                raise AssertionError("must not buffer the next chunk")

        response = Response()
        with patch.dict(os.environ, {"JARVIS_VOICE_URL": "http://voice:8001", "JARVIS_TTS_PROVIDER": "gpu"}), \
                patch("urllib.request.urlopen", return_value=response) as opener:
            stream = voice.stream_speech("**Hola**")
            self.assertIn(b"pcm", next(stream))
            self.assertEqual(response.reads, 1)
            self.assertEqual(json.loads(opener.call_args[0][0].data)["text"], "Hola")
            stream.close()
            self.assertTrue(response.closed)

    def test_legacy_wav_and_truncated_audio(self):
        pcm = b"\0\0" * 100
        line = json.dumps({"pcm": base64.b64encode(pcm).decode(), "sample_rate": 24000}).encode() + b"\n"
        with patch("jarvis.voice.stream_speech", return_value=iter([line[:9], line[9:], b'{"done":true}\n'])):
            data, mime = voice._gpu_wav("Hola")
            self.assertEqual(mime, "audio/wav")
            with wave.open(io.BytesIO(data), "rb") as wav:
                self.assertEqual(wav.getframerate(), 24000)
                self.assertEqual(wav.readframes(100), pcm)
        with patch("jarvis.voice.stream_speech", return_value=iter([line])):
            with self.assertRaises(voice.VoiceUnavailable):
                voice._gpu_wav("Hola")

    def test_gpu_failure_never_spends_openai_tokens(self):
        with patch.dict(os.environ, {"JARVIS_TTS_PROVIDER": "gpu", "OPENAI_API_KEY": "test"}), \
                patch("jarvis.voice._gpu_wav", side_effect=voice.VoiceUnavailable("busy")), \
                patch("jarvis.voice._openai_synthesize") as paid:
            with self.assertRaises(voice.VoiceUnavailable):
                voice.synthesize("Hola")
            paid.assert_not_called()

    def test_bootstrap_is_offline_and_preserves_existing_records(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict(os.environ, {"JARVIS_DB": str(Path(directory) / "db.sqlite3")}), \
                patch("sys.argv", ["bootstrap"]), patch("jarvis.bootstrap.serve"), \
                patch("urllib.request.urlopen", side_effect=AssertionError("startup must be offline")):
            bootstrap.main()
            with connect() as db:
                self.assertEqual(db.execute("SELECT count(*) FROM records").fetchone()[0], 78)
                row = db.execute("SELECT id FROM records LIMIT 1").fetchone()
                db.execute("UPDATE records SET title='Administración actualizó' WHERE id=?", (row[0],))
            bootstrap.main()
            with connect() as db:
                self.assertEqual(db.execute("SELECT title FROM records WHERE id=?", (row[0],)).fetchone()[0], "Administración actualizó")


if __name__ == "__main__":
    unittest.main()
