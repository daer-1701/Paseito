# Jarvis Paseo · backend MVP

Agente conversacional para Paseo Aranjuez. La búsqueda de negocios, eventos y
promociones sale de un catálogo actualizable; el proveedor de LLM es opcional y
configurable. Si no hay proveedor, el servidor sigue respondiendo con evidencia
mediante un generador local, útil para probar toda la integración.

## Inicio rápido

```bash
cd apps/jarvis-backend
python3 -m jarvis.seed
export JARVIS_INGEST_TOKEN="secreto-local-para-la-demo"
python3 -m jarvis.api
```

Servidor: `http://localhost:8000`. Solo usa la biblioteca estándar de Python
3.9 o superior. `JARVIS_DB` permite cambiar la ruta de SQLite. La semilla
incluida está marcada como **datos de demostración**; reemplácenla por datos
confirmados antes de presentarlos como información real.

## API

### `POST /chat`

```json
{"message":"Quiero comprar un regalo y tomar un café", "session_id":"demo-1"}
```

Devuelve `answer`, `sources`, `intent`, `suggestions` y `session_id`. Enviar el
mismo `session_id` conserva los últimos turnos para preguntas de seguimiento.
El servidor
solo entrega al modelo registros encontrados en la base; si no hay evidencia,
responde que no puede confirmarlo. El cliente puede mostrar las fuentes.

### `POST /admin/records`

Requiere `Authorization: Bearer <JARVIS_INGEST_TOKEN>`. Inserta o actualiza por
`id`. Una actualización aparece en la próxima consulta sin reconstruir todo el
índice. Tipos: `venue`, `product`, `promotion`, `event`, `faq`.

```json
{
  "id":"venue:cafe-ejemplo",
  "kind":"venue",
  "title":"Café Ejemplo",
  "text":"Cafetería con bebidas calientes y pastelería.",
  "attributes":{"floor":"2", "unit":"201", "category":"cafetería"},
  "source_url":"https://ejemplo.com/cafe",
  "updated_at":"2026-10-02T12:00:00-04:00",
  "expires_at":null
}
```

`DELETE /admin/records/{id}` retira información obsoleta. `GET /health`
verifica el servicio. Sin `JARVIS_INGEST_TOKEN`, los endpoints de administración
devuelven 401. Las promociones deben incluir `expires_at`.

## Integración con el equipo

- **PaseoYa**: enviará `venue`, `product` y `promotion` al endpoint de ingesta
  cuando se publiquen o modifiquen. Incluir `expires_at` en promociones; no
  exponer inventario no confirmado. El adaptador de lectura en vivo de stock
  se añade cuando el equipo cierre su contrato de API.
- **Paseo Points**: consultar saldo y canjes mediante una API autenticada en
  tiempo real. Los saldos personales nunca se indexan en el RAG compartido.
- **Frontend/voz**: ambos consumen `/chat`. El frontend puede convertir voz a
  texto y leer `answer` con TTS; una conexión de voz en tiempo real se puede
  añadir sin duplicar la lógica de búsqueda.

## Proveedor de LLM

El servidor usa un endpoint HTTP de chat compatible con mensajes (`system` y
`user`) si están configuradas `JARVIS_LLM_URL`, `JARVIS_LLM_MODEL` y
`JARVIS_LLM_API_KEY`. El endpoint debe aceptar `model`, `messages` y
`temperature`, y devolver `choices[0].message.content`. Las fuentes siguen
siendo seleccionadas por el backend. Sin estas variables, usa el generador
local. No se guardan claves en el repositorio.

## Límites deliberados del MVP

- No compra, reserva ni canjea: esas acciones requerirán autenticación y
  confirmación explícita.
- No presenta como reales los registros de demostración.
- No inventa precios, disponibilidad ni horarios cuando faltan en las fuentes.
