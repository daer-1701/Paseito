"""Cancellation regression: runs with the voice image, without GPU inference."""
import threading
import unittest
from types import SimpleNamespace
import anyio
import server


class SlowEngine:
    def __init__(self):
        self.lock = threading.Lock()
        self.entered = threading.Event()
        self.release = threading.Event()
        self.closed = threading.Event()

    def speech(self, parts, cancelled):
        with self.lock:
            try:
                yield server.frame({'pcm': 'AAA=', 'sample_rate': 24000})
                self.entered.set()
                self.release.wait(2)
                if not cancelled.is_set():
                    yield server.frame({'done': True})
            finally:
                self.closed.set()


class CancellationTests(unittest.TestCase):
    def test_disconnect_waits_for_worker_before_closing_generator(self):
        engine = SlowEngine()

        async def scenario():
            request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(engine=engine)))
            response = await server.speech(server.SpeechInput(text='Prueba.'), request)
            async def consume():
                async for _ in response.body_iterator:
                    pass
            async with anyio.create_task_group() as group:
                group.start_soon(consume)
                self.assertTrue(await anyio.to_thread.run_sync(engine.entered.wait, 1))
                group.cancel_scope.cancel()
                with anyio.CancelScope(shield=True):
                    await anyio.sleep(0.02)
                    engine.release.set()
            self.assertTrue(engine.closed.is_set())
            self.assertFalse(engine.lock.locked())

        anyio.run(scenario)


if __name__ == '__main__':
    unittest.main()
