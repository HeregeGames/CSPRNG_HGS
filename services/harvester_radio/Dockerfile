# Estágio 1: Build - Instala dependências de compilação e Python
FROM python:3.11-slim as builder
WORKDIR /install
RUN apt-get update && apt-get install -y build-essential libportaudio2 portaudio19-dev && rm -rf /var/lib/apt/lists/*
COPY services/harvester_radio/requirements.txt .
RUN pip install --no-cache-dir --prefix="/install" -r requirements.txt

# Estágio 2: Final - Imagem de produção com apenas as libs de execução
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libportaudio2 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local
COPY services/harvester_radio/harvester_radio.py .
COPY services/common/ ./common
CMD ["python", "harvester_radio.py"]