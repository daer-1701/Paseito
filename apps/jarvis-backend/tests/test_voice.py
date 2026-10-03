import json
import unittest
from unittest.mock import patch

from jarvis.voice import synthesize


class VoiceTests(unittest.TestCase):
    def test_openai_tts_uses_wav_and_persona_instructions(self):
        captured = []

        class Response:
            headers = type("Headers", (), {"get_content_type": lambda self: "audio/wav"})()

            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

            def read(self, *_):
                return b"RIFF" + b"x" * 100

        def fake_urlopen(request, timeout):
            captured.append((request, timeout))
            return Response()

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "JARVIS_TTS_PROVIDER": "openai"}), \
                patch("urllib.request.urlopen", fake_urlopen):
            audio, mime = synthesize("Hola, **Jarvis**")

        request, timeout = captured[0]
        body = json.loads(request.data)
        self.assertEqual(request.full_url, "https://api.openai.com/v1/audio/speech")
        self.assertEqual(timeout, 25)
        self.assertEqual(body["response_format"], "wav")
        self.assertEqual(body["voice"], "marin")
        self.assertIn("español latino", body["instructions"])
        self.assertEqual(body["input"], "Hola, Jarvis")
        self.assertEqual(mime, "audio/wav")
        self.assertTrue(audio.startswith(b"RIFF"))


if __name__ == "__main__":
    unittest.main()
