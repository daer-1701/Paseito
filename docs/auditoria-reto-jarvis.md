# Auditoría del reto 2: Jarvis Paseo

> Informe histórico. El estado vigente está en [versión única](version-unica-estado.md) y el alcance del PDF en [fase 3](fase3-limpieza-y-alcance.md). Conteos, porcentajes, arquitectura y pendientes de este informe corresponden a su entrega original.


Fecha: 3 de octubre de 2026. Fuente: `docs/retos/Hackathon_By_Paseo_Aranjuez_Documento_Oficial_de_Retos.pdf`, 13 páginas. Se leyó el documento completo; esta matriz desarrolla el reto seleccionado (sección 4), la integración (6), requisitos generales (7), tecnologías (8) y entregables (9). Las secciones 3 y 5 describen otros retos y no se cuentan como obligaciones de Jarvis.

## Resultado y método

**Finalización estimada del MVP de Jarvis y sus entregables: 84%.** No es una nota oficial del jurado ni una medida de preparación para producción.

Se cuentan 29 unidades: 17 capacidades mínimas de 4.6, siete requisitos generales de 7 y cinco entregables de 9. Cada unidad vale lo mismo: completo = 1, parcial = 0,5, pendiente = 0. Un flujo funcional con datos de demostración puede obtener 1; esto no valida su contenido comercial como oficial. Los ejemplos y alternativas no se suman de nuevo. Los adicionales tienen un cálculo separado.

| Bloque | Puntos / máximo | Avance |
|---|---:|---:|
| Capacidades mínimas, 4.6 | 15 / 17 | 88% |
| Requisitos generales, 7 | 6 / 7 | 86% |
| Entregables, 9 | 3,5 / 5 | 70% |
| **MVP + entregables** | **24,5 / 29** | **84%** |
| Adicionales, 4.10, excluidos del MVP | 6 / 14 | 43% |

Fórmula: `100 × 24,5 / 29 = 84,48%`, redondeado a 84%. Este porcentaje puede bajar si un ensayo independiente descubre fallos. No se considera como completo un flujo presente exclusivamente en el backend Gemini separado de Paseito.

## Aplicación principal y evidencia

La aplicación principal es Jarvis: `apps/jarvis-backend/`, kiosco integrado, `compose.yaml` y servicio de voz local `services/voice/`. El avatar de `frontend/js/` incorporado desde Paseito se actualizó en el kiosco, junto con `habla.js` y Three.js. La carpeta `frontend/` y el backend FastAPI en `backend/` permanecen como implementación alternativa histórica; sus endpoints Gemini no alimentan la demo principal.

Observaciones de esta entrega:

- Jarvis reconstruido y arrancado; `/health`: `ok`, 1.661 registros.
- `/voice/status`: transcripción activa, síntesis GPU lista, streaming activo. No acredita un nuevo ensayo de micrófono/altavoz con ruido ni una medición de latencia.
- Navegador: avatar 3D actualizado, búsqueda de camisa, elección de Amore, catálogo y precios, conservando los flujos anteriores.
- Captura: `docs/entregables/avatar-jarvis-integrado.png`.
- Observaciones reproducibles sin credenciales: `docs/entregables/auditoria-reto-observaciones.json`, incluyendo los fallos encontrados y la respuesta posterior a las correcciones.
- WhatsApp: proveedor desactivado, demo local habilitada, entrega real no verificada.
- Consultas HTTP manuales de servicios, evento de mañana, parqueo, regalo, stock, Points y restricciones alimentarias.
- Se detectaron y corrigieron consultas de ubicación/descripción desviadas al catálogo. La solicitud avanzada de varias actividades continúa pendiente.
- No se ejecutó una nueva suite automatizada. Tampoco se certificó el arranque desde un clon limpio en otra PC.

Los datos incluyen 79 negocios, 1.569 productos/servicios (1.565 de demo y cuatro públicos), ocho promociones de demo, cuatro FAQ y un evento. Los horarios faltantes se cubren con un overlay de demo; los reales disponibles prevalecen. Las promociones de demo vencen el 11 de octubre de 2026. La información inventada conserva su procedencia y el indicador general de modo demo.

## 4.1–4.4: identidad, problema y objetivo (página 5)

Jarvis centraliza información del Paseo y proporciona búsqueda, conversación y evidencia específica. Nombre e inspiración no imponen un modelo concreto ni una interfaz de Iron Man.

