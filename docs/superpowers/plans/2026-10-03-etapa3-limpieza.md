# Fase 3: limpieza y alcance del reto

Base f972a5f; fase aprobada por el usuario. Fuente: PDF oficial, secciones 4.6,
4.10, 5.7, 5.12, 6 y 7. Jarvis exige información y recomendaciones; inventario,
transacciones y canjes son integraciones adicionales, no mínimos de Jarvis.

1. Revisar texto y páginas relevantes del PDF; publicar matriz de alcance.
2. Actualizar documentación vigente, ramas de arranque y referencias obsoletas.
   Conservar informes históricos identificados como tales y datos fuente.
3. Retirar test de servidor eliminado, paquete de rutas vacío e importador
   antiguo que crea un catálogo separado. Archivar su fuente JSON; conservar
   avatar 2D, 3D y habla.js porque se usan. Conservar filtros de vigencia ya activos.
4. Corregir respuestas para reserva, pago, cancelación, retiro y pedidos sin
   introducir operaciones ni inventario externo. Mantener OpenAI/local.
5. Build y recorridos manuales, una revisión final de código y publicar rama.
   No añadir/ejecutar suites sin solicitud, conforme a instrucción del desarrollador.

No se borra historial comercial ni se reconfiguran servicios externos. Points real,
mapa interior y stock/PaseoYa permanecen pendientes de integración.

## Registro

Pasos 1–4 implementados. Build correcto; 1801 registros y voz GPU ready. Recorridos manuales de cinco operaciones, inventario y ubicación correctos; interfaz muestra reserva específica. No suites ejecutadas por instrucción del desarrollador. Revisión final de solo lectura completada: sin problemas críticos o importantes
inicialmente identificados. Blob original JSON conservado exactamente; no referencias
activas rotas. Se elevó la prioridad de dos hallazgos menores para cumplir el alcance
aprobado de coherencia documental y respuestas de operaciones: referencia histórica
rotulada vigente y variantes comunes Cómo pago/Puedo recogerlo. Una pasada de
corrección elimina la contradicción y cubre esas formas. No re-revisión ni suites;
recorrido manual de las variantes antes de publicar.

Paso 5 completado: build final correcto y variantes pago/recoger con respuesta específica observada. Cambios listos para commit y publicación. No hallazgos diferidos.
