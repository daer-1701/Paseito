# Verificación de cobertura de Jarvis

3 de octubre de 2026. Cambios aplicados a la instancia local de Docker. Se conservan la base y los modelos en sus volúmenes.

Este informe describe la primera entrega. El bloque adicional 6–10 está documentado en [cierre-tareas-6-10.md](cierre-tareas-6-10.md). Sus cambios no están incluidos en el conteo histórico de pruebas de este informe.

## Evidencia observada

- 34 pruebas Python del backend aprobadas.
- 5 pruebas JavaScript de tarjetas y reproducción aprobadas.
- 6 pruebas del servicio de voz aprobadas, incluida cancelación durante inferencia simulada.
- Total: **45 pruebas aprobadas**, sin fallos en la ejecución final.
- `/health`: `ok`, 84 registros. `/voice/status`: transcripción, síntesis GPU y streaming disponibles.
- Ambos servicios `jarvis` y `voice`: saludables en `docker compose ps`.
- Voz real: `/voice/synthesize` respondió HTTP 200 con WAV de 115244 bytes; alrededor de 2,2 segundos para una frase corta completa. El navegador registró primer audio de una respuesta a los 176 ms en una comprobación local. Son mediciones puntuales, no un benchmark de ruido, carga ni hardware diferente.
- Interfaz: tarjeta de servicio de Sky Games con precio desconocido, fuente y piso; botón de guía disponible.
- HTTP: solicitud de camisa y café recupera dos opciones; «Guíame al segundo» conserva la segunda; `DELETE /chat/{session_id}` responde borrado exitoso.
- «¿Qué eventos hay hoy?» ya no devuelve el negocio HOY HAY. Eventos y promociones sin datos vigentes responden con ausencia de información confirmada.
- «¿A qué hora abre Crocs?» indica ausencia de horario individual y distingue el general.

## Correcciones adicionales encontradas al comprobar

Arranque conserva fichas editadas y cierra conexiones SQLite en Windows. Horarios nocturnos consideran el día anterior. Pisos numéricos activan mapa y guía; el contador del mapa ya no reemplaza el nombre del piso en la tarjeta. QR no crea una imagen visible sin haber cargado. Nombres largos se muestran completos y sombras de elevación se mantienen neutrales. La cancelación AnyIO espera el trabajo de inferencia antes de cerrar el generador y liberar el turno de GPU.

## Cómo repetir las pruebas

Desde `apps/jarvis-backend`, con Python instalado:

```powershell
python -m unittest discover -s tests -v
node --test tests/evidence.test.mjs tests/stream-player.test.mjs
```

Desde la raíz del repositorio, en Ubuntu/WSL con Docker:

```bash
docker compose run --rm --no-deps \
  -v "$PWD/services/voice:/tests:ro" -e PYTHONPATH=/service \
  voice python -m unittest discover -s /tests -v
docker compose ps
```

El conjunto de pruebas de voz usa motores simulados, no descarga modelos. La comprobación HTTP de síntesis sí utilizó el servicio GPU residente.

## Pendientes que impiden declarar el reto totalmente cerrado

1. Agenda fechada y promociones vigentes autorizadas: motor listo, contenido real aún ausente.
2. Catálogo amplio con productos, precios y servicios de cada negocio; solo hay un servicio específico cargado.
3. Horarios particulares, feriados y responsables de aprobación.
4. Plano y recorridos reales: baños, ascensores, acceso al parqueo y origen del kiosco.
5. Ensayo de voz con personas, micrófono y ruido del Paseo; ensayo de presentación.
6. Convertir la presentación editable a las diapositivas finales del equipo y completar evidencias de datos reales.

Points, PaseoYa, WhatsApp, panel visual, QR local y analítica están diseñados en `adicionales-e-integraciones.md`; no se presentan como integraciones activas. El QR actual enlaza una fuente pública mediante un generador externo. No se cargaron eventos ni descuentos ficticios en la instancia.
