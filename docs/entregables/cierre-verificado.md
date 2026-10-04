# Cierre comprobado en la torre

Fecha: 3 de octubre de 2026 (Bolivia). Validación sobre la versión unificada de `main`.

## Resultados

| Comprobación | Evidencia |
|---|---|
| OpenAI Responses directo | HTTP 200, estado completed, 2,33 s |
| Agente con herramientas | Consulta sobre el Paseo: openai_tools, gpt-4.1-mini, fallback=false, 5.234 ms |
| Comida mexicana tras corrección | Chipotle Mexican Food como única tienda; openai_tools, fallback=false, 3.257 ms |
| Voz GPU completa | Dos fragmentos PCM; primer audio 2.172 ms, síntesis total 2.281 ms |
| Whisper GPU | Transcribió correctamente «Hola, soy Paseito. Puedo ayudarte a encontrar una tienda.» en 2.547 ms |
| Administración / analítica anónimas | HTTP 401 en ambas rutas |
| Points personal sin QR | HTTP 403 con session_id válido |
| QR y conversación | DEMO-PUNTOS permitió la lectura en su sesión; otra sesión recibió 403; cerrar revocó el acceso |
| WhatsApp local | Respuesta disponible, segundo message_id idéntico marcado duplicate; sin entrega real |
| Catálogo documentado | JARVIS_DEMO_CATALOG=0: 124 productos visibles, 120 de menús del compañero, cero productos sintéticos y cero promociones vigentes |
| Servicios Docker | Jarvis y voice healthy; SQLite y modelos conservados |
| Credenciales | .env ignorado por Git; ninguna clave registrada en este documento |

Estas latencias corresponden a solicitudes locales individuales, sin concurrencia ni Cloudflare. No representan percentiles ni un compromiso de latencia pública. La primera consulta del agente usó respaldo local; posteriormente dos consultas completas sí usaron OpenAI. El respaldo sigue siendo necesario cuando el proveedor supera el tiempo límite.

## Correcciones publicadas con este cierre

- Conservar la cocina solicitada: «comida mexicana» no sustituye la búsqueda por comida genérica.
- Ofrecer tiendas con fuente aunque falte su catálogo de productos, indicando la falta de precio y stock.
- Actualizar las pruebas del servidor anterior para la arquitectura vigente, sin reintroducir sus funciones obsoletas.
- Corregir rutas de las pruebas de frontend hacia la única carpeta activa.
- Añadir pruebas de aislamiento Points, inactividad de 90 segundos, límite absoluto de 10 minutos y revocación que cancela validaciones pendientes.
- Actualizar el arranque del equipo para clonar main y explicar los modos de catálogo.

## Pruebas automatizadas ejecutadas

- Backend: `python -m unittest discover -s apps/jarvis-backend/tests -p 'test_*.py'`, con PYTHONPATH=apps/jarvis-backend;backend: **39 pruebas, todas correctas**.
- Frontend: `node --test apps/jarvis-backend/tests/evidence.test.mjs apps/jarvis-backend/tests/stream-player.test.mjs`: **5 pruebas, todas correctas**.

La prueba de voz real usó audio generado por Kokoro enviado a Whisper; no comprobó permisos ni calidad del micrófono físico. El recorrido QR usó identidad de ejemplo; no comprobó la API real de Points. No se afirma haber ejecutado todas las pruebas de otros servicios ni una instalación limpia en otro equipo.

## Pendiente antes de una presentación pública

1. Elegir el modo de catálogo activo. En esta revisión no se cambió el .env: continúa el catálogo de ejemplos. La bandera 0 filtra sin borrar registros, pero también deshabilita demos de WhatsApp y ensayos de Points/mirada que aún comparten esa bandera.
2. Cloudflare y transporte SSE público: pendiente de implementar/publicar y medir por HTTPS.
3. Origen físico del kiosco: necesita piso, sector y referencia confirmados.
4. Points/WhatsApp reales y eye tracker: requieren servicio, credenciales o dispositivo.
5. Diapositivas finales, arranque desde copia limpia y ensayo en el lugar: pendientes.

Los puntos anteriores no se consideran cerrados por haber pasado las pruebas locales.
