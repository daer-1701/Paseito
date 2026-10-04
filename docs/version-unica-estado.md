# Versión única: estado vigente tras fases 1–3

Fecha: 2026-10-03. Producto Paseito para el reto Jarvis. Rama de entrega: `main`,
con las fases 1–3 integradas y el diseño definitivo de smm222-cyber activo.

## Arquitectura y aportes conservados

| Parte | Implementación |
|---|---|
| API | FastAPI único en backend/app/main.py |
| Datos | SQLite versionado, 1801 registros cargados; catálogo, precios y promociones de demo con procedencia |
| IA | OpenAI Responses y respaldo local; clave cargada en la torre, respuesta real con herramientas comprobada |
| UX | Kiosco responsive, diseño definitivo de smm222-cyber (PR #4/#5): modelos GLB, árboles, suelo, iluminación horaria y desenfoque; dependencias Three.js locales y resolución adaptativa. Conserva visemas, QR, conversación, 20 imágenes y 120 productos incorporados |
| Voz | Whisper/Kokoro GPU con streaming, cancelación y respaldo del navegador; GPU lista |
| WhatsApp | Demo local y conector Twilio con firma y deduplicación; entrega real pendiente |
| Administración | CRUD, calidad y analytics con token obligatorio |
| Points | Programa público con caché 300 s, antigüedad máxima 600 s; TLS verificado |
| Identidad Points | QR validado por API/HMAC, cookie HttpOnly ligada a conversación, 90 s sin consultas y máximo 10 min |
| Orientación | Piso, sector, torre, local y referencia; ficha y QR públicos |
| Estímulos | Saludo por mirada en bienvenida y demo manual; dispositivo físico pendiente |

No hay agente Gemini, base alternativa ni segundo servidor activo. Avatar 2D y 3D
son implementaciones usadas: el 2D es respaldo si el navegador no permite el 3D.
`habla.js` es compartido por ambos y se conserva.

La vista normal no muestra el botón manual de mirada ni una insignia de demo.
El catálogo conserva su procedencia en «Información del catálogo». Para ensayar
el saludo manual, abrir `/?demo=mirada`; no depende del catálogo sintético.
OpenAI, Points y WhatsApp requieren sus respectivas conexiones reales: ocultar
controles de ensayo no configura proveedores ni valida los precios de ejemplo.

## Requisitos e integraciones

Evidencia reciente y límites: [Cierre comprobado en la torre](entregables/cierre-verificado.md).

El PDF exige para Jarvis informar sobre negocios, horarios, productos, servicios,
promociones, eventos, ubicación y recomendaciones (4.6, p. 6). Integración con
Points/PaseoYa y navegación interna figuran como adicionales (4.10, p. 7).
Inventario, pedidos, pago y retiro pertenecen al reto PaseoYa. No se contabilizan
como carencias mínimas de Jarvis. [Matriz y evidencia del PDF](fase3-limpieza-y-alcance.md).

| Solicitud | Capacidad actual y límite |
|---|---|
| Producto, precio y tienda | Catálogo y conversación con elección, presupuesto y seguimiento; precios demo no son ofertas comerciales aprobadas |
| Stock/talla/color actual | No se consulta inventario real; informa el límite y ofrece catálogo |
| Reserva, compra, pago, pedido o devolución | Explica la alternativa concreta y no confirma operaciones |
| Saldo Points | Flujo temporal listo, demo de ejemplo; proveedor real pendiente |
| Dónde queda | Ubicación publicada y piso destacado; mapa/ruta interior validada pendiente |
| WhatsApp | Demo funciona; proveedor y entrega real pendientes |

Datos comerciales, horarios conflictivos, ubicación exacta del kiosco, móvil en
red y ensayo presencial siguen requiriendo revisión. Los conflictos de horario de
Cayenna y FAQ heredadas no sobrescriben información vigente.

## Privacidad y evidencia

Respuestas personales solo en pantalla; no se envían a voz externa, LLM, turns ni
analytics. Cierre, reinicio, abandono de página y caducidad limpian pantalla y revocan
acceso. Analytics conserva evento genérico. Un código de cupón consulta solo ese cupón.

Build y recorridos manuales documentados en [etapa 1](etapa1-aportes-companero.md),
[etapa 2](entregables/etapa2-points-sesion.md) y [fase 3](fase3-limpieza-y-alcance.md).
No se han ejecutado suites automatizadas. Informes anteriores se conservan como
históricos; sus porcentajes y conteos no describen esta rama.

Una instancia/worker. Múltiples replicas requieren revocación y sesiones compartidas.
No borrar volúmenes Docker para arrancar.
