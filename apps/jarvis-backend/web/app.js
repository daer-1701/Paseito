const conversation = document.querySelector('#conversation');
const form = document.querySelector('#chatForm');
const messageInput = document.querySelector('#message');
const sendButton = document.querySelector('#send');
const recordButton = document.querySelector('#record');
const recordHint = document.querySelector('#recordHint');
const statusLine = document.querySelector('#status');
const spokenAudio = document.querySelector('#spokenAudio');

let sessionId = sessionStorage.getItem('jarvis-session') || null;
let recording = null;
let voiceReady = false;
let spokenAudioUrl = null;

function addTurn(role, text, sources = []) {
  const turn = document.createElement('div');
  turn.className = `turn ${role}`;
  const label = document.createElement('span');
  label.className = 'label';
  label.textContent = role === 'user' ? 'Tú' : 'Jarvis';
  turn.append(label, document.createTextNode(text));
  conversation.append(turn);
  if (sources.length) {
    const list = document.createElement('div');
    list.className = 'sources';
    list.append(document.createTextNode('Fuentes: '));
    sources.forEach((source, index) => {
      if (index) list.append(document.createTextNode(' · '));
      if (source.source_url) {
        const link = document.createElement('a');
        link.href = source.source_url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.textContent = source.title;
        list.append(link);
      } else {
        list.append(document.createTextNode(source.title));
      }
    });
    conversation.append(list);
  }
  conversation.scrollTop = conversation.scrollHeight;
}

async function requestJson(url, options) {
  const response = await fetch(url, options);
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `Error ${response.status}`);
  return body;
}

async function ask(text, spoken = false) {
  if (!text.trim()) return;
  sendButton.disabled = true;
  recordButton.disabled = true;
  addTurn('user', text);
  statusLine.textContent = 'Jarvis está buscando información…';
  try {
    const result = await requestJson('/chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session_id: sessionId }),
    });
    sessionId = result.session_id;
    sessionStorage.setItem('jarvis-session', sessionId);
    addTurn('assistant', result.answer, result.sources);
    statusLine.textContent = 'Listo.';
    if (spoken) await speak(result.answer);
  } catch (error) {
    addTurn('assistant', `No pude completar la consulta: ${error.message}`);
    statusLine.textContent = 'Error de conexión.';
  } finally {
    sendButton.disabled = false;
    recordButton.disabled = !voiceReady;
    messageInput.focus();
  }
}

async function speak(text) {
  try {
    const response = await fetch('/voice/synthesize', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    if (!response.ok) throw new Error('La voz local no está disponible');
    if (spokenAudioUrl) URL.revokeObjectURL(spokenAudioUrl);
    spokenAudioUrl = URL.createObjectURL(await response.blob());
    spokenAudio.src = spokenAudioUrl;
    spokenAudio.hidden = false;
    try { await spokenAudio.play(); }
    catch { statusLine.textContent = 'Respuesta lista: pulsa reproducir para escucharla.'; }
  } catch {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'es-BO';
      speechSynthesis.speak(utterance);
    }
  }
}

function encodeWav(chunks, sampleRate) {
  const length = chunks.reduce((total, chunk) => total + chunk.length, 0);
  const input = new Float32Array(length);
  let position = 0;
  for (const chunk of chunks) { input.set(chunk, position); position += chunk.length; }
  const outputLength = Math.floor(length * 16000 / sampleRate);
  const bytes = new ArrayBuffer(44 + outputLength * 2);
  const view = new DataView(bytes);
  const write = (offset, value) => { for (let i = 0; i < value.length; i++) view.setUint8(offset + i, value.charCodeAt(i)); };
  write(0, 'RIFF'); view.setUint32(4, 36 + outputLength * 2, true); write(8, 'WAVE');
  write(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
  view.setUint16(22, 1, true); view.setUint32(24, 16000, true);
  view.setUint32(28, 32000, true); view.setUint16(32, 2, true);
  view.setUint16(34, 16, true); write(36, 'data'); view.setUint32(40, outputLength * 2, true);
  for (let i = 0; i < outputLength; i++) {
    const sourceIndex = i * sampleRate / 16000;
    const low = Math.floor(sourceIndex);
    const value = input[low] + ((input[Math.min(low + 1, length - 1)] - input[low]) * (sourceIndex - low));
    view.setInt16(44 + i * 2, Math.max(-1, Math.min(1, value)) * 32767, true);
  }
  return bytes;
}

async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const context = new AudioContext();
  const source = context.createMediaStreamSource(stream);
  const processor = context.createScriptProcessor(4096, 1, 1);
  const chunks = [];
  processor.onaudioprocess = event => chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
  source.connect(processor);
  processor.connect(context.destination);
  const timer = setTimeout(() => { if (recording) stopRecording(); }, 12000);
  recording = { stream, context, source, processor, chunks, timer };
  recordButton.textContent = 'Detener y preguntar';
  recordButton.classList.add('active');
  recordHint.textContent = 'Escuchando… máximo 12 segundos';
}

async function stopRecording() {
  const current = recording;
  if (!current) return;
  recording = null;
  clearTimeout(current.timer);
  current.processor.disconnect();
  current.source.disconnect();
  current.stream.getTracks().forEach(track => track.stop());
  const sampleRate = current.context.sampleRate;
  await current.context.close();
  recordButton.textContent = 'Iniciar voz';
  recordButton.classList.remove('active');
  recordButton.disabled = true;
  recordHint.textContent = 'Transcribiendo localmente…';
  try {
    const audio = encodeWav(current.chunks, sampleRate);
    const result = await requestJson('/voice/transcribe', {
      method: 'POST', headers: { 'Content-Type': 'audio/wav' }, body: audio,
    });
    if (!result.text) throw new Error('No detecté palabras. Intenta de nuevo.');
    recordHint.textContent = '';
    await ask(result.text, true);
  } catch (error) {
    recordHint.textContent = error.message;
  } finally {
    recordButton.disabled = !voiceReady;
  }
}

form.addEventListener('submit', event => {
  event.preventDefault();
  const text = messageInput.value.trim();
  messageInput.value = '';
  ask(text);
});

recordButton.addEventListener('click', async () => {
  if (recording) { await stopRecording(); return; }
  try { await startRecording(); }
  catch (error) { recordHint.textContent = `Micrófono no disponible: ${error.message}`; }
});

Promise.all([requestJson('/voice/status'), requestJson('/health')]).then(([voice, health]) => {
  voiceReady = voice.transcription && !!navigator.mediaDevices?.getUserMedia;
  recordButton.disabled = !voiceReady;
  const textMode = health.openai_configured ? 'OpenAI configurado' : 'respuesta local de respaldo';
  statusLine.textContent = voiceReady
    ? `Chat y voz disponibles · ${textMode} · salida: ${voice.synthesis}`
    : `Chat disponible · ${textMode} · configura Whisper para activar el micrófono.`;
}).catch(() => { statusLine.textContent = 'Chat disponible · estado de voz desconocido.'; });