Cada necesidad mencionada en 4.3:

| Necesidad | Situación | Qué falta / recomendación |
|---|---|---|
| Dónde comer | Funcional con categorías y catálogo de demo | Ampliar preferencias y validar menús. |
| Qué negocios están abiertos | Calendarios individuales y hora de Bolivia; demo para faltantes | Validar horarios y excepciones por feriados. |
| Dónde comprar un producto | Tiendas → selección → catálogo; filtros de precio | Stock real, variantes y catálogo comercial oficial. |
| Actividades de hoy | Filtro temporal; puede responder sin eventos para hoy | Completar agenda vigente; una ausencia en la base no implica que no existan actividades. |
| Promociones disponibles | Ocho campañas de demo, condiciones y vencimiento | Promociones oficiales y actualización diaria. |
| Dónde está una oficina | Directorio y ubicación cuando existe | Números de local y referencias faltantes; comprobación física. |
| Qué empresas existen | Directorio recuperable | Descripciones completas y revisión del responsable. |
| Dónde estacionar | FAQ pública sobre parqueo y validación | Entrada exacta, tarifa, capacidad y condiciones. |
| Qué eventos se realizarán | Un evento fechado: Bingo Familiar del 4 de octubre | Agenda completa, anuncios con hora de fin desconocida y cancelaciones. |
| Qué servicios hay | Servicios públicos y servicios de demo | Cobertura de oficinas/empresas y descripciones oficiales. |

## 4.5: ejemplos de conversación (página 5)

| Ejemplo | Estado | Recomendación |
|---|---|---|
| Hambre y comida rápida | Parcial: encuentra alternativas; no interpreta todas las preferencias ni tiempos de preparación | Preguntar preferencias y presupuesto; confirmar rapidez solo con datos del negocio. |
| Regalo para la pareja | Parcial: ofrece alternativas; poca personalización por ocasión/gustos | Pedir presupuesto y tipo de regalo; conservar respuestas en sesión. |
| Ubicación de tienda: piso, sector, local, referencia, mapa | Parcial: campos publicados y guía descriptiva; no mapa interior real | Completar plano y ubicaciones. El diagrama de pisos no es un mapa navegable. |

## 4.6: capacidades mínimas, cada elemento (página 6)

| ID | Requisito | Estado / puntos | Evidencia | Falta y recomendación |
|---|---|---|---|---|
| M01 | Negocios: nombre | Completo · 1 | 79 fichas y nombres en respuestas/tarjetas | Revisión de vigencia del directorio. |
| M02 | Negocios: descripción | Parcial · 0,5 | Categorías y texto de fuente; descripciones aprobadas cuando existen; consulta específica separada del catálogo | Completar descripciones de negocio y evitar respuestas genéricas de categoría. |
| M03 | Negocios: ubicación | Parcial · 0,5 | Piso/sector/local/referencia cuando están cargados; producto hereda ubicación del negocio | Investigación previa: un piso y 69 números de local faltantes. Validar físicamente. |
| M04 | Negocios: horarios | Completo para demo · 1 | Calendarios, día de semana, apertura actual y horarios nocturnos | Validar horarios individuales, feriados y excepciones; overlay no es información oficial. |
| M05 | Negocios: productos | Completo para demo · 1 | Catálogo de 77 negocios, precio BOB, negocio asociado, paginación | Datos reales, variantes y existencias. |
| M06 | Negocios: servicios | Completo para demo · 1 | Cuatro servicios/productos públicos y catálogos de servicios de demo | Ampliar oficinas, condiciones y precios oficiales. |
| M07 | Promociones: descuentos | Completo para demo · 1 | Campañas separadas y precio promocional vinculado cuando corresponde | Aprobación y fuente comercial real. |
| M08 | Promociones: ofertas | Completo para demo · 1 | Ocho campañas consultables por negocio | No confundir paquetes con precio por unidad. |
| M09 | Promociones: beneficios | Completo para demo · 1 | Beneficio y condiciones en atributos/respuestas | Catálogo de beneficios oficial. |
| M10 | Promociones temporales | Completo para demo · 1 | Inicio/vencimiento; exclusión de futuras/vencidas | Proceso de revisión diaria y nuevas campañas cuando expiren. |
| M11 | Eventos: nombre | Completo · 1 | Bingo Familiar | Mayor cobertura, no solo un evento. |
| M12 | Eventos: fecha | Completo · 1 | Fecha absoluta y filtros hoy/mañana | Adaptar anuncios incompletos y ampliar fechas. |
| M13 | Eventos: hora | Completo · 1 | Inicio 15:00 en hora boliviana | Hora de fin desconocida debe admitirse sin inventarla. |
| M14 | Eventos: lugar | Completo · 1 | El Club, Mercado Gastronómico, piso 3 | Ubicación comprobada y agenda completa. |
| M15 | Eventos: descripción | Completo · 1 | Texto de actividad y fuente | Contenido más detallado y cancelaciones. |
| M16 | Encontrar lugares dentro del Paseo | Parcial · 0,5 | Ficha de destino, piso, guía descriptiva y QR | Plano, accesos, rutas accesibles y recorridos comprobados. |
| M17 | Comprender intención y recomendar, no solo buscar «regalo» | Parcial · 0,5 | Sinónimos, categorías, alternativas, presupuesto y seguimiento | Evaluación de paráfrasis; ocasión/gustos; varias intenciones; recuperación semántica si resulta necesaria. |

