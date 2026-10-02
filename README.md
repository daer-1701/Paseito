# Paseito

Asistente inteligente del **Paseo Aranjuez** (Cochabamba, Bolivia), creado para la Hackathon By Paseo 2026.

Paseito es una cochabambina virtual que conversa por voz o texto con los visitantes: les dice dónde
encontrar tiendas, comida, servicios, eventos y promociones, si un local está abierto ahora y cómo llegar.
Todo lo que responde sale de la base de datos del Paseo; el modelo no inventa lugares ni precios.

## Qué incluye

- **Agente conversacional** con Google Gemini y function calling sobre los datos reales del Paseo
  (70 tiendas importadas del sitio oficial, espacios, eventos y preguntas frecuentes).
- **Voz boliviana** (`es-BO-SofiaNeural`) para leer las respuestas en ~1,5 s.
- **Avatar animado** en SVG con sombrero blanco cochabambino, trenzas y aguayo; la boca sigue el audio real.
- **Kiosco** con micrófono, subtítulos y tarjetas de los lugares encontrados.
- **Analítica** de lo más buscado y de la demanda no cubierta (lo que la gente pide y el Paseo no tiene).

## Cómo correrlo

Requiere Python 3.11 o superior.

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # en Windows: copy .env.example .env
# editar .env y poner GEMINI_API_KEY (https://aistudio.google.com/apikey)
uvicorn app.main:app --port 8000
```

La base SQLite (`backend/paseo.db`) se crea y se llena sola en el primer arranque.

| URL | Qué es |
|---|---|
| http://localhost:8000/kiosco | Pantalla del kiosco con Paseito (usar Chrome o Edge para el micrófono) |
| http://localhost:8000/prueba-voz | Página simple para probar chat y voz |
| http://localhost:8000/docs | Documentación interactiva de la API |

El micrófono del navegador solo funciona en `localhost` o con HTTPS.

## API principal

| Método y ruta | Uso |
|---|---|
| `POST /chat` | `{"mensaje": "...", "session_id": "opcional"}` → respuesta, tarjetas, herramientas usadas |
| `DELETE /chat/{session_id}` | Olvida la conversación (nuevo visitante) |
| `POST /voz` | `{"texto": "..."}` → MP3 con la voz de Paseito |
| `GET /lugares`, `/productos`, `/promociones`, `/eventos`, `/faqs` | Catálogo |
| `GET /analitica/resumen` | Consultas, términos más buscados y demanda no cubierta |
| `/admin/...` | Altas, bajas y cambios (header `X-Admin-Token` si `ADMIN_TOKEN` está definido) |

Para usar el avatar en otro frontend:

```js
import { Avatar } from "http://localhost:8000/static/avatar.js";
const avatar = new Avatar(document.getElementById("avatar"));
avatar.desbloquear();                 // dentro de un clic del usuario
await avatar.hablarAudio(urlDelMp3);  // reproduce y mueve la boca
```

## Estructura

```
backend/
  app/
    agente.py        agente Gemini con herramientas y memoria por sesión
    herramientas.py  búsquedas sobre la base del Paseo
    voz.py           texto a voz (edge-tts o Gemini TTS)
    rutas/           endpoints de chat, catálogo, admin, analítica y voz
    static/          avatar.js, kiosco.html y prueba-voz.html
    datos/           lugares.json generado por el importador
  scripts/
    importar_paseo.py  regenera lugares.json desde paseoaranjuez.com
```

## Configuración

Todas las opciones están documentadas en `backend/.env.example`: modelo principal y de respaldo de
Gemini, motor y voz de TTS, orígenes CORS y token de administración. El archivo `.env` nunca se sube al repositorio.
