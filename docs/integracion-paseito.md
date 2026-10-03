# Integración de Paseito y Jarvis

## Origen

- Repositorio destino: https://github.com/daer-1701/Paseito
- Base incorporada: `main`, commit `f1e053ceab3bd6ce9371a45b26b63bf12da5eed9`.
- Trabajo local: monorepo `Timosboy/Hackaton`, rama previa `feat/jarvis-grounded-kiosk`.
- Rama de integración: `feat/integracion-jarvis-paseito-20261003`.

Los repositorios no compartían ancestros. Se guardaron los cambios locales en
un commit y se realizó un merge que conserva ambos historiales.

## Resolución

Los únicos conflictos fueron `README.md` y `.gitignore`:

- El README raíz ofrece acceso a las instrucciones de las dos aplicaciones.
  El README original de Paseito está íntegro en `docs/paseito-original.md`.
- `.gitignore` combina las exclusiones de ambos proyectos.
- `backend/` y `frontend/` conservan el código de Paseito sin modificaciones.
- `apps/`, `services/`, contratos, datos y documentación conservan el trabajo
  local de Jarvis, incluyendo el catálogo, horarios, promociones y WhatsApp.

## Alcance actual

El merge integra el código y los historiales en una sola rama. No adapta el
avatar de Paseito a la API de Jarvis ni unifica sus modelos de datos. Para ese
paso habrá que acordar un contrato común de chat, tarjetas, sesión y voz.

Para la presentación ya preparada de Jarvis, usar su arranque Docker y
`http://localhost:8000/whatsapp/demo`. Las credenciales reales de WhatsApp
continúan pendientes; el conector y la demo local están incluidos.

No se ejecutó una nueva batería de pruebas durante esta integración Git.
