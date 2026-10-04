# Presentación por HTTPS: torre y Cloudflare

URL: https://jarvis.timosboy.win

La interfaz, el agente y SQLite permanecen en la torre. Whisper y Kokoro usan la
GPU local con los modelos precargados. El kiosco usa http://localhost:8000 y no
depende del túnel. Los visitantes acceden por HTTPS a Cloudflare, que conecta con
un proxy local en 127.0.0.1:8082. La ruta de n8n no se modifica.

## Iniciar en esta torre

Docker Desktop debe estar abierto. Desde la raíz del repositorio:

```powershell
docker compose -f compose.yaml -f compose.presentation.yaml up -d --build
.\scripts\start-presentation.ps1
```

La primera descarga de modelos puede tardar; esperar a que voice y jarvis estén
healthy. Si los servicios ya están activos, el comando conserva los volúmenes.
El script comprueba el proxy, valida la configuración y lanza cloudflared en
segundo plano. Volver a ejecutarlo no crea otra copia del proceso registrado.

El túnel dedicado es `paseito-presentacion`, ID
`dd97dbcb-3c29-4306-a748-d51f23f68679`. Sus credenciales permanecen fuera de Git, en
la carpeta .cloudflared del perfil de Windows. Configuración temporal, PID y logs
se guardan en tmp/presentation, ignorado por Git. No copiar credenciales a otro
equipo ni publicarlas. El dominio público se configuró en el .env local como
JARVIS_MOBILE_BASE_URL=https://jarvis.timosboy.win para las fichas por QR.

El túnel requiere iniciar el script nuevamente después de reiniciar Windows;
no se instaló un servicio global que pueda afectar n8n. Docker tiene políticas
de reinicio para sus servicios, pero debe estar ejecutándose.

## Detener solamente el acceso público

```powershell
.\scripts\stop-presentation.ps1
```

El script solo detiene el PID registrado si nombre y fecha de inicio coinciden.
Jarvis, SQLite y la voz siguen disponibles en localhost. Nunca usar down -v para
reiniciar una presentación: elimina volúmenes.

## Otra computadora

Puede usar localhost con las instrucciones de arranque del equipo. Para publicar
por un túnel propio necesita autenticación en Cloudflare y credenciales de su
túnel, y puede pasar -TunnelId al script. El hostname de esta entrega pertenece
a la torre; no iniciar otra instancia contra él sin coordinar el cambio de origen.
El proxy fija la redirección HTTPS a jarvis.timosboy.win; adaptar ese hostname si
se prepara un dominio diferente.

## Transporte y acceso

- La voz interna conserva NDJSON. El navegador solicita text/event-stream, el
  endpoint exterior convierte cada JSON completo en un evento SSE real y el
  lector acepta SSE o NDJSON. Cancelar la reproducción cierra la lectura.
- El proxy desactiva buffering/caché de API, limita frecuencia y conexiones,
  acepta hasta 1 MB de cuerpo y marca la cookie de Points Secure para HTTPS.
- HTTP público se redirige a HTTPS. El kiosco HTTP local conserva su comportamiento.
- Administración, analítica, eventos del eye tracker y documentación de API no
  se publican. Catálogo, conversación, voz, destinos, QR, Points y WhatsApp local
  pasan por una lista de rutas explícita.
- La capacidad actual de GPU admite una tarea de voz a la vez. La publicación
  no añade GPUs ni convierte la demo en un servicio de voces concurrentes.

## Evidencia de despliegue

Comprobaciones del 3 de octubre de 2026, hora de Bolivia:

- 42 pruebas de backend y 6 de frontend correctas.
- Nginx acepta su configuración; conexión de cloudflared con cuatro conexiones
  al borde de Cloudflare.
- HTTPS con certificado validado: interfaz, health y avatar HTTP 200;
  administración, analítica, OpenAPI y estímulos HTTP 404.
- Voz pública SSE: dos fragmentos PCM, primer audio 516 ms y total 594 ms en una
  solicitud con GPU caliente. Esta muestra no representa una media ni un SLA.
- Cookie de sesión Points marcada Secure; se cerró la sesión de ejemplo al acabar.

En el momento de las primeras comprobaciones, 1.1.1.1 resolvía el dominio pero
el resolutor de la red de la torre aún devolvía NXDOMAIN. La comprobación HTTPS
usó la IP publicada por 1.1.1.1 conservando el hostname y la verificación TLS.
No se modificó el DNS global de Windows ni se desactivó la validación del
certificado. Después de expirar la respuesta negativa, el DNS de Windows,
Google y Quad9 resolvieron correctamente. El navegador abrió el dominio,
renderizó el avatar y respondió a «¿Dónde puedo comer?» con tres locales y
sus fuentes. Evidencia: entregables/despliegue-publico.png. El usuario confirmó
que ya cargaba en su celular; la escucha y el micrófono de ese celular todavía
requieren confirmación durante el ensayo.

Las reglas existentes de Cloudflare rechazaron el agente HTTP de Python; el
cliente con agente navegador funcionó. No se desactivaron esas protecciones.

## Respaldo durante la presentación

Si falla Internet o el túnel, usar http://localhost:8000 en el kiosco. La voz GPU
permanece local; OpenAI sigue necesitando Internet y el agente tiene respaldo
local. Para ensayar WhatsApp usar /whatsapp/demo (modo de ejemplos habilitado).
Points real, WhatsApp real, permisos del micrófono y hardware del eye tracker
mantienen los pendientes documentados; publicar esta URL no los conecta.
