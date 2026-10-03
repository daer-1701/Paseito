# Cobertura del reto Jarvis — 3 de octubre de 2026

> Estado vigente: [auditoría del reto 2, requisitos y avance](auditoria-reto-jarvis.md). Este documento conserva información de entregas anteriores; sus conteos y pendientes pueden ser históricos.


Alcance autorizado: completar primero 1–5, luego 6–10, y documentar adicionales. El enunciado fuente es `docs/retos/Hackathon_By_Paseo_Aranjuez_Documento_Oficial_de_Retos.pdf`, sección Jarvis y entregables generales. Elegimos Jarvis; Points y PaseoYa son integraciones adicionales.

## Restricciones y arquitectura

SQLite almacena fichas y conversaciones. RAG significa recuperar evidencia antes de construir una respuesta; no exige una base vectorial. La recuperación actual es léxica con sinónimos, filtros de tipo y tiempo. La respuesta estricta compone atributos; la síntesis LLM es experimental y optativa. No presentamos esto como búsqueda semántica con embeddings.

No inventar precios, stock, promociones, agenda, aprobación del organizador ni planos. Datos públicos, importación y aprobación humana son estados distintos. Mantener voz GPU y volúmenes existentes. No se requiere cambiar a Supabase para cubrir este reto.

## Implementación y criterios de aceptación

| N.º | Trabajo | Evidencia de aceptación | Dependencia pendiente |
|---|---|---|---|
| 1 | Recuperación por intención y tipo | Eventos nunca devuelve un negocio homónimo; filtros fecha y vigencia | Embeddings opcionales, medir antes de agregar |
| 2 | Productos, servicios y descripciones | Contrato con negocio asociado; precio y stock desconocidos explícitos; descripción aprobada | Catálogo real y revisión de negocios |
| 3 | Promociones | Beneficio, condiciones, inicio, vencimiento y negocio obligatorios; futuras y vencidas excluidas | Promociones vigentes oficiales |
| 4 | Eventos | Nombre, inicio/fin con zona, lugar y descripción; hoy/mañana/fecha/próximos | Agenda oficial fechada |
| 5 | Horarios | Horario individual preferido, días especiales y madrugada; fallback general identificado | Horarios particulares/feriados |
| 6 | Ubicación | Piso, local, sector, referencia; origen configurable; no recorrido ficticio | Plano de baños, ascensores, accesibilidad y origen real |
| 7 | Conversación | Selección anterior, preguntas cortas, solicitudes múltiples y presupuesto conocido | Evaluar lenguaje natural y preferencias más amplias |
| 8 | Tarjetas | Negocio/producto/promoción/evento/FAQ con fechas, fuentes y precio desconocido | Contenido real para todas las tarjetas |
| 9 | Calidad del conocimiento | Revisión separada de actualización; borradores excluidos; limpieza de sesión | Responsable y proceso de revisión del Paseo |
| 10 | Presentación y demo | Presentación editable, arquitectura, guion, evidencia y limitaciones | Ensayar con micrófono y jurado simulado |

Entrega adicional del bloque 6–10: [detalle y alcance](cierre-tareas-6-10.md), [PowerPoint editable](entregables/jarvis-reto.pptx). Incluye ficha pública del destino, preferencias temporales y reporte administrativo de cobertura.

## Archivos y comprobaciones

Backend: `store.py`, `agent.py`, `knowledge.py`, `context.py`, `import_records.py`, `api.py`. Frontend: `web/kiosk/index.html`, `web/kiosk/js/evidence.mjs`. Datos públicos: `data/public-services.json`. Pruebas: `tests/test_knowledge.py` y `tests/evidence.test.mjs`.

Revisión prioritaria: selección de fecha en hora boliviana, promoción futura/expirada, madrugada del día anterior, follow-up sin reutilizar una selección eliminada, precio cero y desconocido, borradores no publicados, sesión eliminada. Verificar API real y tarjetas después de reconstruir únicamente Jarvis.

## Datos que debemos pedir al Paseo

1. Catálogo autorizado de productos/servicios con descripción, negocio, precio opcional y fecha del stock.
2. Promociones activas y futuras con condiciones y vencimiento.
3. Agenda con fecha, hora, lugar, descripción y cancelaciones.
4. Horarios de locales y excepciones por fecha.
5. Plano interior, accesos, baños, ascensores y punto del kiosco.
6. Persona responsable de aprobar cada fuente y frecuencia de revisión.

Los casos de prueba usan datos ficticios exclusivamente en bases temporales. No se cargan promociones ni eventos ficticios en la instancia del Paseo.
