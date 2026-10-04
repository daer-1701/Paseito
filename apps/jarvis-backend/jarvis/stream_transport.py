"""Translate internal NDJSON audio into actual SSE events for public tunnels."""
from .voice import VoiceUnavailable


def sse_frames(chunks):
    pending = b''
    try:
        for chunk in chunks:
            pending += chunk
            if len(pending) > 4_000_000:
                raise VoiceUnavailable('audio frame too large')
            while b'\n' in pending:
                line, pending = pending.split(b'\n', 1)
                if line.strip():
                    yield b'data: ' + line.rstrip(b'\r') + b'\n\n'
        if pending.strip():
            raise VoiceUnavailable('incomplete audio frame')
    finally:
        chunks.close()
