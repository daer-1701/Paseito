# Demo conversacional y canal WhatsApp

## Alcance autorizado

Solicitud del 3 de octubre de 2026: respuestas naturales, elección de tienda antes del catálogo, horarios y promociones coherentes para demostración, WhatsApp preparado con respaldo. Navegación interior, inventario real y operaciones permanecen pendientes.

## Diseño

Preprocesar consulta (acentos, sinónimos, intención, presupuesto), recuperar productos y agrupar por negocio; guardar etapa, tema, negocios sugeridos y tienda elegida en preferencias existentes. Presentar tres negocios y una pregunta; después mostrar catálogo paginado. Precio solo en catálogo/consulta de precio; inventario desconocido solo cuando se solicite. Mantener procedencia en datos y una señal general de modo demo, sin avisos hablados repetidos.

Horarios de prueba como overlay: nunca sobrescribir calendario real ni cambiar la fuente oficial. Promociones con inicio, fin y condiciones explícitos, filtradas por la misma activación de demo. Ningún stock inventado.

WhatsApp: webhook Twilio dedicado, validación de firma, sesión opaca por remitente y deduplicación persistente. Respuesta TwiML síncrona desde el mismo agente local: sin dependencia de modelos externos ni cola de envío para el MVP. Solo conversación iniciada por usuario. Vista local del canal, claramente identificada, para respaldo sin proveedor o Internet. No es evidencia de entrega por WhatsApp real. Credenciales y HTTPS externos pendientes de configuración.

## Pasos

- [x] Capa de diálogo y respuestas legibles, conservando agentes de eventos, clima e integraciones pendientes.
- [x] Overlay de horarios, promociones y limpieza de tarjetas/voz.
- [x] Conector Twilio y vista local de respaldo.
- [x] Reconstrucción, revisión de flujos de presentación y documentación de resultado y dependencias.

## Límites

No crear cuentas ni enviar mensajes a personas sin autorización explícita. No exponer administración ni el kiosco completo al habilitar webhook. No prometer ausencia total de fallos; documentar recuperación y guion alternativo. No ejecutar la suite ni añadir tests sin solicitud del usuario; sí comprobar salud y recorrer manualmente las funciones entregadas.

## Cierre observado

Servicio en `ok`, 1.661 registros; voz GPU lista. Recorridos manuales de tienda → selección por número → catálogo → paginación, precio promocional Bs 59, horario y seguimiento por domingo, consulta de inventario pendiente y recuperación de mensaje duplicado. Revisión visual de respaldo a 390 px. Sin suite automatizada ni conversación real por WhatsApp. El usuario eligió conector preparado y respaldo local por no tener cuenta externa.
