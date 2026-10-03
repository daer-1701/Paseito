"""Measure the running deployment. No API keys or paid requests required in strict/GPU mode."""
import argparse
import base64
import json
import math
from pathlib import Path
import statistics
import time
import urllib.request


def request(url, payload, content_type="application/json"):
    body = json.dumps(payload).encode() if content_type == "application/json" else payload
    return urllib.request.urlopen(urllib.request.Request(url, data=body,
        headers={"Content-Type": content_type}, method="POST"), timeout=60)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--wav", type=Path, help="Optional recorded mono PCM16/16kHz WAV, <=15s")
    args = parser.parse_args()
    if not 1 <= args.runs <= 100:
        parser.error("runs must be 1..100")
    url = args.url.rstrip("/")
    with urllib.request.urlopen(url + "/voice/status", timeout=5) as response:
        config = json.load(response)
    if not config.get("streaming"):
        raise SystemExit("GPU streaming must be ready before benchmarking")
    measurements = []
    for run in range(args.runs):
        start = time.perf_counter()
        question = "¿Dónde puedo tomar un café?"
        if args.wav:
            with request(url + "/voice/transcribe", args.wav.read_bytes(), "audio/wav") as response:
                question = json.load(response)["text"]
            if not question:
                raise SystemExit("No speech detected in WAV")
        stt_ms = (time.perf_counter() - start) * 1000
        with request(url + "/chat", {"message": question}) as response:
            answer = json.load(response)
        if answer.get("answer_mode") != "strict":
            raise SystemExit("Benchmark requires strict mode to avoid paid LLM calls")
        chat_end = time.perf_counter()
        first = None
        done = False
        size = 0
        with request(url + "/voice/stream", {"text": answer["answer"]}) as response:
            for line in response:
                event = json.loads(line)
                if event.get("error"):
                    raise SystemExit("Voice stream failed")
                if "pcm" in event:
                    first = first or time.perf_counter()
                    size += len(base64.b64decode(event["pcm"], validate=True))
                done = done or event.get("done", False)
        if first is None or not done:
            raise SystemExit("Incomplete voice stream")
        end = time.perf_counter()
        row = {"run": run + 1, "stt_ms": round(stt_ms) if args.wav else None,
               "chat_ms": round((chat_end - start) * 1000 - stt_ms),
               "tts_first_pcm_ms": round((first - chat_end) * 1000),
               "pipeline_first_pcm_ms": round((first - start) * 1000),
               "tts_rtf": round((end - chat_end) / (size / 48000), 3)}
        measurements.append(row)
        print(json.dumps(row), flush=True)
    values = sorted(row["pipeline_first_pcm_ms"] for row in measurements)
    print(json.dumps({"median_ms": statistics.median(values),
                      "p95_ms": values[math.ceil(len(values) * .95) - 1],
                      "samples": len(values),
                      "note": "Excludes microphone silence, browser buffering and physical audio output. RTF <1 is faster than playback."}))


if __name__ == "__main__":
    main()
