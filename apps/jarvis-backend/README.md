# Biblioteca Jarvis de la aplicación Paseito

Esta carpeta contiene el agente común, catálogo SQLite, voz, analytics y adaptadores.
El servidor único es `backend/app/main.py`; la interfaz única es `frontend/`.

Desde la raíz del repositorio:

```bash
python -m pip install -r apps/jarvis-backend/requirements.txt
python scripts/serve.py
```

Se carga el `.env` raíz. El arranque Docker, GPU y portable está en la
[guía del equipo](../../docs/arranque-equipo.md). Estado y límites en
[versión única](../../docs/version-unica-estado.md).

`python -m jarvis.api` ya no existe. `python -m jarvis.bootstrap` conserva una
entrada compatible hacia el mismo FastAPI, sin segundo servidor.

## Pruebas históricas

Los archivos restantes de `tests/` se conservan como trabajo previo; no se han
certificado contra esta entrega. Se retiró `test_voice_http.py` porque importaba
el servidor HTTP eliminado. Migrar cobertura a FastAPI y ejecutar suites queda
para una solicitud explícita de verificación. Los builds y recorridos manuales
realizados se documentan en las entregas, sin afirmar que la suite pasa.

## Datos

Los bundles versionados de `data/` alimentan un solo catálogo. Se conservan precios,
fuentes, aportes de ambos equipos y tombstones editoriales. La fuente original del
compañero se archiva en `docs/historico/directorio-companero.json`; no es un catálogo
activo. No crear otra base o importador paralelo en `backend/`.
