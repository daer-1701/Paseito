# Estado de Jarvis, catálogo de demostración y WhatsApp

> Estado vigente: [auditoría del reto 2, requisitos y avance](auditoria-reto-jarvis.md). Este documento conserva información de entregas anteriores; sus conteos y pendientes pueden ser históricos.


Actualizado: 3 de octubre de 2026. Alcance: reto 2, Jarvis. Basado en el PDF oficial, secciones 4.6–4.10 y entregables de las páginas 12–13. No declarar completos los otros dos retos: PaseoYa y Points solo tienen propuestas y contratos iniciales.

## Actualización: demo conversacional

La entrega posterior añade ocho promociones con vigencia hasta el 11 de octubre, horarios de prueba para los calendarios faltantes y diálogo de tiendas → elección → catálogo paginado. Se muestran datos y condiciones sin recitar campos o avisos repetidos; el alcance se conserva en el indicador general “Modo demo”. El total local es ahora **1.661 registros**. Los horarios reales existentes prevalecen sobre el overlay.

El conector Twilio ya está implementado y existe [respaldo local](http://localhost:8000/whatsapp/demo); el usuario no tiene cuenta externa, por lo que **WhatsApp real todavía no está conectado**. Leer [MVP y presentación](whatsapp-mvp-y-presentacion.md) para el estado vigente, configuración y guion. Las brechas de datos reales, navegación e inventario/operaciones siguen pendientes. Las tablas siguientes describen la revisión anterior y distinguen carencias de datos oficiales; las promociones y horarios de prueba permiten demostrar sus flujos.

## Revisión anterior: catálogo y requerimientos

- Catálogo generado: **1.565 productos/servicios para 77 negocios**; 24 locales gastronómicos con 10 entradas cada uno y 53 negocios de otras categorías con 25 cada uno. Precio en bolivianos (`price_bs`), nombre, categoría y vínculo al negocio.
- Dos exclusiones: Century 21 y el consultorio de Minerva Montero. No se les atribuye un catálogo minorista. Los salones tienen servicios; Sky Games tiene experiencias de ejemplo.
- **Todo ese catálogo es ficticio y los precios son estimaciones escritas para la demo.** No representa el menú, marcas, stock ni precios reales de esos negocios. No confirma dietas, ingredientes, tallas o colores.
- `data_origin=synthetic_demo`, `price_scope=estimated_demo`. El agente anuncia la simulación, las tarjetas dicen “estimado” y enlazan la explicación `/catalog/demo`. La síntesis experimental no reescribe evidencia demo.
- Activación local explícita `JARVIS_DEMO_CATALOG=1`; predeterminado 0 en Compose y ejemplo de entorno. En 0 la búsqueda y las fichas excluyen los registros demo, aunque estos permanezcan en SQLite. No borrarlos para cambiar de modo.
- Generador reproducible: `scripts/generate-demo-catalog.py`. La carga se hace al arrancar por versiones; cambios editoriales más nuevos prevalecen. Cobertura por negocio en `docs/entregables/catalogo-demo-cobertura.json`.
- Búsqueda de productos restringida al negocio cuando se menciona su nombre completo. Presupuesto aplicado antes de limitar resultados; ausencia de precio no se trata como precio cero.
- Web adaptable: teléfono/tableta estrecha con pestañas Conversación y Resultados; tarjetas verticales completas, botones táctiles, foco visible, entrada de 16 px, adaptación al teclado y reducción de movimiento. Escritorio conserva avatar y paneles. Se añadieron ajustes para tableta ancha.
- Servicio local reconstruido; `/health` devolvió **1.653 registros**: 79 negocios, 1.569 productos/servicios (4 previos + 1.565 demo), 4 FAQ y 1 evento. OpenAI no configurado: recuperación léxica sobre SQLite y respuestas estructuradas. No hay búsqueda vectorial ni razonamiento generativo general activos.

## Requerimientos mínimos y brechas

| Requerimiento oficial | Estado actual | Qué falta y recomendación |
|---|---|---|
| Negocios: nombre, descripción, ubicación, horarios, productos, servicios | Parcial. 79 negocios; ubicación publicada y catálogo demo. Las descripciones de negocios requieren aprobación editorial para presentarse. | Revisar y aprobar descripciones; completar horarios individuales. 78 negocios carecen de calendario completo; no inferirlos del horario general del centro. Un piso y 69 locales sin dato en el informe anterior. |
| Productos y servicios | Demostrables con precios simulados; 4 servicios públicos previos. | Mantener etiqueta demo en presentación. Si luego llegan datos reales, cargar sus fuentes y fechas, sin mezclar estimaciones con ofertas reales. |
| Promociones: descuentos, beneficios y temporalidad | Motor implementado, sin promoción oficial vigente cargada. La fuente pública devolvió una lista vacía. | Para demostrar el flujo, preparar una campaña ficticia separada y rotulada, con inicio, vencimiento y condiciones; en producción depender de datos del Paseo. No presentar ofertas vencidas como vigentes. |
| Eventos: nombre, fecha, hora, lugar y descripción | Parcial: Bingo familiar del 4 de octubre 15:00–18:00 cargado. | Completar agenda. El contrato actual exige hora de fin aunque el reto no la exige; adaptar el esquema para “fin desconocido”, sin inventarlo, antes de cargar anuncios que solo tienen inicio. |
| Encontrar lugares del centro | Piso/sector/local cuando se publican; guía y QR. | Falta mapa real con accesos, ascensores, baños y tramos accesibles. La guía declara que no hay recorrido interior validado. |
| Recomendaciones según intención | Coincidencia de palabras, seguimiento de selección y preferencias limitadas de presupuesto/destinatario. | Mejorar comprensión semántica y aclaraciones para gustos, ocasión, restricciones y preguntas combinadas; añadir evaluación con ejemplos del reto cuando se autorice verificar. |
| Interacción | Chat web, voz y kiosco; web adaptable al móvil. | Conectividad desde teléfono real pendiente. HTTPS y acceso limitado para chat/voz móvil. Una interfaz responsive no acredita una app nativa publicada. |
| Entregables | Código, documentos, arquitectura propuesta y presentación existentes. | Actualizar PPTX con conteos actuales y simulación; preparar demostración de límites y comprobar entrega del código/presentación/arquitectura. |

El apartado 4.7 enumera alternativas de interacción (chat, voz, móvil, web, kiosco, WhatsApp…). No exige implementarlas todas. El reto acepta MVP; no exige producto comercial completo ni una base vectorial específica. Voz/avatar, mapa detallado, integración con Points/PaseoYa, analítica, personalidades, idiomas y panel administrativo son adicionales.

## Preguntas que hoy no se resuelven de forma fiable

| Ejemplo | Límite actual | Próximo paso recomendado |
|---|---|---|
| “¿Hay esa camisa en M y azul? ¿Cuál es el precio de venta hoy?” | Sin inventario real ni variantes; el precio mostrado es ficticio. | Mantener respuesta explícita de desconocido. Integración futura con catálogo del negocio. |
| “¿Qué tiendas están abiertas ahora? ¿A qué hora cierra TUC TOYS el domingo?” | No hay calendario completo por casi ningún negocio; horario del edificio no es el de cada tienda. | Completar calendarios y crear filtro de apertura por negocio. |
| “¿Qué promoción válida tengo hoy y qué condiciones tiene?” | No hay campaña vigente cargada. | Flujo demo etiquetado o fuente real del Paseo. |
| “¿Qué conciertos y películas hay hoy?” | Agenda incompleta. Anuncios de Rubik/cine/música no cargados por faltar hora de fin. | Permitir fin desconocido y cargar publicaciones con fecha clara. |
| “Tengo 45 minutos: camisa, café y reunión a las 5; dame la mejor ruta.” | Puede recuperar destinos; no planifica tiempos reales, distancias ni calendario. | Modelo de rutas/tiempos y planificador que pida hora/lugar de reunión. |
| “¿Dónde están los baños accesibles? ¿Cuánto cuesta el parqueo?” | Sin mapa interior validado, accesibilidad ni tarifa confirmada. | Plano y datos de servicios generales; no inventar caminos o tarifas. |
| “Un regalo para mi pareja, sin perfume, por menos de Bs 200.” | Presupuesto útil pero personalización y exclusiones semánticas limitadas; coincidencias pueden ser poco pertinentes. | Aclaraciones, filtros explícitos y recuperación semántica. |
| “Algo vegano y sin maní.” | El menú demo no prueba ingredientes o seguridad alimentaria. | Datos confirmados por restaurante; desconocido hasta entonces. |
| “¿Cuántos Points tengo? Canjea un premio.” | Sin identidad ni conexión a Points; solo respuesta de integración pendiente. | Autenticación y API de saldo/recompensas/canje con confirmación de operación. |
| “Compra esto, reserva mesa o consulta mi pedido.” | Sin motor de compra, pago, reserva ni conexión a PaseoYa. | Contratos reales, identidad y flujo de confirmación; separar consulta y operación. |
| “Respóndeme por WhatsApp.” | Canal sin configurar. | Elegir una API oficial y conectar el mismo agente; no duplicar la base. |

No se ha ejecutado una nueva suite de pruebas en esta entrega. Se observó la UI a 390, 768 y 1.024 px y la respuesta visual de productos Gap con precios demo; captura en `docs/entregables/catalogo-demo-movil.jpg`. La reconstrucción y salud no equivalen a validar todos los flujos ni un teléfono físico.

## WhatsApp: opciones y decisión

| Opción | Uso recomendado | Dependencias y límite |
|---|---|---|
| Meta WhatsApp Cloud API | Producción con canal propio, control de integración y sin intermediario de mensajería. | App Meta, configuración de número/cuenta, credenciales y webhook HTTPS. Cuenta/precios/políticas se deben revisar al habilitar. |
| Twilio: entorno de prueba / Sandbox | Recomendación para demostrar Jarvis rápidamente en el hackathon. | Cuenta Twilio, usuarios de prueba y webhook público. El Sandbox está en consola antigua; la nueva consola ofrece “Try out WhatsApp” para cuentas trial. No usar Sandbox como servicio comercial. |
| WhatsApp Business con atención manual | Contacto humano de respaldo. | Permite atención del negocio; no conecta por sí solo nuestro agente. Un enlace al chat no equivale a integración automática. |

Twilio Sandbox requiere que cada participante se una, usa número compartido, expira la incorporación a los tres días y limita envíos a uno cada tres segundos. La ventana de atención permite texto libre durante 24 horas tras el mensaje del usuario; fuera se requieren plantillas aprobadas. No asumir gratuidad ilimitada: Twilio y Meta tienen tarifas publicadas.

**Mi recomendación:** cerrar primero los mínimos de agenda/promociones/recomendaciones y la demo móvil; después Twilio para demostrar un canal adicional. Elegir Cloud API para el despliegue permanente. No automatizar WhatsApp Web mediante sesión de navegador como base de la integración.

### Diseño de integración propuesto, aún no implementado

1. Webhook dedicado recibe mensajes, valida firma y deduplica ID para evitar respuestas dobles.
2. Transformar número en identificador opaco de sesión; no poner teléfonos en las fuentes públicas ni compartir sesiones de clientes.
3. Invocar el mismo `chat()` y preservar aviso de catálogo demo, fuentes y límites.
4. Convertir respuesta en texto breve, opciones y enlace a ficha móvil HTTPS; respetar ventana de atención y plantillas.
5. Enviar con API del proveedor y registrar estado de entrega; manejo de fallos, límites y derivación a atención humana.
6. Points/PaseoYa requieren vinculación de identidad con consentimiento: conocer un número no autoriza ver saldos ni pedidos. Consultas públicas funcionan sin esos sistemas.

Fuentes oficiales consultadas el 3 de octubre de 2026:
- [Meta: plataforma y desarrolladores](https://whatsappbusiness.com/developers/developer-hub/).
- [Meta: Cloud API en su colección oficial](https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api?entity=request-13382743-bfd53137-07a0-4f88-a0bc-a15615a6dee2).
- [Twilio Sandbox: configuración y limitaciones](https://www.twilio.com/docs/whatsapp/sandbox).
- [Twilio: precios](https://www.twilio.com/en-us/whatsapp/pricing).

## Orden propuesto para cerrar el reto

1. Agenda con fin desconocido y promociones demo rotuladas: cubrir ambos mínimos sin atribuir datos inventados al Paseo.
2. Recomendación por ocasión y restricciones: aclarar y filtrar, mejorar búsqueda semántica.
3. Acceso móvil HTTPS y ensayo con teléfono/micrófono real; observar rendimiento/ruido del kiosco.
4. Actualizar presentación, arquitectura y guion con evidencias y límites actuales.
5. WhatsApp de prueba; después panel de edición y revisión humana.
6. Points, PaseoYa, navegación interior real y app nativa si el alcance posterior lo requiere.
