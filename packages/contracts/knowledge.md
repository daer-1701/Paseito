# Contrato de conocimiento público v1

Implementación: `apps/jarvis-backend/jarvis/store.py::validate_record`. Transporte actual: `POST /admin/records` con `Authorization: Bearer <JARVIS_INGEST_TOKEN>`. Para un lote: `python -m jarvis.import_records archivo.json`, desde el backend. El archivo es una lista de fichas; validar todas y sus relaciones antes de cargar. No incluir secretos ni datos personales.

## Sobre común

`id`, `kind`, `title`, `text`, `updated_at` obligatorios. `kind`: `venue`, `product`, `promotion`, `event`, `faq`. `source_url`: enlace HTTP(S) real que respalda la ficha. `attributes`: objeto. `expires_at`: opcional excepto promociones. Todos los timestamps incluyen zona horaria, por ejemplo `2026-10-03T18:00:00-04:00`. Una versión anterior no pisa una posterior; una versión igual puede actualizarse, por lo que el editor debe incrementar `updated_at` al editar.

`text` sirve para recuperación, no se repite como respuesta estricta. Los hechos presentados vienen de atributos. `updated_at` es versión de carga, no aprobación. `attributes.observed_at` indica lectura de fuente. `review_status`: `sourced` (por defecto), `draft`, `rejected`, `approved`. Borradores y rechazados no se recuperan. Aprobación requiere `verified_at` con zona y `verified_by` responsable. El importador del directorio acredita observación de una fuente, no aprobación humana.

## Atributos por tipo

| Tipo | Obligatorios adicionales | Opcionales útiles |
|---|---|---|
| venue | Ninguno; no inferir campos ausentes | category, floor, unit, tower, area, reference, hours; description/products/services se presentan con aprobación |
| product | venue_id | venue_name, category, price_bs numérico no negativo, stock, floor, unit, description |
| promotion | venue_id, starts_at, benefit, terms; expires_at en sobre | venue_name, floor, unit |
| event | starts_at, ends_at, location, description | floor, unit, venue_id |
| faq | answer recomendado | scope, floor, unit, reference |

Productos también representan servicios con un negocio asociado. Ausencia de precio o stock significa **desconocido**, no cero ni disponible. `products` y `services` en negocios son listas de cadenas. La carga por lote verifica que `venue_id` apunte a un negocio existente o incluido en el mismo lote. La API de ficha individual valida campos, pero el editor debe cargar primero el negocio asociado.

## Horarios

`hours` usa claves `0` lunes a `6` domingo. Cada día es lista de intervalos `[["10:00","22:00"]]`; lista vacía significa cerrado. `special` es un mapa de fechas ISO a listas de intervalos; prevalece sobre horario semanal. Ejemplo:

```json
{"0":[["10:00","22:00"]], "4":[["12:00","01:00"]], "special":{"2026-12-25":[]}}
```

El intervalo que termina antes de su inicio cruza medianoche. Un día sin entrada se considera cerrado por el contrato: cargar los siete días para evitar omisiones. Usar días especiales para feriados confirmados. Sin un horario individual se explica su ausencia y se informa el horario general con su alcance.

## Vigencia y consultas

Promoción: `starts_at <= ahora < expires_at`. Evento: `ends_at > ahora`; hoy/mañana usa intervalos de fechas en `America/La_Paz` y considera eventos que cruzan medianoche. Próximos se ordenan por inicio. Cancelar un evento eliminándolo con API administrativa o marcándolo `rejected`, conservando auditoría en el futuro panel.

`sources` de `/chat` incluye id, kind, title, attributes, source_url, updated_at y expires_at. La interfaz mapea el tipo al diseño de tarjeta correspondiente. Nunca exponer identidad de clientes, saldos, pedidos, tokens ni grabaciones mediante este contrato.

## Catálogo sintético de demostración

Productos/servicios autorizados para la demo usan `data_origin=synthetic_demo`, `price_scope=estimated_demo` y `source_type=demo_catalog`. `price_bs` es una estimación en BOB, sin afirmar stock. `contains_demo_data` en `/chat` informa si la evidencia seleccionada incluye simulación; la interfaz debe mostrar el alcance general del modo demo, sin repetirlo en cada respuesta. El canal Twilio lo indica en el primer contacto. `JARVIS_DEMO_CATALOG=0` excluye esos registros de la búsqueda y fichas. No implica borrarlos de SQLite. La URL `/catalog/demo` explica la procedencia ficticia. Nunca reinterpretar este origen como publicación oficial o aprobación del negocio.

Los horarios de prueba se aplican como overlay de lectura (`hours_origin=synthetic_demo`, `demo_fields=["hours"]`), solo cuando no hay calendario real. No cambian la fuente ni el registro persistido del negocio. Una promoción con `product_id` puede aportar precio efectivo a su producto durante la vigencia, manteniendo `catalog_price_bs`, `promotion_id` y `promotion_expires_at`; no aplicar el precio de un paquete a una unidad.
