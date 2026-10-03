// PCM16 mono, framed as NDJSON. Playback begins with the first generated segment.
export async function* readFrames(body) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let pending = "";
  let done = false;
  let total = 0;
  try {
    while (true) {
      const result = await reader.read();
      if (result.done) break;
      total += result.value.byteLength;
      if (total > 16_000_000) throw new Error("Audio demasiado grande");
      pending += decoder.decode(result.value, { stream: true });
      let newline;
      while ((newline = pending.indexOf("\n")) >= 0) {
        const line = pending.slice(0, newline);
        pending = pending.slice(newline + 1);
        if (!line.trim()) continue;
        if (done) throw new Error("Datos después del cierre de audio");
        const event = JSON.parse(line);
        if (event.error) throw new Error("Audio interrumpido");
        if (event.done === true) done = true;
        else if (typeof event.pcm !== "string" || event.sample_rate !== 24000) {
          throw new Error("Formato de audio inesperado");
        }
        yield event;
      }
    }
    if (!done || pending.trim()) throw new Error("Audio incompleto");
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

export class StreamPlayer {
  unlock() {
    this.context ??= new AudioContext();
    return this.context.resume();
  }

  async play(url, text, { signal, onAnalyser, onFirstAudio } = {}) {
    await this.unlock();
    const ctx = this.context;
    const started = performance.now();
    const nodes = new Set();
    const endings = [];
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 512;
    analyser.connect(ctx.destination);
    let nextTime = ctx.currentTime;
    let first = true;
    let ttfa = null;
    const stop = () => { for (const source of nodes) source.stop(); };
    signal?.addEventListener("abort", stop, { once: true });
    onAnalyser?.(analyser);
    try {
      const response = await fetch(url, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }), signal,
      });
      if (!response.ok) throw new Error(`Voz no disponible (${response.status})`);
      for await (const event of readFrames(response.body)) {
        signal?.throwIfAborted();
        if (event.done) continue;
        const binary = atob(event.pcm);
        if (!binary.length || binary.length % 2) throw new Error("PCM inválido");
        const bytes = Uint8Array.from(binary, char => char.charCodeAt(0));
        const view = new DataView(bytes.buffer);
        const buffer = ctx.createBuffer(1, bytes.length / 2, event.sample_rate);
        const samples = buffer.getChannelData(0);
        for (let i = 0; i < samples.length; i++) samples[i] = view.getInt16(i * 2, true) / 32768;
        const source = ctx.createBufferSource();
        source.buffer = buffer;
        source.connect(analyser);
        nodes.add(source);
        endings.push(new Promise(resolve => {
          source.onended = () => { nodes.delete(source); source.disconnect(); resolve(); };
        }));
        nextTime = Math.max(nextTime, ctx.currentTime + 0.04);
        source.start(nextTime);
        if (first) {
          ttfa = performance.now() - started + (nextTime - ctx.currentTime) * 1000;
          onFirstAudio?.(ttfa);
          first = false;
        }
        nextTime += buffer.duration;
      }
      if (first) throw new Error("Audio vacío");
      await Promise.all(endings);
      signal?.throwIfAborted();
      return { first_audio_ms: Math.round(ttfa) };
    } finally {
      stop();
      signal?.removeEventListener("abort", stop);
      onAnalyser?.(null);
      analyser.disconnect();
    }
  }
}
