# Arranque del equipo: versión única de Paseito

## 1. Clonar la rama

```powershell
git clone --branch feat/version-unica-openai https://github.com/daer-1701/Paseito.git
cd Paseito
Copy-Item .env.example .env
```

Si ya existe `.env`, conservarlo. La aplicación lee solamente el `.env` de la raíz;
variables del proceso tienen prioridad. Tras cambiarlo, recrear el contenedor.

## 2. Preparar token y modo de presentación (PowerShell)

No imprimir el token ni enviarlo por chat. Este bloque funciona en Windows PowerShell:

```powershell
$taskRng = [Security.Cryptography.RandomNumberGenerator]::Create()
$taskBytes = New-Object byte[] 32
$taskRng.GetBytes($taskBytes)
$taskToken = [BitConverter]::ToString($taskBytes).Replace('-', '').ToLowerInvariant()
$taskEnv = Get-Content .env
$taskEnv = $taskEnv -replace '^JARVIS_INGEST_TOKEN=.*', ('JARVIS_INGEST_TOKEN=' + $taskToken)
$taskEnv = $taskEnv -replace '^JARVIS_DEMO_CATALOG=.*', 'JARVIS_DEMO_CATALOG=1'
$taskEnv | Set-Content .env -Encoding UTF8
$taskRng.Dispose()
```

Completar localmente `OPENAI_API_KEY` para usar OpenAI. El modelo es configurable;
por defecto `gpt-4.1-mini`. No se usa Gemini ni una capa gratuita como dependencia.
Si la clave falta, el respaldo local permite presentar catálogo, horarios y eventos.

## 3. Sin NVIDIA: Docker portable

Abrir Docker Desktop en modo Linux:

```powershell
docker compose -f compose.portable.yaml up -d --build
docker compose -f compose.portable.yaml ps
```

Abrir http://localhost:8000. El navegador proporciona voz y, si lo soporta,
reconocimiento de voz. Disponibilidad y permiso del micrófono dependen del navegador;
texto siempre es el respaldo. Para voz boliviana Edge opcional, poner
`JARVIS_TTS_PROVIDER=edge`; requiere Internet. No activar este proveedor en la torre.

## 4. Torre con NVIDIA

Seguir [Windows + WSL2 + RTX](arranque-torre-windows.md):

```bash
bash scripts/start-tower.sh
```

La aplicación y los datos son los mismos. Solo cambia el adaptador de voz.
Conservar los volúmenes: no utilizar `docker compose down -v`.

## 5. Sin Docker: Python 3.11 o superior

Desde la raíz:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r apps/jarvis-backend/requirements.txt
.\.venv\Scripts\python.exe scripts/serve.py
```

El SQLite local se crea en `apps/jarvis-backend/jarvis.sqlite3`; en Docker se usa
`/data/jarvis.sqlite3`. No ejecutar otra aplicación ni crear otra base en `backend/`.
También funciona `uvicorn app.main:app --app-dir backend --port 8000`.

## 6. Recorrido de presentación

1. Bienvenida y avatar; buscar camisas con presupuesto y elegir una tienda.
2. Ver catálogo, promociones, horario del domingo y ubicación/ficha móvil.
3. Pedir camisa, café y una reunión: las tres necesidades aparecen en la respuesta.
4. Preguntar por recompensas Points. Sin conexión externa, el modo demo devuelve
   programa público y tarjetas; pedir saldo remite a iniciar sesión en Points.
5. `/whatsapp/demo`: buscar, elegir tienda y reenviar el último mensaje para mostrar deduplicación.
6. Volver a bienvenida y pulsar «Demo: activar saludo por mirada». Solo saluda;
   no identifica personas ni mide mirada real. El adaptador físico está pendiente.
7. `/admin.html`: introducir el token local de `.env`; ver analítica de web y WhatsApp,
   revisar calidad y editar registros con fuente/fecha/procedencia.

## 7. Integraciones externas

- Twilio: `JARVIS_WHATSAPP_PROVIDER=twilio`, `TWILIO_AUTH_TOKEN`,
  `JARVIS_WHATSAPP_WEBHOOK_URL=https://.../whatsapp/webhook` y secreto de sesión.
  El gateway `compose.whatsapp.yaml` publica solamente el webhook; falta validar entrega real.
- Points: URL MySQL con cuenta de solo lectura y certificado CA. TLS verifica
  certificado y host. En Docker, poner `PUNTOS_CA_HOST_PATH` con la ruta absoluta del certificado
  público en el host y usar el override `compose.points.yaml`:
  `docker compose -f compose.yaml -f compose.points.yaml up -d jarvis`.
  Para portable, reemplazar el primer archivo por `compose.portable.yaml`.
  El certificado se monta solo lectura en `/run/points-ca.pem`. Nunca copiar una clave privada.
  La caché normal dura 300 s y se descarta a los 600 s; se filtran las vigencias.
  Si falla y el modo demo está activo, se usa el programa público de demostración.
- Fichas móviles: `JARVIS_MOBILE_BASE_URL` debe ser accesible desde el teléfono.
  El gateway `compose.mobile.yaml` publica solamente fichas y QR, no chat ni administración.
- Mirada real: `JARVIS_STIMULUS_ENABLED=1` únicamente después de integrar el dispositivo.
  POST `/stimulus/gaze`: `session_id`, `target_id: gaze_at_kiosk`, `dwell_ms`,
  `welcome: true`, `busy: false`, `manual: false`. Un saludo por sesión y cooldown;
  el productor debe observar el estado de la interfaz y no enviar imágenes ni coordenadas.

## Estado fiable

`/health`, `/voice/status`, `/whatsapp/status` y `/points/programa` muestran capacidades
reales. Una demo pública no prueba conexión a Points o entrega a un teléfono.
Para el detalle completo, [estado de la versión](version-unica-estado.md).

## Aportes del compañero: primera etapa

La rama `feat/aportes-companero-etapa1` conserva la aplicación unificada e incorpora avatar cochabambino, imágenes, 120 productos y lector QR. Ver [registro de etapa 1](etapa1-aportes-companero.md).

En el kiosco, el botón de cámara **Lee mi QR** abre el lector. La cámara se solicita solo al pulsar **Abrir cámara**; necesita localhost o HTTPS y permiso del navegador. También se puede escribir un código. **Ver ejemplo local** funciona cuando `JARVIS_DEMO_CATALOG=1` y no permite canjear.

Para cupones reales se usa la conexión MySQL de Points ya configurada con CA. El QR de cliente se valida mediante `PUNTOS_API_URL` y `PUNTOS_API_KEY` (ruta `/api/integrations/customer-qr/verify`), o mediante `PUNTOS_QR_SECRET` dedicado como alternativa. Poner secretos únicamente en el entorno local. Las variables se propagan en Compose GPU y portable. `GET /cupones/status` informa capacidades sin revelar secretos.

`POST /cupones/verificar` recibe `codigo` y `session_id`. No canjea, no consulta saldo por teléfono/correo y no envía QR al modelo. Con un código se muestra únicamente ese cupón; con QR de cliente validado se muestran hasta 20 cupones propios. El saldo y las políticas adicionales quedan para la segunda etapa.