## 4.7: formas de interacción, alternativas (página 6)

El documento permite escoger canales; no exige implementarlos todos. Se valora la experiencia conversacional.

| Canal enumerado | Estado en la aplicación principal |
|---|---|
| Chat | Funcional. |
| Voz | STT/TTS local en perfil GPU; ensayo presencial pendiente. |
| Chat + voz | Integrado en el mismo kiosco. |
| Aplicación móvil | Web responsive; sin aplicación nativa publicada ni validación en teléfono físico. |
| Aplicación web | Funcional. |
| Pantalla/kiosco inteligente | Avatar e interfaz listos; instalación física pendiente. |
| Bot WhatsApp | Conector Twilio preparado; demo local funcional; falta cuenta, HTTPS y entrega real. |
| Página web | Servida por Jarvis. |
| Experiencia de conversación | Tiendas → elección → catálogo, horarios y promociones; limitaciones en preguntas complejas. |

## 4.8: tecnologías de IA permitidas (páginas 6–7)

| Opción enumerada | Uso actual |
|---|---|
| Modelos de lenguaje | Síntesis OpenAI experimental y optativa; no configurada en la demo principal. |
| APIs de IA | OpenAI optativa; Gemini corresponde a la aplicación alternativa. |
| Modelos locales | Whisper/Kokoro para voz. |
| RAG | Recuperación de conocimiento antes de generar la respuesta. |
| Bases de conocimiento | Fichas tipadas y fuentes en SQLite. |
| Bases vectoriales | No implementadas; opcionales según el documento. |
| Reconocimiento de voz | Whisper local. |
| Text-to-Speech | Kokoro; adaptadores anteriores y respaldo del navegador. |
| Speech-to-Text | Whisper local. |
| Agentes inteligentes | Enrutamiento de intención, sesión, recuperación y respuestas estrictas. |
| Información específica del Paseo | Directorio público, fuentes y datos de demo separados. No responde solo con conocimiento genérico del modelo. |

SQLite almacena los datos; RAG describe el procedimiento. No son alternativas incompatibles. La recuperación actual es léxica con sinónimos; no se presenta como búsqueda vectorial.

## 4.9: conocimiento estructurado, cada elemento (página 7)

| Información enumerada | Modelo / situación |
|---|---|
| Empresas | `venue`, categoría/directorio; contenido incompleto. |
| Tiendas | `venue`; 79 negocios de diferentes tipos. |
| Oficinas | `venue`; datos y ubicaciones parciales. |
| Restaurantes | `venue` y catálogo asociado. |
| Productos | `product`, negocio, precio y procedencia. |
| Servicios | `product` para servicios; no inventario físico. |
| Horarios | Atributos de negocio + overlay de demo. |
| Promociones | `promotion`, condiciones y vigencia. |
| Eventos | `event`, fechas, lugar y descripción. |
| Ubicaciones | Piso/local/sector/torre/referencia; sin grafo de rutas. |
| Uso del conocimiento para responder | Recuperación filtrada; evidencia en respuestas y tarjetas. |

## 4.10: adicionales, cada elemento (página 7)

