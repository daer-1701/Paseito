# WhatsApp MVP y respaldo para presentación

Estado del 3 de octubre de 2026: el usuario no dispone de cuenta Twilio ni Meta. Se implementaron el conector Twilio y la vista local de respaldo. **No se ha conectado ni acreditado entrega en WhatsApp real.**

## Para mostrar hoy

Abrir [respaldo local](http://localhost:8000/whatsapp/demo) o [kiosco](http://localhost:8000/kiosk/). La vista de mensajes usa el mismo agente y la misma sesión conversacional que usará el webhook; no envía mensajes a teléfonos. Mantenerla abierta antes de presentar.

Guion sugerido:

1. “Busco una camisa”: tres tiendas, productos relevantes y pregunta de elección, sin precios/stock recitados.
2. “2”: catálogo de la segunda tienda, con precios; después “Ver catálogo de …” para ampliar la selección.
3. “Horario de Amore” o “¿Y el domingo?”: horario completo de la tienda elegida.
4. “¿Qué promoción hay en Almacén de Pizzas?”: familiar de ocho porciones a Bs 59, sabores/condiciones y fin el **11 de octubre de 2026 a las 23:59**, hora de Bolivia.
5. “Precio de pizza familiar en Almacén de Pizzas”: mostrar Bs 59 durante la vigencia. Después de vencer, volver al precio base del catálogo. El descuento de paquete de dos poleras no se aplica a una sola prenda.
6. “¿Hay stock?”: indicar una sola vez que no se consultan existencias en tiempo real. No inventar cantidades.
7. Reiniciar para regresar a una sesión nueva sin preferencias anteriores.

El canal local no requiere Internet, cuenta externa ni LLM remoto. El servidor y sus datos deben estar funcionando. El kiosco conserva voz local GPU; el respaldo por texto funciona aunque el micrófono, altavoz o la voz fallen. No se promete ausencia absoluta de fallos.

Si falla una solicitud, el botón de reintento conserva su identificador: no duplica el turno procesado. Si el servidor cae, usar el kiosco tras recuperar Docker; no presentar capturas como interacción en vivo.

## Implementado

- `GET /whatsapp/demo`: interfaz móvil/escritorio local, historial visible, elecciones, reinicio y reintento.
- `POST /whatsapp/demo/message`: sesión de demostración, mismo procesamiento del webhook, respuesta JSON. Solo disponible en modo demo.
- `POST /whatsapp/webhook`: formulario Twilio entrante; SDK oficial `twilio==9.11.2` para comprobar `X-Twilio-Signature`, incluyendo todos los parámetros recibidos y URL HTTPS exacta.
- Respuesta TwiML síncrona. No llamadas de envío proactivo ni dependencia de un LLM/consulta de clima en este canal.
- Identificador de sesión derivado mediante HMAC del remitente; no guardar su teléfono en la búsqueda pública ni exponerlo en estado del conector.
- Deduplicación SQLite durante 48 horas. Un mensaje repetido devuelve TwiML vacío en el canal real para no enviar dos respuestas; la vista local recupera su respuesta previa. Un mismo ID con contenido distinto se rechaza.
- Consulta de estado `/whatsapp/status`, sin devolver secretos. `configured` no significa entrega confirmada; `delivery_verified` permanece falso y se requiere observar una conversación real.
- Adjuntos reciben una petición de escribir texto. Operaciones, inventario real y navegación interior siguen pendientes.
- `compose.whatsapp.yaml` y `deploy/whatsapp.conf`: pasarela opcional, ligada a loopback en 8081, que solo permite POST al webhook. No abre administración, conversaciones privadas ni el kiosco a Internet.

## Activar WhatsApp real posteriormente

1. Crear/configurar la cuenta Twilio personalmente y aceptar sus términos. En consola antigua, Sandbox; en la consola nueva y trial, “Try out WhatsApp”. Cada participante debe incorporarse al entorno de prueba. [Instrucciones de Twilio](https://www.twilio.com/docs/whatsapp/sandbox).
2. En `.env` local, nunca en chat ni Git:

   ```dotenv
   JARVIS_WHATSAPP_PROVIDER=twilio
   TWILIO_AUTH_TOKEN=<Auth Token de la cuenta>
   JARVIS_WHATSAPP_SESSION_SECRET=<secreto aleatorio largo y estable>
   JARVIS_WHATSAPP_WEBHOOK_URL=https://<dominio>/whatsapp/webhook
   ```

   Si falta el secreto dedicado, se usa el token administrativo local como secreto HMAC. Para un servicio permanente, configurar el secreto dedicado y conservarlo entre reinicios. No necesita Account SID para esta respuesta entrante TwiML; se necesitaría para integrar envío mediante REST después.

3. Aplicar desde Ubuntu/WSL, en la raíz del repositorio:

   ```bash
   docker compose -f compose.yaml -f compose.whatsapp.yaml up -d --build jarvis whatsapp
   ```

4. Proveer HTTPS confiable mediante un despliegue o túnel dedicado a `127.0.0.1:8081`. Esa exposición no se activó ahora. Evitar URL temporal para el ensayo final; si cambia, actualizar `.env`, recrear Jarvis y configurar la misma URL exacta en Twilio. No publicar el puerto 8000 completo.
5. Configurar “When a Message Comes in” como POST a la URL exacta. No usar el callback de estado en este endpoint: sus eventos no son mensajes entrantes. La firma debe validarse; nunca deshabilitarla para solventar una URL mal configurada. [Seguridad del webhook](https://www.twilio.com/docs/usage/webhooks/webhooks-security).
6. Un participante envía una consulta y se observa la respuesta **en WhatsApp**, la elección de tienda, el catálogo y la promoción. Repetir desde una sesión nueva antes de subir al escenario. El usuario debe autorizar cualquier mensaje a una persona; este MVP solo responde mensajes iniciados por participantes.

## Antes de presentar

- Docker y Jarvis abiertos, `/health` en `ok`; abrir la vista local y dejar una segunda pestaña con kiosco.
- Reiniciar conversación para limpiar presupuesto/tienda anteriores.
- Revisar fecha: promociones actuales terminan el 11 de octubre; no renovar campañas automáticamente ni afirmar vigencia vencida.
- Si se demuestra voz, seleccionar micrófono/altavoz y ensayar en el ruido del lugar; usar texto ante un fallo.
- Si después se configura Twilio, confirmar incorporación reciente de participantes, URL exacta, saldo/límites y respuesta real; ensayar el cambio al respaldo local. El Sandbox limita envíos y participantes y no es un canal comercial. [Límites oficiales](https://www.twilio.com/docs/whatsapp/sandbox).

## Presentación de los datos

Se quitaron advertencias repetidas de las respuestas y tarjetas. El kiosco conserva “Modo demo” con enlace a su alcance; el respaldo local tiene aviso general y el canal Twilio indica “Jarvis · modo demo” en su primer contacto. La procedencia sigue en el JSON. Productos/precios/promociones y los horarios faltantes son datos de prueba, no publicaciones de los negocios. Los horarios reales existentes se conservan mediante un overlay solo en modo demo.

## Resultado observado

La primera reconstrucción arrancó con 1.661 registros: 79 negocios, 1.569 productos/servicios, 8 promociones, 4 FAQ y 1 evento. Se recorrió en navegador la búsqueda de camisas, elección por número, catálogo, horario de tienda y promoción de pizzas. No se ejecutó una suite automatizada ni se envió un mensaje por WhatsApp real. La documentación de cierre registra las revisiones finales adicionales.

### Revisión final

Se observó el catálogo de pizzas: familiar a Bs 59 en la primera página y los otros cinco productos en la segunda; recomendación de tres tiendas con elección por número, catálogo de Amore y seguimiento “¿Y el domingo?” (11:00–20:00). Un reintento del mismo ID devolvió `duplicate=true` y el mismo texto; la primera respuesta devolvió `duplicate=false`. Consulta breve de stock responde que todavía no hay consulta de existencias, sin recitar cantidades. `/voice/status` informó GPU lista, transcripción y streaming disponibles. Captura de la vista local: `docs/entregables/demo-dialogo-movil.jpg`. Esto no sustituye ensayar audio en el lugar ni acreditar entrega por WhatsApp real.
