# Decisiones técnicas para Paseo Aranjuez Digital

Fecha: 2 de octubre de 2026. Objetivo: una demo funcional de Jarvis,
PaseoYa y Paseo Points antes del domingo a las 10:00. Suposiciones: demo en
navegador, presupuesto bajo, datos preparados por el equipo y proveedor de IA
aún por elegir.

## Recomendación

| Capa | Elegir ahora | Motivo |
| --- | --- | --- |
| Web | Next.js + TypeScript, una experiencia web con rutas de Jarvis, PaseoYa y Points | Una sesión y navegación coherentes; el monorepo puede desplegar proyectos por directorio. |
| Backend Jarvis | Python + FastAPI + Pydantic | Reutiliza la lógica Python existente y genera documentación OpenAPI para el resto del equipo. |
| Datos e identidad | Un proyecto Supabase: PostgreSQL + Auth | Catálogo, pedidos y puntos consultables desde un mismo lugar con reglas de acceso. |
| Búsqueda inicial | PostgreSQL Full Text Search sobre negocios, productos, promociones, eventos y FAQ | El catálogo de la demo será pequeño y cambia con frecuencia. |
| Modelo de texto | Gemini 3.1 Flash-Lite | Tiene capa compatible con Chat Completions, funciones, salidas estructuradas y nivel gratuito sujeto a límites. |
| Voz | Gemini 3.1 Flash Live Preview si el texto ya funciona | Tiene conversación de audio y llamadas a funciones; la vista web obtiene un token efímero desde el backend. |
| Despliegue | Vercel para web y FastAPI como proyectos separados del mismo Git; Supabase para datos | Evita depender del disco local de una función. Mantener también una demo local preparada. |

La elección de Next.js depende de que el equipo frontend ya sepa React. Si
conoce mejor otra herramienta, mantener el contrato HTTP de Jarvis y escoger
la que permita terminar la demo. Vercel admite proyectos separados por carpeta
de un monorepo y despliegue de FastAPI, pero su runtime Python está en beta.
[Next.js](https://nextjs.org/docs/app), [Vercel monorepos](https://vercel.com/docs/monorepos),
[FastAPI en Vercel](https://vercel.com/docs/frameworks/backend/fastapi),
[runtime Python](https://vercel.com/docs/functions/runtimes/python).

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

## Elección de modelos y voz

**Primera opción: Gemini.** Gemini 3.1 Flash-Lite ofrece un nivel gratuito y
puede usarse mediante un endpoint compatible con Chat Completions, por lo que
el adaptador configurable del prototipo Jarvis puede conectarse sin cambiar
el formato general de petición. Gemini 3.1 Flash Live Preview ofrece audio y
funciones, pero es un modelo preview: revisar el límite real del proyecto en
AI Studio y preparar una ruta de texto. Los tokens efímeros de Live se crean
en el servidor para una conexión del navegador.
[Modelo de texto](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite),
[compatibilidad OpenAI](https://ai.google.dev/gemini-api/docs/openai),
[precios](https://ai.google.dev/gemini-api/docs/pricing),
[límites](https://ai.google.dev/gemini-api/docs/rate-limits),
[Live y herramientas](https://ai.google.dev/gemini-api/docs/live-api/tools),
[tokens efímeros](https://ai.google.dev/gemini-api/docs/live-api/ephemeral-tokens).

Configuración prevista para el adaptador de texto existente (pendiente de una
prueba con la clave real del equipo):

```bash
JARVIS_LLM_URL=https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
JARVIS_LLM_MODEL=gemini-3.1-flash-lite
JARVIS_LLM_API_KEY=<clave-del-proyecto>
```

**Alternativa con presupuesto: OpenAI.** GPT-6 Luna cuesta actualmente
USD 0,10 por millón de tokens de entrada y USD 0,50 por millón de salida.
GPT-Live cuesta USD 0,05 por minuto de sesión, además del trabajo del backend;
permite mantener el agente de texto separado de la conversación hablada.
Su guía recomienda WebRTC para voz en navegador. Confirmar acceso del
proyecto antes de depender de esta opción.
[GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna),
[precios](https://developers.openai.com/api/docs/pricing),
[arquitecturas de voz](https://developers.openai.com/api/docs/guides/voice-agents),
[WebRTC](https://developers.openai.com/api/docs/guides/voice-webrtc).

## Despliegue y orden de entrega

Vercel permite desplegar FastAPI como una función y organizar
proyectos separados por directorio. Su runtime Python está en beta. Si falla
la integración, Render permite desplegar FastAPI; su instancia gratuita se
duerme tras 15 minutos de inactividad y pierde el SQLite local al reiniciarse.
Para una demo sin ese arranque lento, su instancia Starter figura a USD 7/mes
o USD 0,05/hora. En ambos casos, usar Supabase para persistir datos.
[Vercel FastAPI](https://vercel.com/docs/frameworks/backend/fastapi),
[Render FastAPI](https://render.com/docs/deploy-fastapi),
[Render Free](https://render.com/docs/free),
[Render pricing](https://render.com/pricing).

La secuencia de entrega es texto → fuentes e integración → voz. La voz debe
llamar la misma lógica de consultas de Jarvis. Una ruta de respaldo de pulsar
para hablar puede usar transcripción → `/chat` → síntesis si Live falla;
OpenAI documenta esta arquitectura por etapas para controlar cada paso.
[Voice agents](https://developers.openai.com/api/docs/guides/voice-agents).

## Cambios necesarios al prototipo actual

El backend actual en `apps/jarvis-backend` es una base local: usa
`http.server`, SQLite y coincidencia de palabras. Antes de integrarlo con la
web compartida:

1. Pasar la API a FastAPI con modelos de entrada/salida Pydantic y publicar
   `/openapi.json` para los otros equipos.
2. Definir tablas y permisos en Supabase. Puntos y pedidos se consultan con
   identidad del visitante, no se agregan al índice público.
3. Sustituir la búsqueda lineal local por consultas de PostgreSQL. Mantener
   `source_id`, `updated_at`, `starts_at` y `ends_at` en las respuestas.
4. Configurar el proveedor de texto con una clave del servidor, y luego unir
   la interfaz de voz a `/chat` o a funciones de lectura equivalentes.

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
- Una clave de Gemini y su límite real en AI Studio; si no funciona, una clave
  de OpenAI con un presupuesto pequeño.
- URL pública de la web y del API, con una demo local ya cargada como respaldo.

Para el jurado, preparar tres recorridos: recomendar un regalo, mostrar un
producto para retiro presencial en PaseoYa y consultar puntos autenticados.
