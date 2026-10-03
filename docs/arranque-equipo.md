# Arranque del equipo: Jarvis con el avatar reciente de Paseito

La aplicación principal vive en `apps/jarvis-backend/`. Incluye el avatar actualizado, conversación, catálogo, horarios/promociones de demo y respaldo WhatsApp. No requiere clave Gemini ni OpenAI.

## Descargar

```powershell
git clone --branch feat/avatar-jarvis-auditoria-reto https://github.com/daer-1701/Paseito.git
cd Paseito
```

Cuando esta rama sea mergeada, también estará disponible en `main`. Para un clon existente, guardar primero el trabajo propio antes de cambiar de rama; no usar reset forzado.

## Opción A: cualquier PC con Docker, sin GPU

Desde PowerShell en la raíz, con Docker Desktop abierto y contenedores Linux:

```powershell
$env:JARVIS_INGEST_TOKEN=[guid]::NewGuid().ToString("N")
$env:JARVIS_DEMO_CATALOG="1"
docker compose -f compose.portable.yaml up -d --build
```

El token es local al proceso; para conservarlo entre terminales, guardarlo en `.env` ignorado por Git. Si ya hay uno configurado, reutilizarlo. El perfil portable comparte el volumen `jarvis-data` con el perfil GPU y usa el mismo puerto: escoger un perfil por equipo. No iniciar ambas aplicaciones a la vez en el mismo puerto.

Abrir `http://localhost:8000` y `http://localhost:8000/whatsapp/demo`. Incluye texto, avatar, catálogo y horarios/promociones. No instala Whisper/Kokoro ni garantiza voz del sistema: el navegador puede leer la respuesta y reconocer voz si dispone de esos servicios. Siempre hay entrada por texto.

```powershell
docker compose -f compose.portable.yaml logs --tail 50 jarvis
docker compose -f compose.portable.yaml stop
```

No usar `down -v` para una parada normal: elimina los datos persistidos. No publicar el puerto completo para dar acceso móvil; ver `acceso-movil.md`.

## Opción B: Windows sin Docker, Python 3.11

Desde la raíz, PowerShell:

```powershell
cd apps/jarvis-backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:JARVIS_DEMO_CATALOG="1"
$env:JARVIS_RESPONSE_MODE="strict"
$env:JARVIS_INGEST_TOKEN=[guid]::NewGuid().ToString("N")
.\.venv\Scripts\python.exe -m jarvis.bootstrap
```

El bootstrap carga los datos incluidos. No ejecutar únicamente `jarvis.api` en una base nueva: ese comando no carga todo el catálogo. `tzdata` está declarado para soportar la zona horaria de Bolivia en Windows. En este modo las variables se configuran en la terminal; el backend Jarvis no carga automáticamente el `.env` raíz. Ctrl+C detiene el servidor.

## Opción C: voz local GPU

Windows + NVIDIA + WSL2/Ubuntu + Docker Desktop: seguir `arranque-torre-windows.md`.
Configurar `JARVIS_DEMO_CATALOG=1` en el `.env` local para mostrar el catálogo completo y WhatsApp local. Después:

```bash
bash scripts/start-tower.sh
```

Este perfil requiere NVIDIA; el script verifica CUDA y descarga los modelos la primera vez. La integración del avatar no necesita ejecutar `backend/` ni configurar Gemini.

## Qué probar manualmente

1. «Busco una camisa» → elegir una tienda → catálogo → «Más opciones».
2. «Horario de Amore» → «¿Y el domingo?».
3. «¿Dónde queda Amore?» → ubicación, sin recorrido ficticio.
4. «Promoción de Almacén de Pizzas» → familiar de ocho porciones Bs 59 hasta el 11 de octubre de 2026.
5. Abrir respaldo local de WhatsApp; no envía mensajes reales.
6. Reiniciar sesión y comprobar que la elección anterior desaparece.

El perfil portable está preparado en código; queda pendiente certificarlo desde un clon limpio en el PC de un compañero. El perfil GPU se reconstruyó y arrancó en la torre local.

## Implementación alternativa

`frontend/` y `backend/` conservan la aplicación original de Paseito con Gemini. Su guía está en `paseito-original.md`. Para ejecutarla simultáneamente, usar `uvicorn app.main:app --port 8002` y abrir `http://localhost:8002/?api=http://localhost:8002`; el parámetro evita que su configuración actual envíe solicitudes al puerto 8000 de Jarvis.

No usar esa aplicación para evaluar los cambios de catálogo/WhatsApp de Jarvis. Ambos contratos de chat son distintos.
