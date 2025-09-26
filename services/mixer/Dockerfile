# Estágio 1: Build - Instala dependências
FROM python:3.11-slim as builder
WORKDIR /install
COPY services/mixer/requirements.txt .
RUN pip install --no-cache-dir --prefix="/install" -r requirements.txt

# Estágio 2: Final - Imagem de produção enxuta
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY services/mixer/mixer_server.py .
COPY services/common/ ./common/
CMD ["python", "mixer_server.py"]
