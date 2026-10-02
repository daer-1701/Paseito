# Jarvis Paseo · backend MVP

Agente conversacional para Paseo Aranjuez. La búsqueda de negocios, eventos y
promociones sale de un catálogo actualizable; OpenAI sintetiza la respuesta si
se configura una clave. Si no hay conexión o saldo, el servidor sigue respondiendo con evidencia
mediante un generador local, útil para probar toda la integración.

## Inicio rápido

```bash
cd apps/jarvis-backend
python3 -m jarvis.seed
export JARVIS_INGEST_TOKEN="secreto-local-para-la-demo"
python3 -m jarvis.api
```

Abrir `http://localhost:8000` para usar la página funcional de chat. El backend
de texto solo usa la biblioteca estándar de Python 3.9 o superior. `JARVIS_DB`
permite cambiar la ruta de SQLite. La semilla
incluida está marcada como **datos de demostración**; reemplácenla por datos
confirmados antes de presentarlos como información real.
La página integrada comparte origen con la API. Si otro frontend consume el
backend desde un dominio distinto, establecer `JARVIS_CORS_ORIGIN` con ese
origen exacto; no se habilita CORS abierto por defecto.

## Voz local

La página ofrece grabación de hasta 12 segundos con botón. Envía WAV mono de
16 kHz a `POST /voice/transcribe`, consulta `/chat` y pide el audio de respuesta
a `POST /voice/synthesize`. `GET /voice/status` indica qué adaptadores están
disponibles. El micrófono del navegador requiere `localhost` o HTTPS.

En este Mac ya están instalados `whisper-cli`, el modelo multilingüe `base` y
una voz Piper `es_MX-ald-medium`. Los modelos están en `models/` (ignorado por
Git); para arrancar todo, usa el entorno virtual local:

```bash
cd apps/jarvis-backend
.venv/bin/python -m jarvis.seed
.venv/bin/python -m jarvis.api
```

En otra máquina, instalar `whisper-cli`, crear un entorno virtual, instalar
Piper y descargar los modelos. En macOS con Homebrew:

```bash
brew install whisper-cpp
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-voice.txt
mkdir -p models
curl --fail --location -o models/ggml-base.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin
.venv/bin/python -m piper.download_voices --download-dir models es_MX-ald-medium
```

Si los modelos viven en otra ruta, configurar `JARVIS_WHISPER_MODEL` y
`JARVIS_PIPER_MODEL`. Se puede cambiar `JARVIS_WHISPER_BIN`. El reconocimiento
usa CPU por defecto para mayor compatibilidad; `JARVIS_WHISPER_GPU=1` habilita
la GPU si el equipo la soporta. En macOS, si falta Piper, se usa la voz del
sistema; en otros equipos el navegador puede leer la respuesta. El chat de
texto sigue disponible aunque falte la voz.

## API

### `POST /chat`

```json
{"message":"Quiero comprar un regalo y tomar un café", "session_id":"demo-1"}
```

Devuelve `answer`, `sources`, `intent`, `suggestions` y `session_id`. Enviar el
mismo `session_id` conserva los últimos turnos para preguntas de seguimiento.
El servidor
solo entrega al modelo registros encontrados en la base; si no hay evidencia,
responde que no puede confirmarlo. El cliente puede mostrar las fuentes.

### `POST /admin/records`

Requiere `Authorization: Bearer <JARVIS_INGEST_TOKEN>`. Inserta o actualiza por
`id`. Una actualización aparece en la próxima consulta sin reconstruir todo el
índice. Tipos: `venue`, `product`, `promotion`, `event`, `faq`.

```json
{
  "id":"venue:cafe-ejemplo",
  "kind":"venue",
  "title":"Café Ejemplo",
  "text":"Cafetería con bebidas calientes y pastelería.",
  "attributes":{"floor":"2", "unit":"201", "category":"cafetería"},
  "source_url":"https://ejemplo.com/cafe",
  "updated_at":"2026-10-02T12:00:00-04:00",
  "expires_at":null
}
```

`DELETE /admin/records/{id}` retira información obsoleta. `GET /health`
verifica el servicio. Sin `JARVIS_INGEST_TOKEN`, los endpoints de administración
devuelven 401. Las promociones deben incluir `expires_at`.

### `POST /stimulus/gaze` (integración opcional)

El frontend del eye tracker envía **un evento de mirada sostenida sobre una
ficha**, no video ni coordenadas. El `target_id` es el `id` de un registro
público ya mostrado al visitante. El backend exige al menos 900 ms de mirada y
aplica 12 segundos de espera por objetivo y sesión para evitar respuestas
repetidas y gasto accidental.

```json
{"session_id":"demo-1", "target_id":"venue:demo-cafe", "dwell_ms":1000}
```

La respuesta tiene `triggered: false` y un motivo, o `triggered: true` y el
objeto `chat` de Jarvis. El dispositivo y la UI de mirada todavía deben
conectarse; este endpoint permite integrarlos sin cambiar el agente.

## Integración con el equipo

- **PaseoYa**: enviará `venue`, `product` y `promotion` al endpoint de ingesta
  cuando se publiquen o modifiquen. Incluir `expires_at` en promociones; no
  exponer inventario no confirmado. El adaptador de lectura en vivo de stock
  se añade cuando el equipo cierre su contrato de API.
- **Paseo Points**: consultar saldo y canjes mediante una API autenticada en
  tiempo real. Los saldos personales nunca se indexan en el RAG compartido.
- **Frontend/voz**: ambos consumen `/chat`. El frontend puede convertir voz a
  texto y leer `answer` con TTS; la página integrada muestra este recorrido.

## Proveedor de LLM

Configurar `OPENAI_API_KEY` **solo en el servidor**. Por defecto se usa
`gpt-6-luna` con la API Responses; `OPENAI_TEXT_MODEL` permite cambiarlo por
otro modelo que admita `reasoning.effort=none`. El backend selecciona las
fuentes antes de llamar al modelo y limita la salida a 350 tokens. Si la clave
falta o la llamada falla, usa el generador local. No guardar claves en Git ni
en el navegador.

```bash
export OPENAI_API_KEY="tu-clave-local"
python3 -m jarvis.api
```

La voz local funciona por turnos: pulsar, hablar, detener y escuchar. Esto
permite una demo confiable antes de implementar conversación simultánea.

## Límites deliberados del MVP

- No compra, reserva ni canjea: esas acciones requerirán autenticación y
  confirmación explícita.
- No presenta como reales los registros de demostración.
- No inventa precios, disponibilidad ni horarios cuando faltan en las fuentes.
