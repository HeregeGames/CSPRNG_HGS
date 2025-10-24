#!/bin/bash

# Este script coleta uma grande quantidade de números aleatórios do serviço
# generator para serem usados em testes estatísticos.

set -e

OUTPUT_FILE="random_numbers.txt"
TOTAL_NUMBERS=25000000 # ~100MB de dados (25M * 4 bytes/int)
NUMBERS_PER_REQUEST=1000

echo "Iniciando a coleta de ${TOTAL_NUMBERS} números aleatórios..."
echo "Isso pode levar vários minutos."

# Limpa o arquivo de saída se ele já existir
> "$OUTPUT_FILE"

REQUEST_COUNT=$((TOTAL_NUMBERS / NUMBERS_PER_REQUEST))

for i in $(seq 1 $REQUEST_COUNT); do
  # Faz a requisição e extrai os números do JSON, um por linha.
  # Assumimos um endpoint GET /api/v1/random/integer?count=N
  curl -s "http://localhost:5001/api/v1/random/integer?count=${NUMBERS_PER_REQUEST}" | jq '.numbers[]' >> "$OUTPUT_FILE"
  
  # Mostra o progresso
  echo -ne "Progresso: $i / $REQUEST_COUNT requisições concluídas.\r"
done

echo -e "\nColeta concluída! Dados salvos em '${OUTPUT_FILE}'."