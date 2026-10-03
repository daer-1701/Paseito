# Decisiones técnicas para Paseo Aranjuez Digital

Fecha: 2 de octubre de 2026. Objetivo: una demo funcional de Jarvis,
PaseoYa y Paseo Points antes del domingo a las 10:00. Suposiciones: demo en
navegador, USD 10 iniciales para la API de OpenAI y datos preparados por el equipo.

**Actualización:** Jarvis se plantea como un [asistente presencial con servidor
central](propuesta-jarvis-presencial.md). Esa propuesta define el despliegue y
la experiencia de la demo; las opciones de esta página sirven para decidir
integraciones y una evolución posterior.

## Recomendación

| Capa | Elegir ahora | Motivo |
| --- | --- | --- |
| Web | Página de kiosco actual y enlaces al frontend del equipo | Permite demostrar voz, fuentes y continuidad por QR sin rehacer la interfaz antes del domingo. |
| Backend Jarvis | Servicio Python actual; FastAPI después de estabilizar la demo | Mantiene funcional la lógica existente. OpenAPI será útil al ampliar las integraciones. |
| Datos e identidad | Catálogo SQLite para demo; PaseoYa y Points como dueños de sus datos | Permite actualizaciones inmediatas y evita copiar saldos o pedidos privados al RAG. |
| Búsqueda inicial | Campos estructurados y búsqueda de texto local; PostgreSQL al crecer | El catálogo inicial será pequeño y cambia con frecuencia. |
| Modelo de texto | OpenAI GPT-6 Luna mediante Responses API | Costo bajo para respuestas breves basadas en datos recuperados; `reasoning.effort=none` evita gastar tokens de razonamiento en el MVP. |
| Voz | Whisper local para transcribir + Piper local para hablar | Reduce el consumo de la API y reutiliza `/chat`; la primera versión funciona por turnos. |
| Despliegue | Un servidor central local y kioscos en navegador | Mantiene modelos de voz y catálogo cargados; permite varios puntos con una fuente común. |

La página de Jarvis puede correr en un navegador del kiosco y el resto del
equipo puede conservar su framework web. Las integraciones se acuerdan mediante
contratos HTTP e IDs estables.

## Cómo debe responder Jarvis

1. Entender la necesidad del visitante y consultar herramientas de lectura:
   `buscar_negocios`, `buscar_productos`, `ver_promociones`, `ver_eventos`.
2. Consultar `ver_puntos` y `ver_pedido` únicamente con una sesión autenticada.
3. Construir la respuesta con registros recuperados, fecha de actualización y
   enlaces/identificadores de fuente. Si un horario, precio o disponibilidad
   no consta, decirlo.
4. Para compras y canjes, dirigir al flujo de PaseoYa o Points. Una acción de
   escritura futura exige confirmación del usuario.

