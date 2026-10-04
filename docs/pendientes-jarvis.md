# Pendientes de Jarvis: estado al 2026-10-03

> Informe histórico. El estado vigente está en [versión única](version-unica-estado.md) y el alcance del PDF en [fase 3](fase3-limpieza-y-alcance.md). Conteos, porcentajes, arquitectura y pendientes de este informe corresponden a su entrega original.


> Referencia de aquella entrega: [auditoría histórica del reto 2](auditoria-reto-jarvis.md). El estado vigente está en [versión única](version-unica-estado.md).


## Actualización tras investigar fuentes públicas

Se enriquecieron 74 negocios y se añadieron tres servicios de Rezzom y un evento real: Bingo Familiar del 4 de octubre, 15:00–18:00. La instancia tiene 88 fichas. Faltan un piso, 69 locales y 78 horarios completos; cuatro negocios conservan fecha de fuente pendiente. Rezzom tiene horario parcial y Pauker calendario semanal. Ver [investigación y recomendaciones](investigacion-datos-publicos.md). Los feeds oficiales publican otros eventos con horario incompleto; el endpoint de promociones está vacío, sin que eso demuestre ausencia de descuentos en cada negocio.

El trabajo descrito abajo corresponde a la entrega previa a esta investigación; los conteos de esa comprobación son históricos.

## Trabajo realizado en esta entrega

- QR generado localmente en SVG; dependencia fija `qrcode==8.2` instalada en la imagen Docker. La URL sigue apuntando a la fuente oficial mientras no se configure acceso móvil.
- Pasarela opcional de fichas públicas preparada en `compose.mobile.yaml`; no iniciada ni publicada en LAN. Por defecto escucha en localhost.
- Solicitud lista para administración en [solicitud-datos-paseo.md](solicitud-datos-paseo.md), sin envío externo.
- Copia de 79 negocios para revisión y cinco plantillas CSV en `docs/entregables/datos-paseo/`. Los negocios exportados son borradores; la base principal no fue sustituida por esa exportación.
- Procedimiento de ensayo preparado en [ensayo-presencial.md](ensayo-presencial.md).
- Guion de presentación y documento de integraciones actualizados para explicar el QR local. El PPTX conserva la versión de la entrega anterior.

## Lo que requiere cerrar la entrega

| Pendiente | Recomendación | Qué permite cerrarlo |
|---|---|---|
| Datos comerciales | Priorizar ropa, café, reuniones y Sky Games, después completar directorio | Archivos/fuentes actuales y revisión del responsable |
| Agenda y promociones | Cargar toda la información vigente o confirmar su ausencia | Fechas, condiciones, lugar y fuente oficial |
| Horarios y ubicación | Validar por negocio; conservar desconocidos explícitos | Horarios de siete días, piso/local, excepciones y responsable |
| Rutas interiores | Recorrer cinco destinos desde el kiosco, incluyendo ruta accesible | Plano autorizado y comprobación presencial |
| Acceso móvil | Para demo, voz en PC y fichas por Wi-Fi | Confirmar red/modalidad, configurar URL y abrir desde teléfono |
| Ensayo de voz | Usar micrófono/altavoz reales y ruido representativo | Observaciones registradas en la hoja de ensayo |
| Points/PaseoYa/WhatsApp | Acordar responsables, contratos y entorno de desarrollo | Accesos autorizados y documentación; no conectado actualmente |

## Evidencia operativa de esta entrega

La imagen de Jarvis se reconstruyó y el contenedor arrancó. `/health` informó estado `ok`, 84 fichas y OpenAI no configurado. `/voice/status` informó transcripción activa, síntesis GPU, `ready=true` y streaming. La exportación contiene 79 negocios.

Estas comprobaciones de arranque no acreditan la calidad de las conversaciones, lectura del QR, conectividad LAN ni voz presencial. No se ejecutaron nuevas pruebas automatizadas ni se cargaron promociones/eventos ficticios. Para acceso móvil falta la respuesta sobre red y uso del teléfono; para datos y rutas faltan archivos y confirmación del Paseo.
