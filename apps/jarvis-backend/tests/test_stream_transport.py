import unittest
from jarvis.stream_transport import sse_frames
from jarvis.voice import VoiceUnavailable


class StreamTransportTests(unittest.TestCase):
    def test_split_network_chunks_become_complete_sse_events(self):
        def source():
            yield b'{"pcm":"AA'
            yield b'A=","sample_rate":24000}\n{"done":true}\n'
        self.assertEqual(list(sse_frames(source())), [
            b'data: {"pcm":"AAA=","sample_rate":24000}\n\n',
            b'data: {"done":true}\n\n'])

    def test_cancellation_closes_upstream(self):
        closed = []
        def source():
            try:
                yield b'{"done":true}\n'
                raise AssertionError('must not read ahead')
            finally:
                closed.append(True)
        stream = sse_frames(source())
        next(stream)
        stream.close()
        self.assertEqual(closed, [True])

    def test_unfinished_frame_is_rejected(self):
        def source():
            yield b'{"pcm":"AAA="}'
        with self.assertRaises(VoiceUnavailable):
            list(sse_frames(source()))
