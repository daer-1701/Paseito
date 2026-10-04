# Presentación: despliegue y revisión de integraciones

Estado del despliegue: propuesta para revisar; sin cambios de DNS ni publicación. Consulta realizada el 3 de octubre de 2026, hora de Bolivia.

Actualización posterior: el usuario aprobó como definitivos los PR de UX/UI. Se activaron en `main` los modelos, suelo, árboles, iluminación horaria, desenfoque y cambios de cabecera. Se alojaron localmente las dependencias de posprocesado y se reactivó la resolución adaptativa, preservando los controles de la aplicación unificada. La revisión siguiente documenta los hallazgos previos a esa activación.

## Objetivo

Mostrar la versión unificada desde móviles mediante HTTPS y mantener la voz con GPU en la torre. El kiosco debe seguir funcionando por localhost si falla Internet. La ruta existente de n8n se conserva.

## Despliegue propuesto

- Dominio: `jarvis.timosboy.win`.
- Flujo público: navegador → Cloudflare Tunnel → proxy local → FastAPI → voz GPU. SQLite y modelos permanecen en sus volúmenes actuales.
- Flujo del kiosco: navegador local → FastAPI → voz GPU, sin pasar por Cloudflare.
- Un túnel dedicado para Jarvis y su configuración separada, evitando cambiar el origen Docker `http://n8n:5678` del túnel existente `n8n-local`.
- Publicar solamente interfaz, catálogo, conversación, voz, destinos, QR, sesión Points y demo WhatsApp. Administración, analítica, documentación de API y estímulos quedan fuera del acceso público.
- El proxy debe limitar cuerpos de audio y frecuencia de solicitudes, desactivar buffering de voz y caché de respuestas privadas. Una sola instancia de FastAPI conserva las sesiones personales actuales.
- Mantener las cookies personales seguras en HTTPS sin impedir las sesiones del kiosco en localhost. Usar encabezados del proxy solamente desde el proxy de confianza.
- El servicio de voz conserva sus modelos precargados y rechazo de concurrencia. La presentación usa una conversación de voz a la vez; no se promete atender voces simultáneas.

Cloudflared está instalado y sus credenciales permiten listar túneles. El túnel existente no registraba conexiones activas al consultar. El hostname propuesto todavía no se creó ni se verificó como libre.

### Transporte de voz

Actualmente `/voice/stream` devuelve NDJSON y el navegador interpreta líneas JSON. Cloudflare documenta buffering por defecto salvo `text/event-stream`.

Implementar negociación SSE en el endpoint exterior y soporte SSE en el lector del navegador. Cada mensaje debe ser un evento real `data: <JSON>` seguido por una línea vacía; no basta cambiar Content-Type. Conservar NDJSON dentro del servicio GPU y para clientes actuales que lo soliciten. Así se evita reconstruir el sistema de voz.

Fuente: https://developers.cloudflare.com/tunnel/troubleshooting/#cloudflare-tunnel-is-buffering-my-streaming-response-instead-of-streaming-it-live

### Por qué Cloudflare ahora

La torre ya tiene el runtime CUDA y los modelos residentes. Publicar esta misma aplicación reduce cambios y mantiene el origen de las mediciones de latencia. Vercel podría alojar la interfaz, pero la torre seguiría siendo necesaria para esta arquitectura de voz y aparecería otra conexión entre frontend y backend. La latencia pública incluye red y no será idéntica a localhost.

### Secuencia de implementación

1. Rama de despliegue basada en la versión unificada, sin fusionar todo main.
2. Transporte SSE exterior, manteniendo el protocolo interno.
3. Proxy público y configuración separada de cloudflared; conservar administración local.
4. Comprobar disponibilidad del hostname y crear su ruta DNS, iniciar el conector dedicado.
5. Revisar desde HTTPS conversación, voz por fragmentos, cámara, QR, caducidad y rechazo público de administración. La comprobación pública requiere acceso al despliegue real; todavía no se realizó.
6. Mantener acceso local y demo WhatsApp como respaldo. Dejar instrucciones de inicio y apagado del túnel.

## Points: contrato revisado

Repositorio: https://github.com/whoJP/Sistema_Fidelizacion_MiPaseito

Commit consultado: `f01b455a8f2159869d38411dce8729c32823c168`, EduardoA-J. Añade privacidad del snapshot, manejo de permisos de cámara y tabla de niveles móvil. La consulta de PR no devolvió PR en este repositorio.

- Express/Prisma/MySQL: es un servicio independiente, no sustituye la SQLite del catálogo de Jarvis.
- La verificación existente de Jarvis ya coincide con `POST /api/integrations/customer-qr/verify`, cuerpo `token`, encabezado `x-api-key`.
- La API devuelve identidad y expiración del QR. Mantener la capacidad de consulta temporal en el servidor, el límite de inactividad y la limpieza al cerrar conversación.
- Preferir `GET /api/integration/v1/customers/:id` después de verificar el QR para saldo, nivel y recompensas. Evitar acceso personal por correo o teléfono desde el kiosco.
- El QR PP1 se firma con el secreto JWT del sistema Points. Jarvis debe verificarlo por API y no recibir ese secreto general.
- Los nuevos canjes incluyen `expiresAt`. Nuestro lector SQL necesita contemplar esa fecha además del estado para no informar válido un canje vencido.
- Stock de recompensas, cumpleaños y reglas de canje pertenecen a Points; conviene consumir sus resultados en vez de duplicar cálculos en Jarvis.

Faltan URL accesible de la API y una clave de integración configurada en el entorno local. No se conectó una base real, no se ejecutaron migraciones y no se cargó el volcado SQL del repositorio. El catálogo y las conversaciones pueden presentarse sin esa conexión; los puntos personales siguen pendientes de integración real.

## UX/UI: aportes revisados

Repositorio: https://github.com/daer-1701/Paseito

PR #4 y #5 de `smm222-cyber` están fusionados. Main consultado: `b460732`, merge de David Andres Escalera Rocha. Nuestra rama y main divergen: 3 commits exclusivos nuestros y 16 exclusivos de main.

| Aporte | Decisión recomendada |
|---|---|
| Modelos del Cristo, edificio y árboles; suelo | Conservar mediante integración selectiva en nuestro avatar. |
| Iluminación según horario | Conservar con un modo fijo para una presentación consistente. |
| Desenfoque y compositor | Adaptar con calidad reducida o desactivación en móviles modestos. |
| Correcciones móviles y composición visual | Conservar tras comparar con nuestros controles actuales. |
| Eliminación del logo | Revisar identidad acordada; conservar una identificación clara del producto. |
| Sustitución completa de index/avatar | Evitar: requiere preservar QR, privacidad, Points, WhatsApp y compatibilidad de nuestra versión. |

Antes de incorporar: alojar localmente los módulos de posprocesado importados desde CDN; reactivar el ajuste automático de calidad comentado; prever errores de carga de GLB y revisar el peso de aproximadamente 12 MB de modelos. No se midió el rendimiento de estos nuevos visuales.

Commits destacados: `5640c54` logo, `cea289a` suelo, `7eb5588` blur móvil, `54479b9` árboles y `f193143` iluminación por horario. Estos aportes todavía no se integraron en nuestra rama.

PR: https://github.com/daer-1701/Paseito/pull/4 y https://github.com/daer-1701/Paseito/pull/5
