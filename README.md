# Paseo Aranjuez Digital

Monorepo del equipo para la Hackatón by Paseo Aranjuez. Agrupa los tres retos
con una aplicación separada para cada uno y contratos compartidos para que se
puedan integrar sin acoplar sus implementaciones.

## Estructura

```text
apps/
  jarvis-backend/   API conversacional y búsqueda de conocimiento
  paseoya/          Marketplace y retiro presencial
  paseo-points/     Fidelización y recompensas
packages/
  contracts/        Contratos API y modelos compartidos
docs/
  retos/            Enunciado oficial
```

Jarvis está inicializado en `apps/jarvis-backend`. PaseoYa y Paseo Points tienen
un README inicial para que sus responsables agreguen ahí sus aplicaciones.
Los contratos entre equipos se documentan en `packages/contracts`.

## Correr Jarvis

```bash
cd apps/jarvis-backend
python3 -m jarvis.seed
export JARVIS_INGEST_TOKEN="un-secreto-para-la-demo"
python3 -m jarvis.api
```

Abrir `http://localhost:8000` para probar el chat y la voz local. Consulta el
[README de Jarvis](apps/jarvis-backend/README.md) para preparar Whisper y Piper
en otra máquina.

Consulta el README de cada aplicación para sus detalles. El repositorio no fija
un lenguaje ni framework común a las tres aplicaciones; cada equipo puede
escogerlos y compartir únicamente los contratos de integración.

La [recomendación técnica](docs/decisiones-tecnicas.md) propone un stack y los
acuerdos de datos que el equipo debe cerrar antes de integrar la demo.
La [propuesta de Jarvis presencial](docs/propuesta-jarvis-presencial.md) describe
la experiencia, el servidor central, las garantías sobre fuentes y la
demostración para el jurado.
