# Versión única: estado y pendientes

Base del compañero: `paseito/main` **28b9729**, incluida en
`feat/version-unica-openai`. Producto: **Paseito**, para el reto Jarvis.

## Decisiones implementadas

| Parte | Versión conservada e integración |
|---|---|
| API | FastAPI del compañero, con rutas para el catálogo versionado, voz y canales comunes |
| RAG/datos | SQLite y filtros de Jarvis; herramientas de lectura y descripción/FAQ/agenda del compañero |
| Proveedor | OpenAI Responses principal; respuesta local si falta clave, se excede el plazo o falla la API |
| Prompt | Español boliviano cálido; pocas opciones, elección de tienda y contexto; sin hechos inventados |
| UX/UI | Nuestro kiosco responsive, último avatar y visemas del compañero; tarjetas públicas Points |
| Voz | Whisper/Kokoro GPU con streaming, cancelación y respaldo del navegador antes de iniciar audio; Edge opcional portable |
| WhatsApp | Demo local y conector Twilio del mismo agente, firma y deduplicación por mensaje |
| Analítica | Métricas del compañero adaptadas al SQLite común y a todos los canales; datos de contacto redactados |
| Administración | Panel responsive para métricas, calidad y CRUD de registros; token obligatorio |
| Points | Conector público MySQL de solo lectura con TLS; caché normal 300 s, máximo 600 s y filtro de vigencias; demo pública opcional |
| Estímulos | Mirada saluda solamente en bienvenida sin conversación activa; repetición bloqueada, cooldown y demo manual |

Eliminadas las implementaciones activas duplicadas: agente Gemini, modelos SQLModel,
SQLite independiente, servidor HTTP anterior y copias del frontend. Sus fuentes
siguen recuperables en el historial Git. Se verificó además un respaldo completo
del frontend anterior antes de retirarlo.

## Catálogo consolidado

En el arranque de torre: **1.681 registros**: 82 lugares, 1.569 productos/servicios,
8 promociones, 15 FAQ (3 borradores excluidos) y 7 eventos (se filtran los terminados).
Los 74 lugares del compañero están representados: 71 enriquecen IDs existentes y
3 espacios públicos se incorporan. No se sobrescribieron horarios reales existentes.

El catálogo demo mantiene 10 productos por negocio gastronómico y 25 por tienda
comercial, precios en bolivianos y promociones con vencimiento. No crea existencias
reales. Los metadatos conservan procedencia, fechas, revisión y condición demo;
la interfaz identifica el modo y el agente no repite esas etiquetas en cada frase.

Las FAQ divergentes de horarios, estacionamiento y acceso 24/7 se mantienen como
borradores para revisión: [conflictos](conflictos-catalogo.json). Los seis eventos
del cronograma heredado conservan procedencia; falta revisión editorial de su fuente.

## Recorrido observado en esta torre

- Arranque Docker de la API unificada; `/health` correcto y voz GPU `ready` con streaming.
- Arranque de la misma imagen sin GPU con base vacía: 1.681 registros y voz de navegador disponible como respaldo.
- Camisas hasta Bs 150 → tres tiendas → primera tienda → catálogo filtrado → horario del domingo.
- Camisa + café + reunión de cinco: respuesta cubre las tres necesidades y conserva pendientes;
  la capacidad/disponibilidad de una sala requiere confirmación.
- Pizza por WhatsApp local → elección por número → catálogo con familiar a Bs 59;
  repetir ID devuelve `duplicate: true` sin una segunda consulta analítica.
- Programa público Points y tarjetas de recompensas en modo demo; saldo personal bloqueado.
- Saludo manual por mirada en la interfaz; el segundo evento de la sesión no vuelve a saludar.
- Analítica y calidad rechazan acceso sin token (401); consulta personal Points bloqueada (403).
- Consulta administrativa autenticada devuelve métricas de web y WhatsApp sobre el mismo almacén.
- Interfaz revisada en escritorio y viewport móvil de 390 × 844.

Se realizó revisión de código y recorridos manuales, sin agregar ni ejecutar suites.
La suite histórica del servidor HTTP anterior necesita adaptación a FastAPI;
por ejemplo, `test_voice_http.py` aún importa el handler que se retiró. Esa suite
no se presenta como validación de esta versión.
La revisión corrigió coherencia de opciones con el estado, cancelación de STT,
concurrencia entre visitantes WhatsApp, visibilidad de frescura Points y reinicio
tras eliminaciones administrativas. El servicio se configura con un único worker;
una futura réplica necesita coordinación distribuida de mensajes y sesiones.

## Qué falta para responder o actuar de verdad

| Solicitud del visitante | Estado y paso pendiente |
|---|---|
| «¿Queda una camisa talla M?» | Falta inventario de la tienda: stock, tallas y colores sincronizados |
| «Compra/reserva y confirma mi pedido» | Falta API PaseoYa, autorización, pago, idempotencia y confirmación del proveedor |
| «¿Cuántos puntos tengo?, canjea mi recompensa» | Bloqueado hasta sesión externa verificada; después integrar saldo y transacciones |
| Recompensas reales Points | Faltan URL, cuenta MySQL de solo lectura, CA y validación del esquema/permisos; existe demo pública identificada |
| «Escríbeme en mi WhatsApp real» | Faltan cuenta Twilio, credenciales, HTTPS y comprobación de entrega; la demo es local |
| «Guíame paso a paso desde donde estoy» | Hay piso/local y ficha/QR; falta mapa, posición real del kiosco y rutas validadas accesibles |
| Activación automática al mirar el kiosco | Endpoint y saludo listos; falta dispositivo, productor de eventos y calibración física |
| Conversación OpenAI en esta torre | Conector implementado; no se encontró `OPENAI_API_KEY` configurada. No se acredita una llamada real al proveedor |
| Datos comerciales oficiales | Precios/promociones/horarios demo requieren validación comercial antes de usarlos fuera de la presentación |

También faltan despliegue público y comprobación en un teléfono físico/PC ajeno,
medición de carga y revisión de los entregables finales/presentación con esta arquitectura.
La aplicación web responsive no equivale a una app nativa publicada en tiendas.

## Relación con la auditoría del reto

La auditoría detallada sigue en [auditoria-reto-jarvis.md](auditoria-reto-jarvis.md),
con el enunciado oficial del reto 2. Su **84 %** era una estimación del MVP y sus
entregables antes de esta consolidación; no se presenta como porcentaje de producción
ni se eleva automáticamente por tener conectores sin credenciales. Esta entrega
unifica la arquitectura y amplía la demo, con los pendientes externos explícitos.

## Referencia de implementación OpenAI

Se usa el flujo de llamadas a funciones de Responses, `function_call_output`,
esquemas estrictos y `store: false`, según la
[documentación oficial](https://developers.openai.com/api/docs/guides/function-calling).
El [modelo por defecto](https://developers.openai.com/api/docs/models/gpt-4.1-mini)
es configurable; no se atribuye una calidad o latencia medida sin una llamada real.
