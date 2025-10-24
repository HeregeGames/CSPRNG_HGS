# Estágio 1: Builder - Instala dependências de compilação e Python
FROM python:3.11-slim as builder

# Instala dependências de sistema para compilar PyAudio e para ping3
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libportaudio2 \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /install
COPY services/harvester/requirements.txt .
RUN pip install --no-cache-dir --prefix="/install" -r requirements.txt

# Estágio 2: Final - Imagem de produção enxuta
FROM python:3.11-slim

# Instala apenas as bibliotecas de sistema necessárias para execução
RUN apt-get update && apt-get install -y --no-install-recommends libportaudio2 iputils-ping && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /install /usr/local
COPY services/common/ ./common
COPY services/harvester/ ./

CMD ["python", "harvester.py"]