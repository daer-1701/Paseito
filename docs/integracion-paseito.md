> Documento histórico. El arranque vigente y la aplicación única están en [docs/arranque-equipo.md](arranque-equipo.md). El backend Gemini y las APIs duplicadas se retiraron en `feat/version-unica-openai`.

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

## Actualización: avatar reciente conectado a Jarvis

La entrega `feat/avatar-jarvis-auditoria-reto` incorpora los módulos recientes
`avatar3d.js`, `avatar.js`, `habla.js` y Three.js dentro del kiosco de Jarvis.
Usa su contrato `/chat` (`message`/`answer`), su voz `/voice/*`, catálogo,
horarios, promociones y WhatsApp local. La reproducción streaming conserva
sincronía por energía del audio; el audio completo utiliza visemas estimados
por texto y silencios, y la voz del navegador sigue eventos de palabra.
La alineación fonética es aproximada, no una medición exacta de fonemas.

Jarvis es la aplicación principal. El backend Gemini de Paseito se conserva
como alternativa; no es una dependencia del kiosco integrado.
[Arranque del equipo](arranque-equipo.md) y [auditoría](auditoria-reto-jarvis.md).

## Alcance del merge inicial

El merge integra el código y los historiales en una sola rama. No adapta el
avatar de Paseito a la API de Jarvis ni unifica sus modelos de datos. Para ese
paso habrá que acordar un contrato común de chat, tarjetas, sesión y voz.

Para la presentación ya preparada de Jarvis, usar su arranque Docker y
`http://localhost:8000/whatsapp/demo`. Las credenciales reales de WhatsApp
continúan pendientes; el conector y la demo local están incluidos.

No se ejecutó una nueva batería de pruebas durante esta integración Git.