Los productos, stock, puntos y pedidos son datos estructurados: se consultan
en PostgreSQL o mediante la API dueña del dato en el momento de la pregunta.
La recuperación de texto sirve para descripciones, FAQs y lenguaje del
visitante. PostgreSQL incorpora búsqueda de texto; Supabase ofrece después
`pgvector` y búsqueda híbrida si una evaluación muestra que se pierden
sinónimos o consultas semánticas. Empezar con columnas `category`, `tags` y
texto claro facilita consultas como «quiero un regalo».
[PostgreSQL Full Text Search](https://www.postgresql.org/docs/current/textsearch-intro.html),
[Supabase Full Text Search](https://supabase.com/docs/guides/database/full-text-search),
[Supabase hybrid search](https://supabase.com/docs/guides/ai/hybrid-search).

No hace falta un proceso continuo de reindexación para este MVP: cuando el
equipo actualice un registro, se consulta la fila vigente; las descripciones
indexadas se actualizan con la misma transacción. Supabase permite webhooks de
`INSERT`, `UPDATE` y `DELETE` si algún equipo mantiene otra base y necesita
sincronizarla. Las promociones llevan `starts_at`, `ends_at` y estado.
[Supabase Database Webhooks](https://supabase.com/docs/guides/database/webhooks).

## OpenAI: modelos, voz y presupuesto

GPT-6 Luna cuesta USD 0,10 por millón de tokens de entrada y USD 0,50 por
millón de salida. Una consulta estimada de 1.000 tokens de entrada y 300 de
salida costaría alrededor de USD 0,00025; el consumo real depende del tamaño
del contexto y de las respuestas. Jarvis usa Responses API con
`reasoning.effort=none`, `store=false` y un máximo de 350 tokens de salida.
La clave `OPENAI_API_KEY` vive solo en el backend. Hay que comprobar el acceso
del proyecto al modelo con una llamada real antes de la demo.
[GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna),
[Responses API](https://developers.openai.com/api/docs/guides/text),
[precios](https://developers.openai.com/api/docs/pricing),
[lista de despliegue](https://developers.openai.com/api/docs/guides/deployment-checklist).

La voz elegida es local. El navegador graba una frase, `whisper-cli` la
transcribe en español, Jarvis consulta sus datos y OpenAI produce el texto; un
modelo Piper genera la respuesta hablada. Esto evita facturar sesiones de voz
en OpenAI. En el Mac de desarrollo ya están descargados los modelos y existe
una página de prueba en el backend. El backend ya acepta eventos de mirada
sostenida sobre una ficha mediante `/stimulus/gaze`; falta conectar el
dispositivo y su UI. La conversación simultánea requiere medir latencia antes
de integrarse a la demo.
[whisper.cpp](https://github.com/ggml-org/whisper.cpp),
[Piper](https://github.com/OHF-Voice/piper1-gpl).

## Despliegue y orden de entrega

Para el jurado, el Mac actual puede alojar Jarvis y servir la página del
kiosco en la red local. Para operación 24/7, usar un servidor central dedicado
con almacenamiento persistente, refrigeración, monitoreo y respaldo de energía;
los kioscos solo capturan interacción y muestran resultados. Las aplicaciones
PaseoYa y Points pueden desplegarse por separado y conservar sus propios
datos. La API de Jarvis consulta sus datos privados únicamente con identidad.

La secuencia de entrega es texto → fuentes e integración → voz por turnos.
La voz llama la misma lógica de consultas de Jarvis. Medir transcripción,
respuesta y síntesis con el hardware que se llevará a la presentación.

## Cambios necesarios al prototipo actual

El backend actual en `apps/jarvis-backend` es una base local: usa
`http.server`, SQLite y coincidencia de palabras. Antes de integrarlo con la
web compartida:

1. Definir contratos mínimos con PaseoYa y Points. Puntos y pedidos se
   consultan con identidad del visitante y no se agregan al índice público.
2. Cargar datos reales con `source_id`, `updated_at`, `starts_at` y `ends_at`;
   retirar automáticamente información vencida.
3. Verificar una llamada real de OpenAI con la clave del servidor y probar la
   página de voz local con el catálogo definitivo.
4. Tras la demo, pasar a FastAPI/OpenAPI y PostgreSQL si la operación y el
   tamaño del catálogo lo justifican.

FastAPI genera documentación OpenAPI y valida modelos con Pydantic. Supabase
recomienda Row Level Security para controlar el acceso de las aplicaciones a
PostgreSQL.
[FastAPI](https://fastapi.tiangolo.com/features/),
[Supabase RLS](https://supabase.com/docs/guides/database/postgres/roles).

## Acuerdos que el equipo debe cerrar hoy

- Nombre y campos mínimos de negocio, producto, promoción, evento, pedido y
  cuenta de puntos; dueño de cada tabla.
- IDs estables compartidos (`user_id`, `venue_id`, `product_id`) y moneda BOB.
- Primeras 20–30 fichas de negocio/producto y 3–5 promociones/eventos con
  fuente y vigencia; suficientes para una demo honesta.
- Una clave del proyecto OpenAI configurada en el servidor y un límite de gasto
  acorde con los USD 10 cargados; verificar el modelo y monitorear el uso.
- Dirección estable del servidor en la red local y una demo cargada que funcione
  aunque falle internet.

Para el jurado, preparar tres recorridos: recomendar un regalo, mostrar un
producto para retiro presencial en PaseoYa y consultar puntos autenticados.
