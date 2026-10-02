# Paseito

Asistente inteligente del **Paseo Aranjuez** (Cochabamba, Bolivia), creado para la Hackathon By Paseo 2026.

Paseito es una cochabambina virtual que conversa por voz o texto con los visitantes: les dice dónde
encontrar tiendas, comida, servicios, eventos y promociones, si un local está abierto ahora y cómo llegar.
Todo lo que responde sale de la base de datos del Paseo; el modelo no inventa lugares ni precios.

## Qué incluye

- **Agente conversacional** con Google Gemini y function calling sobre los datos reales del Paseo
  (70 tiendas importadas del sitio oficial, espacios, eventos y preguntas frecuentes).
- **Voz boliviana** (`es-BO-SofiaNeural`) para leer las respuestas en ~1,5 s.
- **Avatar 3D** (Three.js) con sombrero blanco cochabambino, trenzas, manta de aguayo y pollera, frente al
  Tunari y el Cristo de la Concordia; la boca sigue el audio real. Respaldo 2D en SVG si no hay WebGL.
- **Kiosco** con micrófono, subtítulos sincronizados y tarjetas de los lugares encontrados.
- **Analítica** de lo más buscado y de la demanda no cubierta (lo que la gente pide y el Paseo no tiene).

## Cómo correrlo

El proyecto está separado en dos partes:

- `backend/`: API en FastAPI + Gemini + SQLite (Python 3.11 o superior).
- `frontend/`: kiosco en HTML/JS puro con Three.js incluido; no necesita build ni `npm install`.

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # en Windows: copy .env.example .env
# editar .env y poner GEMINI_API_KEY (https://aistudio.google.com/apikey)
uvicorn app.main:app --port 8000
```

La base SQLite (`backend/paseo.db`) se crea y se llena sola en el primer arranque.
La documentación interactiva de la API queda en http://localhost:8000/docs.

### Frontend

La forma más simple: el backend sirve la carpeta `frontend/` en la raíz, así que con el backend corriendo
basta abrir **http://localhost:8000** (kiosco) o http://localhost:8000/prueba-voz.html.

Para trabajarlo por separado, con cualquier servidor estático:

```bash
cd frontend
python -m http.server 5500
```

y abrir http://localhost:5500. El frontend busca la API en el puerto 8000 del mismo host; para otro servidor
se cambia `frontend/config.js` o se abre la página con `?api=https://mi-backend.com`.

El micrófono solo funciona en `localhost` o con HTTPS. En Chrome y Edge se usa el reconocimiento del
navegador; en los demás, el audio se transcribe con Gemini en `POST /voz/escuchar`.

## API principal

| Método y ruta | Uso |
|---|---|
| `POST /chat` | `{"mensaje": "...", "session_id": "opcional"}` → respuesta, tarjetas, herramientas usadas |
| `DELETE /chat/{session_id}` | Olvida la conversación (nuevo visitante) |
| `POST /voz` | `{"texto": "..."}` → MP3 con la voz de Paseito |
| `POST /voz/escuchar` | Audio en el cuerpo (`Content-Type: audio/wav`, `audio/mp3`…) → `{"texto": "..."}` |
| `GET /lugares`, `/productos`, `/promociones`, `/eventos`, `/faqs` | Catálogo |
| `GET /analitica/resumen` | Consultas, términos más buscados y demanda no cubierta |
| `/admin/...` | Altas, bajas y cambios (header `X-Admin-Token` si `ADMIN_TOKEN` está definido) |

Para usar el avatar en otro frontend:

```js
import { Avatar } from "http://localhost:8000/js/avatar.js";
const avatar = new Avatar(document.getElementById("avatar"));
avatar.desbloquear();                 // dentro de un clic del usuario
await avatar.hablarAudio(urlDelMp3);  // reproduce y mueve la boca
```

## Estructura

```
backend/                 API (FastAPI)
  app/
    main.py          app, CORS y montaje opcional del frontend
    agente.py        agente Gemini con herramientas y memoria por sesión
    herramientas.py  búsquedas sobre la base del Paseo
    voz.py           texto a voz (edge-tts o Gemini TTS) y transcripción con Gemini
    rutas/           endpoints de chat, catálogo, admin, analítica y voz
    datos/           lugares.json generado por el importador
  scripts/
    importar_paseo.py  regenera lugares.json desde paseoaranjuez.com
frontend/                kiosco (HTML/JS sin build)
  index.html         pantalla del kiosco con Paseito en 3D
  prueba-voz.html    página simple para probar chat y voz
  config.js          URL del backend
  js/
    avatar3d.js      Paseito en Three.js con la escena de Cochabamba
    avatar.js        avatar 2D en SVG (respaldo sin WebGL)
  vendor/three/      Three.js 0.186.1
```

## Configuración

Todas las opciones están documentadas en `backend/.env.example`: modelo principal y de respaldo de
Gemini, motor y voz de TTS, orígenes CORS y token de administración. El archivo `.env` nunca se sube al repositorio.
