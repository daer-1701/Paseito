# Tareas 6–10: implementación y entrega

> Estado vigente: [auditoría del reto 2, requisitos y avance](auditoria-reto-jarvis.md). Este documento conserva información de entregas anteriores; sus conteos y pendientes pueden ser históricos.


## 6. Ubicación y continuidad

Se conservan piso, local, torre, sector y referencia. `/destination/{id}` devuelve una ficha pública adaptable al teléfono, con fuente y aviso de recorrido interior pendiente. No incluye sesión, preferencias ni historial. Si la ficha se elimina, rechaza o vence, la página deja de estar disponible.

`JARVIS_KIOSK_ORIGIN` describe el punto real de instalación cuando se confirme. `JARVIS_MOBILE_BASE_URL` configura una dirección que pueda abrirse desde teléfonos. Mientras esté vacía, el QR enlaza la fuente pública y la interfaz lo explica. El servidor actual escucha solo en localhost: configurar esa variable no publica el servicio. El QR ahora se genera localmente. La pasarela opcional `compose.mobile.yaml` permite publicar únicamente las fichas; instrucciones en `docs/acceso-movil.md`.

Pendiente de información del Paseo: plano, baños, ascensores, accesibilidad, ingreso al parqueo y cinco recorridos físicamente comprobados.

## 7. Conversación

La sesión mantiene selección, tema, presupuesto y destinatario infantil. «Busco un regalo» seguido de «Hasta 100 Bs» conserva el tema. Solo filtra por presupuesto productos con precio publicado; los negocios sin catálogo se presentan con la limitación explícita. Las consultas múltiples señalan las partes sin evidencia, en lugar de omitirlas. Horarios y clima no reemplazan la selección comercial anterior.

Preferencias e historial caducan a las 24 horas y se eliminan al reiniciar. No constituyen un perfil permanente ni autenticación. Las recomendaciones siguen siendo léxicas y basadas en categorías; hace falta evaluar paráfrasis y preferencias con visitantes reales.

## 8. Tarjetas

Negocios: ubicación, torre/sector y referencia. Productos/servicios: precio conocido o desconocido, negocio y disponibilidad publicada o desconocida. Promociones: beneficio, negocio, condiciones y vencimiento. Eventos: fecha en hora boliviana, lugar, descripción y fin. Las fichas diferencian revisión humana y mera disponibilidad de fuente.

## 9. Calidad del conocimiento

`GET /admin/quality` requiere el mismo token administrativo de ingesta. Devuelve conteos por tipo y una lista de fichas con campos pendientes: piso, local, horarios, precio, stock, revisión humana, fecha de fuente y expiración. Permite priorizar la carga sin inventar datos. Una fuente consultada no significa aprobación de administración.

Informe actualizado de la instancia: [informe de conocimiento](entregables/informe-conocimiento.md). Tras la investigación pública tiene 79 negocios, cuatro servicios/productos, cuatro FAQ y un evento fechado. No hay promociones cargadas. Faltan calendarios individuales completos para 78 negocios, número de local en 69 y piso en uno. Hay cuatro fichas sin fecha de fuente y 88 sin aprobación humana registrada. Rezzom tiene horario parcial publicado; Pauker calendario semanal. Detalle: `docs/investigacion-datos-publicos.md`.

Proceso recomendado: editor prepara borrador → responsable revisa fuente, alcance y fechas → publica `approved` con `verified_by`/`verified_at` → revisa agenda y promociones diariamente → rechaza o elimina cambios cancelados. El panel visual y auditoría detallada siguen en el documento de adicionales.

## 10. Presentación y demo

Entrega editable: `docs/entregables/jarvis-reto.pptx`, ocho diapositivas con problema, usuarios, funcionamiento, arquitectura, alcance, pendientes, demo y siguientes pasos. Guion de exposición y preguntas del jurado: `docs/presentacion-y-demo-jarvis.md`. El PPTX incluye notas para quien expone.

Ensayo pendiente: micrófono y altavoz reales, ruido del Paseo, recorridos físicos y tiempo asignado por organización. Presentar Points, PaseoYa y WhatsApp como integraciones propuestas. No afirmar que se confirmó una reserva, compra o canje.

Paquete para cerrar pendientes: `docs/solicitud-datos-paseo.md`, `docs/entregables/datos-paseo/`, `docs/acceso-movil.md` y `docs/ensayo-presencial.md`. La solicitud está preparada y no enviada; los 79 negocios exportados son borradores de revisión, no una nueva carga aprobada.

## Alcance de comprobación de esta entrega

Se reconstruye la instancia local para aplicar este bloque y se comprueba su arranque. Las 45 pruebas documentadas en la entrega anterior corresponden a aquella versión; no se presentan como pruebas ejecutadas sobre estos cambios adicionales.
