# Etapa 2: Points temporal y orientación

Base: etapa 1, 114c0c5. Rama: feat/etapa2-points-sesion. Arquitectura: FastAPI, SQLite común, un orquestador OpenAI con respaldo local y una interfaz para web/kiosco. WhatsApp conserva el mismo agente público.

## Las diez decisiones aprobadas

| Punto | Resultado |
|---|---|
| 1. Identidad temporal | QR validado emite capacidad aleatoria HttpOnly/SameSite Strict, ligada también al session_id. 90 segundos sin consulta conversacional; máximo 10 minutos. Cierre, reinicio o reinicio del servidor revocan. |
| 2. Validación | API HTTPS sin redirecciones o firma HMAC con secreto dedicado, vencimiento finito e identificador positivo. Cuenta CUSTOMER activa antes de conceder acceso real. Teléfono/correo nunca acreditan identidad. |
| 3. Caché | Solo programa público: 300 segundos, antigüedad máxima 600, filtro de vigencia y refresco en segundo plano. Saldo siempre consulta nueva. |
| 4. TLS | MySQL verifica CA y nombre del host. API QR HTTPS excepto loopback de desarrollo. |
| 5. Un intento | Sin reintentar una lectura fallida. Espera máxima de respuesta 8 segundos, acceso compartido limitado y máximo 8 lectores pendientes. Mensaje para continuar desde la web. Código de cupón consulta solo ese cupón. |
| 6. Ubicación | Respuesta natural con piso, sector, torre, local y referencia del directorio; destaca piso en pantalla y ofrece ficha/QR para teléfono. |
| 7. Recorrido | Sin tiempos, distancias, giros o ascensores inventados. Sigue pendiente el mapa interior validado y origen físico del kiosco. |
| 8. Catálogo | Conserva 1801 registros y aportes de etapa 1. Fuentes, fechas editoriales y tombstones evitan borrar o sobrescribir trabajo aprobado. Conflictos comerciales quedan en revisión administrativa. |
| 9. Administración | Token obligatorio siempre, incluyendo analítica y calidad. No habilitar acceso por ausencia de configuración. |
| 10. IA | OpenAI y respaldo local. No se reintroduce Gemini. |

## Privacidad en pantalla

Saldo y cupones personales no entran al historial del modelo, SQLite ni analytics. Analytics guarda solo el evento genérico y conteo. Las respuestas personales se muestran solo en pantalla: no se envían a OpenAI TTS, Edge ni a cachés de voz. Caducidad, cierre y cambio de conversación limpian tarjetas, subtítulos y guía. Al abandonar la página también se limpia su contenido personal. La cookie revocada puede seguir almacenada hasta 10 minutos pero no concede acceso; no se elimina con respuestas tardías que podrían borrar una capacidad nueva.

La actividad que renueva el permiso es una consulta al agente; mover el ratón o escribir sin enviar no lo prolonga. Un código de cupón no concede acceso al perfil y su resultado desaparece tras 90 segundos. Cada QR de cliente requiere validación nueva para reabrir acceso expirado.

## Revisar la demo

1. Abrir http://localhost:8000/ y tocar para empezar.
2. Pulsar Lee mi QR → Probar identidad de demo.
3. Preguntar Cuántos puntos tengo. Aparece saldo de ejemplo de 160 y nivel Plata, identificado como demo.
4. Cerrar desde el indicador temporal, pulsar Nueva conversación o dejar 90 segundos sin consultas. El saldo desaparece y debe validarse nuevamente.
5. Ver ejemplo local en el lector permite mostrar un cupón independiente, no canjeable.

La demo requiere JARVIS_DEMO_CATALOG=1. No acredita saldo ni cuenta reales.

## Conexión real pendiente

Configurar localmente PUNTOS_DATABASE_URL y PUNTOS_DB_CA con cuenta MySQL de solo lectura; API PUNTOS_API_URL/PUNTOS_API_KEY del emisor o PUNTOS_QR_SECRET acordado con él. No compartir secretos por chat. La CA se monta con compose.points.yaml. El proveedor debe confirmar esquema User/PointMovement/StatusMovement/Tier y contrato PP1. Para proxy HTTPS, establecer PASEITO_COOKIE_SECURE=1 en la configuración.

No hay credenciales reales de Points ni OpenAI configuradas en la torre. El flujo real con cuentas del proveedor, emisión QR, cámara física y canje externo requieren integración y revisión con ese equipo. WhatsApp real sigue requiriendo proveedor; la demo local continúa disponible. Inventario/operaciones y mapa interior siguen pendientes.

## Evidencia y alcance

Build de jarvis realizado conservando el servicio GPU de voz. Recorridos manuales HTTP y navegador; no se añadieron ni ejecutaron suites automatizadas. Revisión final de código con correcciones: respuestas personales sin voz externa, actividad conversacional para renovación y límite para resultados de cupón sin identidad. Captura: etapa2-points-sesion.png.

Una instancia y un worker, como el despliegue actual. Para múltiples workers/replicas debe trasladarse la capacidad y revocación a un almacén compartido con TTL. Reiniciar hoy invalida todas las capacidades en memoria.

### Resultados manuales observados

- Health: ok, 1801 registros, proveedor configurado false, respaldo local. GPU: ready, streaming true.
- DEMO-PUNTOS: capacidad autenticada demo, 89999 ms de inactividad y 599999 ms absolutos al emitir.
- Consulta demo: 160 puntos, Plata. Cookie HttpOnly y SameSite Strict.
- Sin cookie, otra conversación, después de reset y después de cierre: HTTP 403.
- Tras 92 segundos sin solicitudes: HTTP 403, authenticated false.
- Código inválido: error y authenticated false.
- Dónde está Cayenna: intent navigation y cuarto piso, sector El Cuarto (terraza gourmet). Se corrigió la detección de dónde está, que antes perdía esas palabras al filtrar términos de búsqueda.
- Canjea mis puntos: deriva a web/comercio; ninguna operación financiera.
- SQLite: cero turns con la respuesta de saldo demo; tres eventos genéricos de consulta personal en el recorrido registrado.
- Navegador tras las correcciones: identidad → saldo en pantalla → cierre limpia saldo y pregunta, muestra mensaje de privacidad. Las respuestas personales no invocan hablar().

Decisión técnica: se priorizó revisión estática, build y recorridos manuales conforme a la instrucción de no añadir/ejecutar suites. El proveedor real y su esquema no se han validado por falta de credenciales.
