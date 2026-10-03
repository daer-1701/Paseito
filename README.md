# Paseito · Asistente del Paseo Aranjuez

Una aplicación web responsive para el reto Jarvis: avatar, voz, catálogo, horarios,
promociones, eventos, WhatsApp y analítica consultan el mismo servicio.

## Arranque

[Guía única para el equipo](docs/arranque-equipo.md) ·
[Windows, WSL y NVIDIA](docs/arranque-torre-windows.md) ·
[Estado y pendientes](docs/version-unica-estado.md)

```bash
git clone --branch feat/version-unica-openai https://github.com/daer-1701/Paseito.git
cd Paseito
# Preparar .env siguiendo la guía; requiere un token administrativo local.
docker compose -f compose.portable.yaml up -d --build
```

Abrir http://localhost:8000. La versión portable usa texto y voz del navegador;
la torre usa Whisper y Kokoro en GPU mediante `docker compose up -d --build`.
Sin Docker: instalar `apps/jarvis-backend/requirements.txt` y ejecutar
`python scripts/serve.py` desde la raíz. Se carga únicamente el `.env` raíz.

## Una sola arquitectura

| Parte | Implementación |
|---|---|
| Servidor | `backend/app/main.py`, FastAPI |
| Datos y sesiones | SQLite versionado en `jarvis.store` |
| Agente común | `jarvis.orchestrator`, OpenAI Responses con herramientas y respaldo local |
| Interfaz | `frontend/`, responsive con el último avatar del compañero |
| Voz de torre | `services/voice/`, Whisper y Kokoro con streaming y cancelación |
| WhatsApp | Twilio firmado e idempotente; demo local del mismo agente |
| Analítica y administración | `/admin.html`, API con credencial obligatoria |
| Points | Programa público, MySQL de solo lectura con TLS y caché limitada; demo pública de respaldo |
| Mirada | Evento `gaze_at_kiosk` para saludar en bienvenida, con demo manual |

El backend Gemini, su SQLite independiente, el servidor HTTP anterior y las
copias del kiosco se retiraron. Los historiales de ambos equipos se conservan
con Git. `python -m jarvis.bootstrap` redirige al mismo FastAPI por compatibilidad.

## Configuración y límites

- OpenAI: `OPENAI_API_KEY`, `OPENAI_TEXT_MODEL` (por defecto `gpt-4.1-mini`).
  La clave queda en el servidor; si falta o falla, responde el respaldo local.
- `JARVIS_DEMO_CATALOG=1` activa precios, promociones, horarios faltantes y
  programa público Points de demostración. El modo aparece en la interfaz,
  sin repetir advertencias en cada respuesta. `0` excluye esos datos.
- WhatsApp real requiere Twilio y HTTPS. La demo está en `/whatsapp/demo`.
- No se consultan saldos personales, ni se realizan compras, reservas o canjes.
  Inventario real, PaseoYa, identidad Points, navegación paso a paso y hardware
  eye tracker siguen sujetos a sus integraciones externas.
- Nunca subir `.env`, claves, bases locales o certificados privados al repositorio.

[Definición acordada](docs/definicion-version-unica.md) ·
[Conflictos de datos conservados para revisión](docs/conflictos-catalogo.json) ·
[Auditoría del enunciado](docs/auditoria-reto-jarvis.md)