| ID | Adicional | Estado / puntos | Recomendación |
|---|---|---|---|
| A01 | Reconocimiento de voz | Completo · 1 | Ensayar ruido; evaluar VAD y transcripción durante el habla. |
| A02 | Respuestas por voz | Completo · 1 | Medir latencia y calidad en micrófono/altavoz finales. |
| A03 | Avatar animado | Completo · 1 | Última versión incorporada; comprobar también respaldo 2D en otro equipo. |
| A04 | Interfaz futurista | Completo · 1 | Mantener legibilidad, contraste y tamaños táctiles. |
| A05 | Mapas interactivos | Pendiente · 0 | Plano autorizado, marcadores y rutas. |
| A06 | Navegación interna | Pendiente · 0 | Grafo de recorridos, accesibilidad y comprobación física. |
| A07 | Recomendaciones personalizadas | Parcial · 0,5 | Ampliar gustos/ocasión/restricciones; no perfiles persistentes actualmente. |
| A08 | Integración Points | Pendiente · 0 | API e identidad autenticada; documentos/contratos no equivalen a conexión. |
| A09 | Integración PaseoYa | Pendiente · 0 | Catálogo/stock y enlaces primero; checkout en PaseoYa. |
| A10 | Historial de conversaciones | Completo · 1 | Sesión y caducidad 24 h, reinicio; no historial permanente de cliente. |
| A11 | Diferentes personalidades | Pendiente · 0 | Personalidades de conversación seleccionables; expresiones del avatar no cumplen este punto. |
| A12 | Soporte multilingüe | Pendiente · 0 | STT multilingüe no equivale a agente e interfaz multilingües. |
| A13 | Analítica de preguntas frecuentes | Pendiente · 0 | Endpoint/panel de demanda y consultas en Jarvis; existe en backend alternativo, no integrado. |
| A14 | Administración de conocimiento | Parcial · 0,5 | Ingesta/borrado y calidad por API; falta panel de revisión y auditoría de cambios. |

## 4.11: ejemplo avanzado (página 7)

Consulta revisada: camisa + café + reunión a las 5. La respuesta observada solo recomienda tiendas de camisas. **Parcial, pendiente**: descomponer objetivos, pedir ubicación/hora de reunión, manejar pendientes en sesión y proponer secuencia. No calcular «45 minutos» ni distancias sin horarios, duraciones y recorridos comprobados. Este ejemplo ilustra una capacidad avanzada; no se cuenta como una segunda obligación mínima.

## 6: integración entre retos (páginas 11–12)

El documento valora demostrar cómo podría integrarse posteriormente el ecosistema. La propuesta existe en `docs/adicionales-e-integraciones.md` y `packages/contracts/`; conexión real pendiente. El recorrido compra → Points → retiro presencial no está implementado por Jarvis. No se declaran completos Points o PaseoYa.

## 7: requisitos generales, cada elemento (página 12)

| ID | Requisito | Estado / puntos | Pendiente |
|---|---|---|---|
| G01 | Resolver claramente el problema seleccionado | Completo · 1 | Centralización y descubrimiento del Paseo; fortalecer cobertura. |
| G02 | Interfaz demostrable | Completo · 1 | Kiosco, chat y vista WhatsApp local. |
| G03 | Lógica funcional | Completo · 1 | Recuperación, catálogo, sesiones, vigencia y respuestas. |
| G04 | Arquitectura coherente | Completo · 1 | Jarvis principal: web/API/SQLite/voz; backend alternativo explícitamente separado. |
| G05 | Considerar implementación real | Parcial · 0,5 | Plan existe; falta datos aprobados, despliegue/red y operación del kiosco. |
| G06 | Buena experiencia de usuario | Parcial · 0,5 | Flujo natural y responsive; falta ensayo con usuarios, teléfono y consultas complejas. |
| G07 | Poder presentarse mediante demostración | Completo · 1 | Guion, prototipo y respaldo local disponibles; ensayo final pendiente. |

Seleccionar un reto: cumplido, Jarvis es el reto 2. El documento espera un MVP funcional y no exige un producto comercial terminado.

## 8: tecnologías (páginas 12–13)

Frontend, backend, base de datos e IA son de libre elección. HTML/JS, Python, SQLite, Whisper/Kokoro y RAG son compatibles con esta libertad. No se exige app nativa, proveedor de nube, LLM remoto ni base vectorial específicos.

## 9: entregables mínimos (página 13)

