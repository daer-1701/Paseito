# Implementación de la versión única

Especificación: `docs/definicion-version-unica.md`. Base: `paseito/main` 28b9729.
Rama: `feat/version-unica-openai`. Ejecución directa con executing-plans.

1. Unificar catálogo: importar descripciones, contactos, FAQ y agenda del compañero, conservar IDs y registrar conflictos. SQLite será el almacén único.
2. Unificar agente: OpenAI Responses con herramientas de lectura, contexto persistente, límite de tiempo y respaldo local. Cubrir solicitudes compuestas. WhatsApp llama al mismo servicio.
3. Unificar API FastAPI: catálogo, chat, voz, calidad, CRUD protegido, analítica común y destinos móviles. Eliminar servidores y agentes duplicados activos.
4. Conservar Points público con TLS, caché limitada y vigencias; cerrar consultas personales hasta contar con identidad verificada. Estímulos solo saludan en bienvenida.
5. Frontend único responsive con último avatar, tarjetas Points, cancelación de voz, demo WhatsApp y estímulo manual. Añadir panel administrativo protegido.
6. Unificar Compose GPU/portable y guías. Arranque manual y revisión de recorridos; sin agregar ni ejecutar suites de pruebas, conforme a instrucciones de esta sesión.
7. Revisar cambios, commit, push a la rama nueva y PR adjunto. No fusionar main.

## Registro

- Inicio: rama creada sobre el último main; cambios previos conservados.
- Decisión: mantener `jarvis` como biblioteca de datos y voz; FastAPI en `backend/app/main.py` es el único servidor. Evita reescribir código que ya funciona.
- Decisión: credenciales e integraciones externas se reportan por su estado real. El saludo por mirada no consulta fichas ni almacena datos biométricos.
- Catálogo: 74 lugares del compañero integrados; tres FAQ divergentes en draft, 1.681 registros en el arranque.
- Agente/API/frontend: implementados; contrato único, sesión común, OpenAI con herramientas y respaldo local; Gemini y servidores duplicados retirados.
- Points/WhatsApp/estímulos/admin: implementados con respaldo público demo, privacidad, TLS, deduplicación y protección administrativa.
- Arranque observado: torre GPU y contenedor portable con base vacía. Recorridos manuales de compra exploratoria, consulta compuesta, WhatsApp, Points y saludo.
- Revisión final con contexto fresco: corregidos reinicio tras tombstones, frescura Points, STT antiguo, bloqueo entre visitantes WhatsApp y divergencia de opciones. No se ejecutaron suites por la instrucción de la sesión; la suite histórica de HTTP necesita migración.
- Decisión adicional: Points sin credenciales dispone de programa público demo identificado; nunca se inventa un saldo personal. En móvil se muestran los pisos en las tarjetas para dejar espacio al catálogo.

- Cierre: cancelación de captura y reconocimiento por generación de conversación; imagen móvil guardada en `docs/entregables/version-unica-mobile.png`. Build final y recorrido móvil observados.
