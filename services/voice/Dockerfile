FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime
ENV PYTHONUNBUFFERED=1 HF_HOME=/models/huggingface TOKENIZERS_PARALLELISM=false
RUN apt-get update && apt-get install -y --no-install-recommends espeak-ng libsndfile1 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /service
COPY services/voice/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY services/voice/server.py ./server.py
# One worker: the models stay resident and are not duplicated in VRAM.
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
