# Fase 3: limpieza y alcance confirmado del reto

Fecha: 2026-10-03. Base: f972a5f. Rama: feat/etapa3-limpieza.
Fuente revisada: Hackathon_By_Paseo_Aranjuez_Documento_Oficial_de_Retos.pdf,
13 páginas, copia local en docs/retos/. Texto completo leído y páginas relevantes
renderizadas para contrastar secciones y listas. El PDF original no se modificó.

## Qué exige Jarvis y qué es integración adicional

| Capacidad | Clasificación y fuente |
|---|---|
| Informar negocios, descripción, ubicación, horarios, productos y servicios | Mínimo de Jarvis, 4.6, p. 6 |
| Promociones, eventos y recomendaciones según intención | Mínimo de Jarvis, 4.6, p. 6 |
| Ayudar a encontrar lugares | Mínimo de Jarvis, 4.6, p. 6. Piso/sector/local/referencia/mapa aparecen como ejemplo en 4.5, p. 5 |
| Chat, voz, web, móvil, kiosco o WhatsApp | Formas que los participantes pueden implementar, 4.7, p. 6. No exige implementar todas |
| Avatar, mapa interactivo y navegación interna | Adicionales valorados de Jarvis, 4.10, p. 7 |
| Integrar Points y PaseoYa | Adicionales valorados de Jarvis, 4.10, p. 7 y sección 6, pp. 11–12 |
| Stock/disponibilidad y administración de inventario | Funciones del reto PaseoYa: 5.3, p. 8; 5.7, p. 10; control de inventario y reserva de productos también en 5.12, p. 11 |
| Crear pedidos, pagar y confirmar retiro/entrega | Reto PaseoYa: 5.5 y 5.7, pp. 8–10; estados y validación de retiro, 5.8–5.9, p. 10 |
| Acumular puntos y canjear recompensas | Reto Points: 3.6 y 3.8, pp. 2–3 |
| Reservar mesas/salas, cancelaciones y devoluciones desde Jarvis | Extensiones propuestas por nosotros; no figuran como mínimos de Jarvis. Reserva de productos sí figura como adicional de PaseoYa |
| Prototipo funcional, código, presentación, demo y arquitectura | Entregables generales, sección 9, p. 13 |

La sección 7 (p. 12) pide elegir un reto y un MVP funcional; no exige terminar un
producto comercial. La sección 6 valora demostrar cómo se integraría posteriormente
el ecosistema. Por tanto, inventario real y operaciones son pendientes de integración,
no requisitos mínimos incumplidos del reto Jarvis. Su ausencia limita respuestas
como Queda talla M o Ya puedes recoger tu pedido, pero no obliga a construir otro
marketplace para completar nuestro reto.

## Cambios de limpieza

- README raíz y guía de arranque apuntan a la rama actual, al servidor FastAPI único
  y al acceso Points temporal de etapa 2.
- Estado de versión única actualizado a 1801 registros y límites actuales.
- README antiguo de la biblioteca sustituido por instrucciones hacia el servidor
  vigente. Se retiraron comandos de arranque del servidor que ya no existe.
- Auditoría, pendientes iniciales, propuesta original del compañero y entrega de
  etapa 1 se conservan identificados como históricos; no usar sus porcentajes
  anteriores para calificar esta versión.
- Se retiró test_voice_http.py, que importaba Handler/ThreadingHTTPServer eliminados.
  No se añadieron ni ejecutaron tests; las demás pruebas históricas se conservan
  sin afirmar cobertura vigente.
- Se retiraron el paquete vacío backend/app/rutas y el importador anterior del
  directorio, que generaba un catálogo separado con supuestos de horario.
- El JSON original del compañero se conserva en docs/historico/directorio-companero.json.
  Su información útil permanece en los bundles canónicos; no se elimina su aporte.
- Respuestas de reserva, pago, cancelación/devolución, retiro y pedido diferenciadas;
  no remiten indiscriminadamente a consultar un pedido ni afirman ejecutar acciones.
- Avatar 2D, avatar 3D y habla.js conservados porque ambos avatares usan los visemas;
  el 2D es el respaldo de la interfaz.
- Los filtros existentes ya excluyen promociones vencidas/futuras, eventos finalizados
  y borradores. Se conserva su historial y no se purga la base comercial.

## Pendientes por prioridad

1. Revisión comercial del conocimiento: horarios, pisos/locales faltantes, ofertas,
   agenda vigente y fuentes; resolver conflictos con administración.
2. Ensayo del MVP en entorno de presentación: micrófono, altavoz, dispositivo,
   conversación natural y fichas accesibles desde teléfono.
3. OpenAI: configurar clave local para comprobar respuestas del proveedor; hoy
   responde el respaldo local. No se cambia de proveedor ni se introduce Gemini.
4. Integraciones adicionales acordadas: Points real, mapa interior, inventario
   y PaseoYa, WhatsApp real y eye tracker físico. Mantener sus responsables y contratos.
5. Entregables: mantener presentación y demo coherentes con capacidades reales.

## Evidencia de entrega

Build de jarvis completado conservando datos y voz GPU. Health: ok, 1801 registros.
Voice status: ready true. Recorridos manuales HTTP: reserva, pago, cancelación,
retiro y consulta de pedido devuelven sus mensajes específicos; stock explica que
no consulta existencias; Cayenna sigue ubicada en cuarto piso, sector El Cuarto.
Navegador: mensaje de reserva visible con avatar y controles funcionales.
Captura: entregables/fase3-reservas.png. No se ejecutaron suites automáticas ni
se declara un nuevo porcentaje sin una auditoría actualizada.

Revisión final de código completada; directorio original preservado sin cambios de contenido y sin consumidores activos rotos. Se corrigieron también la referencia histórica rotulada vigente y las variantes Cómo pago/Puedo recogerlo, comprobadas manualmente con respuesta order específica.
