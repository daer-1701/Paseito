# Investigación de datos públicos del Paseo

Fecha de consulta: 2026-10-03. Objetivo: completar Jarvis con evidencia pública específica de Aranjuez, manteniendo separados publicación, vigencia y aprobación humana.

## Resultado incorporado

El endpoint oficial [directorio de negocios](https://paseoaranjuez.com/stores) devolvió 70 entradas. Se conservó una instantánea en `docs/entregables/investigacion-publica/directorio-oficial-2026-10-03.json`. Se relacionaron las 70 con identificadores existentes; no se añadieron negocios duplicados por variantes de nombre. Se guardaron categorías, contactos públicos y seis enlaces de menú; estos últimos son referencias, no menús transcritos ni precios confirmados.

La carga fechada `apps/jarvis-backend/data/research-2026-10-03.json` enriquece 74 negocios en total y agrega tres fichas de servicios y un evento. Cada campo añadido tiene URL de respaldo; `observed_at` significa consulta de fuente, no aprobación. `review_status` permanece `sourced`. Los cambios editoriales con fecha posterior prevalecen sobre esta carga.

| Negocio | Información sustentada | Fuente y alcance |
|---|---|---|
| TUC TOYS | Piso 1, local 114 | [Contacto oficial](https://toys.tuctuc.com.bo/contacto/); también figura en primer piso del directorio. La página del negocio fue accesible mediante índice web; consulta HTTP directa devolvió 500 |
| Legend | Planta baja, locales 6 y 3 | [Sucursales de Impulse](https://www.impulse.bo/cms/page/view/page_id/7); se mantiene la forma publicada sin interpretar que sea un intervalo |
| Impulse | Piso 1, locales 101–102 | [Sucursales de Impulse](https://www.impulse.bo/cms/page/view/page_id/7) |
| Crocs | Nivel 2, local 13 | [Tiendas oficiales](https://crocs.com.bo/nuestras-tiendas) |
| Ópticas Pauker | Planta baja en directorio; lunes–sábado 10–22, domingo 11–21; contacto 77000207 | [Sucursales](https://opticaspauker.com/sucursales/), horario específico de Paseo Aranjuez; excepciones pendientes |
| LYNX / Samsung | Planta baja, local 9 | [Tiendas Samsung](https://samsung.com.bo/tiendas-samsung); horario contradictorio, no cargado como calendario |
| Rezzom Beauty | Torre 2, piso 5; lunes–sábado 09–19, previa cita | [Web del negocio](https://www.rezzombeauty.com/); domingo no declarado. Se guardó como texto parcial para evitar tratarlo como cerrado |
| Rezzom Beauty | Mechas/color, corte/estilismo y manicura/pedicura | [Servicios publicados](https://www.rezzombeauty.com/); tres fichas con costo y disponibilidad desconocidos |
| Gool Store | Piso 2 | [Canal del negocio](https://linktr.ee/gool.store) |
| El Cuarto | Piso 4 y horario del área | [Paseo](https://paseoaranjuez.com/); no atribuir ese horario a cada restaurante |

## Hallazgos que requieren revalidación

### Catálogo y precios

El [catálogo de TUC TOYS etiquetado Paseo Aranjuez](https://toys.tuctuc.com.bo/product-tag/paseo-aranjuez/) muestra productos y precios en el índice consultado. Ejemplos de investigación: Sorpresas Sneakers serie 1, Bs 169; figuras sorpresa Adopt Me, Bs 85 y marcada agotada; autos Hot Wheels BAS1, Bs 25 y marcada agotada.

La lectura directa del catálogo y contacto devolvió HTTP 500. No se cargaron estos valores como precios actuales. Además, un precio web y un botón de compra no acreditan inventario de la sucursal. Recomendación: recuperar la web o pedir lista actual al negocio, conservar fecha, alcance online/local y disponibilidad por sucursal antes de recomendar por presupuesto.

### Horarios contradictorios

Samsung publica para LYNX tanto lunes–viernes 10–20 como lunes–domingo 10–21. No hay base para elegir uno. Recomendación: confirmación de la sucursal y fecha efectiva.

Rezzom declara lunes–sábado y cita previa; no informa domingo. Se presenta el horario parcial sin afirmar estado abierto/cerrado para días no publicados. Pauker sí enumera toda la semana; feriados y modificaciones deben confirmarse.

### Promociones

La página de Totto denominada [Promociones Vigentes 26](https://bo.totto.com/promociones-vigentes-26) contiene una campaña que terminó el 31 de enero de 2026, con vales hasta el 31 de marzo. No es vigente el 3 de octubre. Las bases sí sitúan Aranjuez en piso 2, local 203, pero una campaña pasada no confirma por sí sola la operación actual de esa sucursal.

También aparecieron campañas Samsung de años anteriores y publicaciones secundarias de ferias pasadas. No se cargó ninguna promoción activa sin inicio, vencimiento, condiciones y alcance verificables.

### Eventos y redes

La web del Paseo anuncia funciones habituales de Cinema Lounge y tipos de actividad, sin una agenda fechada completa para hoy. Las consultas a Facebook/Instagram y a menús de Google Drive no permitieron leer contenido verificable suficiente mediante las herramientas usadas. Los resultados generales también mezclan Aranjuez de España, eventos históricos y fechas de rastreo con fechas de actividad; se descartaron.

La revisión adicional del JavaScript público de la web descubrió [el feed del Mercado](https://paseoaranjuez.com/instagram/mercado_gastronomico_bypaseo/8), [el feed de El Cuarto](https://paseoaranjuez.com/instagram/elcuartobypaseo/6) y [el endpoint de promociones](https://paseoaranjuez.com/promotions). Este último devolvió una lista vacía; no demuestra que cada negocio carezca de descuentos.

**Agenda hallada y carga:** Bingo Familiar, domingo 4 de octubre de 2026, 15:00–18:00, El Club/Mercado Gastronómico, piso 3. Se cargó como evento con fuente pública y sin aprobación humana. El año se contextualizó con la fecha de publicación del feed; la fecha de ingesta no se utilizó como fecha del evento.

**Anuncios incompletos conservados para revisión:** torneo de Rubik el sábado 3 a las 17:00; cine el sábado 3 (Demon Slayer 15:30, Weapons 19:00) y domingo 4 (Hotel Transilvania 14:30, Monsters Inc. 18:00). El Cuarto anuncia En Coma el sábado 3 y Luis Vaca el domingo 4; hay publicaciones relacionadas con horarios, pero faltan fines explícitos. No se inventaron duraciones para satisfacer el contrato actual, que exige inicio y fin. La feria del viernes 2 ya terminó y no se cargó como próxima.

Recomendación: confirmar duración/cancelación y permitir en una mejora del contrato eventos con hora de fin desconocida, sin confundir fecha publicada con hora de finalización. Los archivos del feed guardan metadatos y enlaces; no reproducen íntegramente las publicaciones.

### Plano y datos operativos

No se localizó plano interior oficial utilizable que identifique baños, ascensores, accesos y rutas accesibles. Documentos de terceros y planos de otros establecimientos no resuelven esta necesidad. Recomendación: plano autorizado y cinco recorridos comprobados desde la ubicación real del kiosco.

## Qué más queda por hacer

| Prioridad | Trabajo | Recomendación |
|---|---|---|
| Necesario para cerrar el contenido | Agenda/promociones vigentes, catálogo actual, horarios restantes, aprobación | Solicitar solamente los campos que siguen faltando; no pedir de nuevo lo ya respaldado públicamente |
| Necesario para la demo | Micrófono/altavoz con ruido real, teléfono/QR y recorridos | Ejecutar `docs/ensayo-presencial.md` y registrar resultados; el estado de salud del servidor no los acredita |
| Necesario para la entrega | Actualizar PPTX y README con el alcance actual; repasar explicación del RAG | Incorporar QR local, fuentes nuevas, límites de precios y estado de integraciones |
| Recomendado antes de operar | Actualizaciones del directorio y fuentes, conflictos y retiro de información | Revisar el importador: hoy agrega faltantes; no concilia por sí solo cambios y cierres de negocios. Proponer diferencias para revisión antes de reemplazar ubicación/horarios |
| Recomendado antes de operar | Edición administrativa, respaldo/restauración y evaluación de respuestas | API de carga e informe ya existen; falta una interfaz editorial y confirmar recuperación de datos. Evaluar paráfrasis, selección, presupuesto y vencimientos en la versión actual |
| Según modalidad móvil | URL de fichas en Wi-Fi o kiosco HTTPS | Resolver red y modalidad del teléfono; `compose.mobile.yaml` está preparado pero no publicado |
| Adicional | Points, PaseoYa y WhatsApp | Acordar contratos, responsables y accesos; no son integraciones activas |
| Opcional | Embeddings, analítica, multidioma y preferencias más amplias | Priorizar según evaluación de uso. SQLite y recuperación léxica permiten el prototipo RAG actual |

## Reproducibilidad y alcance

`scripts/prepare-public-research.py` prepara el JSON desde la instantánea y el archivo de revisión previo; no escribe la base activa. Es un compilador de esta investigación fechada, no un sincronizador automático. El arranque incorpora la carga por versión. El seed conserva las fechas explícitas para que una nueva instalación reproduzca los datos consultados.

Las páginas accesibles por HTTP se contrastaron y conservaron en `tmp/investigacion-publica/` (ignorado por Git). La ficha TUC usa evidencia primaria indexada y esa limitación se registra arriba. No se ejecutaron nuevas pruebas automatizadas por esta investigación. Falta comprobar las respuestas y dispositivos sobre esta versión, además de la revisión humana del contenido.

La carga final lleva la instancia a 88 fichas: 79 negocios, cuatro servicios/productos, cuatro FAQ y un evento. El reporte real (`docs/entregables/investigacion-publica/calidad-despues.json`) registra un piso ausente, 69 números de local pendientes, 78 horarios sin calendario completo, cuatro fichas sin fecha de fuente y 88 sin aprobación humana. Rezzom tiene texto de horario parcial y no cuenta como calendario completo. Los cuatro servicios/productos mantienen precio y disponibilidad desconocidos. No hay promociones cargadas.
