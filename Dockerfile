# Usa uma imagem oficial do Python como base, otimizada para ser menor
FROM python:3.9-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia apenas o arquivo de dependências primeiro
# Isso otimiza o cache do Docker.
COPY requirements.txt .

# Instala as dependências a partir do requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante dos arquivos do projeto para o container
COPY . .

# Exposição das portas
EXPOSE 5000
EXPOSE 5001

# Comando padrão. O docker-compose pode sobrescrever este comando
CMD ["python", "mixer_server.py"]
