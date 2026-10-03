# Solicitud de información para completar Jarvis

Borrador listo para compartir con administración; no se ha enviado. Fecha: 2026-10-03.

Hola, estamos preparando Jarvis para el reto del Paseo Aranjuez. Para que la demostración responda con información real y vigente, solicitamos estos datos y una persona responsable de revisarlos:

| Información | Contenido solicitado | Prioridad y criterio de cierre |
|---|---|---|
| Directorio | Nombre, categoría, descripción, productos/servicios, piso, número de local, torre/sector y referencia | Alta: revisar los 79 negocios; completar cuatro pisos y 72 números de local ausentes |
| Horarios | Los siete días, descansos y excepciones de feriados por negocio | Alta: los 79 negocios necesitan horario individual o confirmación explícita de que sigue pendiente |
| Catálogo | Productos/servicios representativos, negocio, descripción, precio en Bs y disponibilidad con fecha | Alta: precio y stock solo cuando estén confirmados |
| Promociones | Negocio, beneficio, condiciones/exclusiones, inicio y vencimiento con hora boliviana, enlace o material oficial | Alta: todas las promociones vigentes; confirmar explícitamente si no hay ninguna |
| Eventos | Nombre, descripción, inicio y fin, lugar/piso/local, condiciones de acceso y fuente | Alta: agenda de las próximas semanas; confirmar explícitamente si está vacía |
| Orientación | Plano autorizado, ubicación del kiosco, ascensores, escaleras, baños, parqueo y accesibilidad | Alta: cinco recorridos comprobados físicamente, incluyendo uno accesible |
| Revisión | Nombre/cargo del responsable, fecha de aprobación y canal para comunicar cancelaciones/cambios | Alta: la fuente pública consultada no equivale a aprobación humana |
| Integraciones | Responsables y documentación de Points y PaseoYa; contacto de atención y titular del número de WhatsApp Business | Siguiente etapa: contratos y entorno de desarrollo, sin credenciales en archivos públicos |

Agradecemos Excel, CSV o JSON y los materiales oficiales que respaldan cada dato. No necesitamos información personal de visitantes. Si algún campo no está disponible, conservarlo como pendiente; no completar horarios, precios ni rutas por aproximación.

## Paquete de trabajo

`docs/entregables/datos-paseo/negocios-para-revision.json` contiene una copia de los negocios existentes marcada `draft` para revisar. Es un documento de trabajo: **no cargar directamente**, porque reemplazaría las fichas públicas por borradores. Se conservan los identificadores para relacionar productos y promociones.

Los CSV de la carpeta son plantillas vacías. Se pueden abrir en Excel. No son importables directamente por la API; convertir las filas confirmadas al contrato JSON de `packages/contracts/knowledge.md`. Omitir campos desconocidos, en lugar de sustituirlos por cero o por texto ficticio.

Antes de cargar: actualizar `updated_at` con zona horaria; contrastar el material; registrar `review_status=approved`, `verified_by` y `verified_at` solo con aprobación real; conservar fuente y fecha de observación; verificar `venue_id`; revisar ventanas temporales. Usar `python -m jarvis.import_records archivo.json` en el backend. Cargar datos reales en la base principal; ejemplos de eventos y promociones deben permanecer fuera de ella.

## Recomendación

Pedir primero un conjunto pequeño pero completo: negocios de ropa, café y reunión para la demo, su ubicación y horario, servicios de Sky Games, y la agenda/promociones vigentes. Después completar el directorio. Es más útil mostrar un recorrido sustentado de principio a fin que ampliar respuestas con datos sin confirmar.
