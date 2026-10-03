// URL del backend de Paseito.
// Vacío = mismo origen (FastAPI sirve el frontend en http://localhost:8000).
// Si el frontend se sirve aparte (p. ej. http://localhost:5500), apunta al puerto 8000 del mismo host.
// Para otro servidor, cámbialo aquí o abre la página con ?api=https://mi-backend.com
window.PASEITO_API =
  new URLSearchParams(location.search).get("api") ??
  (location.port === "8000" ? "" : `${location.protocol}//${location.hostname}:8000`);
