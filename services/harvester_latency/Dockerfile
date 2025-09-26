# Estágio 1: Build - Instala dependências
FROM python:3.11-slim as builder
WORKDIR /install
COPY services/harvester_latency/requirements.txt .
RUN pip install --no-cache-dir --prefix="/install" -r requirements.txt

# Estágio 2: Final - Imagem de produção com dependências de sistema
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y iputils-ping && rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local
COPY services/harvester_latency/harvester_latency.py .
COPY services/common/ ./common
CMD ["python", "harvester_latency.py"]