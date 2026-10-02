"""Exercise the actual HTTP handler; binds an ephemeral loopback port."""
import json
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

from jarvis.api import Handler, ThreadingHTTPServer
from jarvis.voice import VoiceUnavailable


class QuietHandler(Handler):
    def log_message(self, *_):
        pass


class StreamingHTTPTests(unittest.TestCase):
    def test_first_frame_arrives_before_producer_finishes_and_busy_is_503(self):
        release = threading.Event()

        def output(_):
            yield b'{"pcm":"AAA=","sample_rate":24000}\n'
            if not release.wait(3):
                raise RuntimeError("client did not receive the first frame")
            yield b'{"done":true}\n'

        with ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            url = f"http://127.0.0.1:{server.server_port}/voice/stream"

            def request():
                return urllib.request.Request(url, data=b'{"text":"Hola"}',
                                              headers={"Content-Type": "application/json"})

            try:
                with patch("jarvis.api.stream_speech", output):
                    with urllib.request.urlopen(request(), timeout=4) as response:
                        self.assertIn(b"pcm", response.readline())
                        release.set()
                        self.assertTrue(json.loads(response.readline())["done"])
                        self.assertEqual(response.read(), b"")
                with patch("jarvis.api.stream_speech", side_effect=VoiceUnavailable("busy")):
                    with self.assertRaises(urllib.error.HTTPError) as result:
                        urllib.request.urlopen(request(), timeout=4)
                    self.assertEqual(result.exception.code, 503)
            finally:
                release.set()
                server.shutdown()
                thread.join()


if __name__ == "__main__":
    unittest.main()
