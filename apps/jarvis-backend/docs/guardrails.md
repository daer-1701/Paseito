# Guardrails de Jarvis

## Contrato de una respuesta pública

1. Una ficha necesita `source_url` HTTP(S), marca de tiempo y un tipo conocido
   antes de entrar al índice.
2. Las promociones requieren `expires_at`; la búsqueda descarta las vencidas.
3. El buscador devuelve como máximo tres fichas de evidencia al agente y al
   cliente. Una respuesta sin fichas usa el mensaje de falta de confirmación.
4. El modo predeterminado (`strict`) no ejecuta un LLM. Construye la respuesta
   desde atributos tipados como `category`, `floor` y `unit`; no repite el campo
   libre `text` del feed.
5. La UI escapa todo contenido de una ficha antes de insertarlo en el DOM y
   vincula cada tarjeta a su fuente.

## Ingesta y datos privados

Los endpoints `POST /admin/records` y `DELETE /admin/records/...` necesitan
`JARVIS_INGEST_TOKEN`. El token vive solo en el servidor. Paseo Points y
PaseoYa deben resolver saldo, pedidos y acciones transaccionales con la sesión
autenticada de cada producto: esos datos no entran al índice público.

## OpenAI opcional

`JARVIS_RESPONSE_MODE=experimental` habilita síntesis con OpenAI. La
instrucción del modelo ordena tratar el texto recuperado como datos y jamás
como instrucciones. Mantener este modo apagado para información que aún no
haya sido evaluada con preguntas reales. La prueba automatizada verifica que
el modo estricto no llame al LLM y que texto malicioso en una ficha no aparezca
en la respuesta pública.