| ID | Entregable | Estado / puntos | Pendiente |
|---|---|---|---|
| E01 | Prototipo funcional con funciones principales | Completo · 1 | Jarvis principal operativo; comprobar instalación limpia independiente. |
| E02 | Código fuente | Completo · 1 | Repositorio Paseito, historial integrado y cambios versionados. |
| E03 | Presentación breve | Parcial · 0,5 | PPTX y guion disponibles; actualizar diapositivas al estado de avatar, 1.661 registros, demo y WhatsApp. |
| E04 | Demostración en vivo de funciones principales | Pendiente · 0 | Comprobaciones locales no equivalen a la exposición al jurado. Ensayo y demostración final. |
| E05 | Explicación de arquitectura | Completo · 1 | Código, documentos de arquitectura y separación de servicios disponibles. |

Elementos que debe explicar la presentación, revisados individualmente:

| Elemento | Situación |
|---|---|
| Problema | Documentado. |
| Solución | Documentada; actualizar la integración del avatar. |
| Usuarios | Visitantes/kiosco y responsables de información documentados. |
| Propuesta de valor | Centralización, descubrimiento y continuidad; reforzar diferenciación en las diapositivas. |
| Funcionamiento | Guion existente; actualizar conteos y ejemplos. |
| Arquitectura | Disponible; mostrar Jarvis principal y no mezclarlo con Gemini alternativo. |
| Tecnologías | Documentadas; explicar que no hay embeddings configurados. |
| Posible implementación | Plan de torre/kioscos; pendientes de red y operación. |

Elementos de arquitectura que exige explicar, revisados individualmente:

| Elemento | Implementación principal |
|---|---|
| Frontend | HTML/JS responsive, Three.js local y avatar actualizado. |
| Backend | Python, API HTTP, intención, recuperación y sesiones. |
| Base de datos | SQLite, fichas, preferencias, conversaciones y deduplicación. |
| APIs | Chat, voz, destino/QR, ingesta, calidad y WhatsApp. |
| IA | Whisper STT, Kokoro TTS, RAG léxico, respuesta estricta; LLM experimental opcional. |
| Servicios externos | Fuentes públicas/clima; descarga inicial de modelos; Twilio y OpenAI opcionales, no configurados en demo. |

## Qué no puede responder o ejecutar con garantías hoy

1. Existencias reales, talla/color disponibles, precios oficiales ni disponibilidad en tiempo real.
2. Comprar, cobrar, reservar, confirmar un pedido o consultar su estado real.
3. Saldo de Points, historial personal o canjear recompensas.
4. Ruta paso a paso desde el kiosco, distancias, ascensores/baños cercanos o ruta accesible validada.
5. Agenda completa o afirmar que no hay eventos porque no hay registros para la fecha.
6. Horarios oficiales de todos los locales, feriados, excepciones y datos faltantes de oficinas.
7. Garantizar ingredientes, alergias o ausencia de gluten.
8. Resolver toda la solicitud camisa + café + reunión y calcular tiempos reales.
9. Conversar en varios idiomas con interfaz y voz consistentes.
10. Recibir/responder mensajes en WhatsApp real mientras no se configure el proveedor.

## Orden recomendado para cerrar

1. **Entrega compartida:** marcar Jarvis como aplicación principal, guía vigente con URL/rama reales y arranque sin GPU; instalación limpia en otra PC.
2. **Comprensión:** corregir desvíos de intención y evaluar 30–50 consultas; descomponer peticiones combinadas sin inventar tiempos.
3. **Presentación:** actualizar PPTX y guion, ensayar voz y respaldo por texto, exponer límites como alcance del MVP.
4. **Contenido:** completar descripciones/agenda; mantener separación de datos de demo y datos oficiales.
5. **Móvil:** URL alcanzable, HTTPS y ensayo en teléfono; no basta configurar la variable de URL.
6. **Adicionales útiles:** panel de conocimiento y analítica de demanda antes de personalidades o multilingüe.
7. **Dependencias externas:** mapa real, API de stock/PaseoYa/Points y WhatsApp real requieren acuerdos o accesos que hoy no existen.

Esta auditoría sustituye como referencia de estado a los conteos y afirmaciones históricos de `plan-cobertura-jarvis.md`, `cierre-tareas-6-10.md`, `pendientes-jarvis.md` y partes de `estado-requerimientos-y-whatsapp.md`.
