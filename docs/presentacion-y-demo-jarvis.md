# Jarvis: presentación y demo actualizadas

Presentación editable de ocho diapositivas: [jarvis-reto-actualizado.pptx](entregables/jarvis-reto-actualizado.pptx).
El archivo jarvis-reto.pptx se conserva como versión histórica. Usar la versión
actualizada para exponer. Tiempo sugerido: 5 minutos de presentación y 3 de demo,
adaptado al tiempo oficial. Alcance: [revisión del PDF](fase3-limpieza-y-alcance.md).

## Contenido de las diapositivas

1. **Paseito · Reto Jarvis:** web con voz y avatar; https://jarvis.timosboy.win.
2. **Necesidad:** encontrar opciones, elegir y consultar ubicación y datos;
   administración mantiene una fuente común.
3. **Conversación y evidencia:** texto o voz, fichas con fuente, selección y guía.
   Información desconocida se trata como desconocida; vigencia filtra eventos y
   promociones. Los precios de ejemplo no certifican stock comercial.
4. **Arquitectura:** FastAPI, catálogo SQLite, OpenAI Responses con herramientas
   y respaldo local. RAG léxico con sinónimos y datos estructurados; no embeddings.
   Whisper y Kokoro en GPU local; SSE por Cloudflare. Web responsive y Three.js.
5. **Funciones:** catálogo, precios en Bs, horarios, promociones, eventos, guía
   por piso/sector/local, QR de destino, sesión Points temporal, WhatsApp local,
   adaptador Twilio, administración, analítica y evento de mirada.
6. **Datos y validación:** catálogo documentado y ejemplos comerciales;
   procedencia en «Información del catálogo». Cierre del despliegue: 42 pruebas
   backend y 6 frontend correctas. Navegador público verificado; el usuario
   confirmó carga y funcionamiento. Validación comercial y plano pendientes.
7. **Demo:** comida, local, catálogo, precio, ubicación, voz, QR, WhatsApp local,
   Points de ejemplo y reinicio de sesión.
8. **Pendientes:** Points real, número/proveedor de WhatsApp, hardware eye tracker,
   mapa interior y datos validados. Compras, canjes y stock real son adicionales.

## Guion de demo

Antes: comprobar /health, /voice/status, micrófono y parlantes. Docker y el túnel
deben estar activos. La GPU admite una tarea de voz a la vez.
[Inicio, límites y evidencia del despliegue](despliegue-presentacion.md).

1. Abrir https://jarvis.timosboy.win y tocar «Toca para empezar».
2. Preguntar «¿Dónde puedo comer?» y elegir «Almacén de Pizzas».
3. Pedir catálogo, precio y guía. Mostrar fuentes y piso/local.
4. Alternar texto y micrófono; abrir la ficha desde su QR en otro dispositivo.
5. Mostrar /whatsapp/demo: el mismo agente y conocimiento, sin cuenta real.
6. Leer DEMO-PUNTOS en modo de ejemplo. Sesión ligada a conversación y cookie;
   caduca a los 90 s de inactividad y tiene máximo de 10 minutos.
7. Reiniciar conversación: termina la sesión personal.

No presentar precios, promociones y horarios de ejemplo como datos comerciales
validados. No anunciar recorridos interiores confirmados, compras o canjes.
Points y WhatsApp reales necesitan credenciales; tener adaptadores no significa
que estén conectados.

## Respaldo y preguntas del jurado

Si falla Internet o el túnel, abrir http://localhost:8000 en el kiosco. Voz GPU
local disponible con modelos descargados. OpenAI necesita Internet; respaldo
local para catálogo. Clima y enlaces externos requieren red. Sin GPU, usar
modalidad portable con texto y voz del navegador.

- **¿Usan RAG?** Sí: recuperación léxica y estructurada; OpenAI consulta herramientas
  del catálogo. SQLite guarda el conocimiento local.
- **¿Cómo cuidan Points?** QR validado, cookie temporal y conversación vinculada;
  sesión personal en memoria, sin saldo privado en LLM ni analítica.
- **¿Qué está conectado?** OpenAI y GPU funcionando, HTTPS publicado. WhatsApp local
  y Points de ejemplo; integración real pendiente.
- **¿Qué falta?** Plano y datos validados, credenciales externas y ensayo físico
  de mirada y voz con ruido y concurrencia reales.

Pruebas: [cierre](entregables/cierre-verificado.md) y
[despliegue](despliegue-presentacion.md). Métricas puntuales de voz no son SLA.
