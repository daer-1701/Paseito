#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
command -v docker >/dev/null || { echo 'Instala Docker Desktop y activa la integración con Ubuntu WSL2.' >&2; exit 1; }
docker compose version >/dev/null
docker info >/dev/null || { echo 'Abre Docker Desktop antes de iniciar Jarvis.' >&2; exit 1; }
if [[ ! -f .env ]]; then
  command -v openssl >/dev/null
  umask 077
  cp .env.example .env
  token=$(openssl rand -hex 32)
  sed -i "s/^JARVIS_INGEST_TOKEN=$/JARVIS_INGEST_TOKEN=$token/" .env
fi
docker compose config --quiet
echo 'Verificando acceso a la GPU NVIDIA desde Docker…'
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
echo 'Construyendo e iniciando. El primer arranque descarga los modelos; puede tardar varios minutos.'
docker compose up --build --detach --wait --wait-timeout 1800
docker compose exec -T jarvis python -c 'import json, urllib.request; status=json.load(urllib.request.urlopen("http://localhost:8000/voice/status")); assert status.get("ready"), status; print(status)'
echo 'Listo. Abre http://localhost:8000 en Chrome o Edge de Windows (o el puerto de .env).'
echo 'Para medir: docker compose exec -T jarvis python -m jarvis.benchmark --runs 5'
