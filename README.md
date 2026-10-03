# Paseito · integración con Jarvis

Esta rama reúne el último `main` de `daer-1701/Paseito` y el trabajo del
monorepo Paseo Aranjuez Digital, conservando ambos historiales Git.

## Aplicaciones disponibles

| Aplicación | Carpetas | Arranque |
|---|---|---|
| Paseito con avatar cochabambino, Gemini y FastAPI | `backend/`, `frontend/` | [Guía de Paseito](docs/paseito-original.md) |
| Jarvis con voz local GPU, catálogo conversacional y demo WhatsApp | `apps/jarvis-backend/`, `services/voice/` | [Arranque Windows y WSL2](docs/arranque-torre-windows.md) |

Son dos aplicaciones independientes dentro del mismo repositorio. Sus APIs,
sesiones y bases SQLite todavía no están unificadas. El frontend de Paseito
utiliza su backend FastAPI; el kiosco Jarvis utiliza su propia API. Ambos usan
el puerto 8000 por defecto: ejecuta uno a la vez o inicia Paseito con
`uvicorn app.main:app --port 8002` desde `backend/` y abre `http://localhost:8002`.

Los archivos `.env`, bases de datos locales y descargas temporales se mantienen
fuera de Git. Los ejemplos de configuración de ambos proyectos se conservan.

[Detalle de esta integración](docs/integracion-paseito.md).

---

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

Para la **torre Windows 11 + WSL2 + RTX 4070**, seguir el
[arranque con Docker y voz local](docs/arranque-torre-windows.md).
Una vez instalados Docker Desktop y el controlador NVIDIA:

```bash
bash scripts/start-tower.sh
```

Para desarrollo directo en la Mac:

```bash
cd apps/jarvis-backend
python3 -m pip install -r requirements.txt
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
El [plan de implementación futura](docs/implementacion-futura-jarvis.md) define
la transición hacia kioscos Raspberry Pi, un servidor central, voz local y el
uso posterior de Vercel y AWS.

El [estado actual de datos e investigación](docs/investigacion-datos-publicos.md)
documenta fuentes, horarios contradictorios, límites del catálogo y pendientes.
El [acceso móvil](docs/acceso-movil.md) explica el QR local y la pasarela opcional.

El [estado de requerimientos, catálogo demo y WhatsApp](docs/estado-requerimientos-y-whatsapp.md) detalla lo implementado y las consultas pendientes. El catálogo ficticio se habilita con `JARVIS_DEMO_CATALOG=1`; su procedencia se conserva en los datos y en la indicación general de modo demo.

La [demo conversacional y el respaldo de WhatsApp](docs/whatsapp-mvp-y-presentacion.md)
explican el flujo de tiendas → catálogo, horarios, promociones y el conector Twilio.
Abrir `http://localhost:8000/whatsapp/demo` para el respaldo local sin cuenta externa.
El alcance de los datos se indica una vez mediante “Modo demo”, sin repetirlo en cada respuesta.
