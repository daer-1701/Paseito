import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const source = await readFile(new URL('../../../frontend/js/stream-player.js', import.meta.url), 'utf8');
const { readFrames, StreamPlayer } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const pcm = JSON.stringify({ pcm: 'AAAAAA==', sample_rate: 24000 }) + '\n';
const done = '{"done":true}\n';
const encoder = new TextEncoder();
const body = chunks => new ReadableStream({ start(controller) {
  for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
  controller.close();
} });

test('accepts arbitrary network boundaries and rejects truncated/error streams', async () => {
  const frames = [];
  for await (const frame of readFrames(body([pcm.slice(0, 7), pcm.slice(7), done]))) frames.push(frame);
  assert.equal(frames.length, 2);
  assert.equal(frames[1].done, true);
  for (const chunks of [[pcm], [pcm, '{"error":"failed"}\n'], [done, pcm]]) {
    await assert.rejects(async () => { for await (const _ of readFrames(body(chunks))) {} });
  }
});

test('starts playback before final frame and abort stops scheduled sound', async () => {
  let started;
  const firstSound = new Promise(resolve => { started = resolve; });
  let stopped = 0;
  let controller;
  globalThis.AudioContext = class {
    currentTime = 0;
    destination = {};
    resume() { return Promise.resolve(); }
    createAnalyser() { return { connect() {}, disconnect() {}, fftSize: 512 }; }
    createBuffer(_channels, count, rate) { return { duration: count / rate, getChannelData: () => new Float32Array(count) }; }
    createBufferSource() { return {
      connect() {}, disconnect() {}, start() { started(); },
      stop() { stopped++; this.onended?.(); },
    }; }
  };
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (_url, options) => ({ ok: true, body: new ReadableStream({ start(c) {
    controller = c;
    options.signal.addEventListener('abort', () => c.error(options.signal.reason));
    c.enqueue(encoder.encode(pcm));
  } }) });
  try {
    const abort = new AbortController();
    const playing = new StreamPlayer().play('/voice/stream', 'Hola', { signal: abort.signal });
    const rejected = assert.rejects(playing, { name: 'AbortError' });
    await firstSound;
    assert.ok(controller, 'sound started before a done frame was sent');
    abort.abort();
    await rejected;
    assert.ok(stopped >= 1);
  } finally {
    globalThis.fetch = originalFetch;
    delete globalThis.AudioContext;
  }
});
