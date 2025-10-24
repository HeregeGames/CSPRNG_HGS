#!/bin/bash

# Script completo para testar a qualidade do CSPRNG com dieharder.

set -e

BINARY_DATA_FILE="random_data.bin"
TARGET_SIZE_MB=100 # Quantidade de dados em MB para gerar. 100MB é um bom começo.
SIZE_IN_BYTES=$((TARGET_SIZE_MB * 1024 * 1024))

if ! command -v dieharder &> /dev/null || ! command -v pv &> /dev/null
then
    echo "Erro: 'dieharder' não está instalado."
    echo "Por favor, instale-o para continuar (ex: sudo apt-get install dieharder)."
    exit 1
fi

echo "Passo 1: Gerando o HMAC para autenticação..."
API_KEY=$(grep API_AUTH_KEY .env | cut -d '=' -f2)
if [ -z "$API_KEY" ]; then
    echo "Erro: Não foi possível encontrar API_AUTH_KEY no arquivo .env"
    exit 1
fi
HMAC=$(python3 -c "import hmac, hashlib; print(hmac.new(b'$API_KEY', b'', hashlib.sha256).hexdigest())")

echo "Passo 2: Gerando ${TARGET_SIZE_MB}MB de dados binários a partir do gerador..."
echo "Isso pode levar alguns minutos. O progresso será exibido abaixo."

# Usamos 'curl' para obter o stream, 'pv' para mostrar o progresso e 'head' para limitar o tamanho exato.
# 1. curl inicia o stream infinito.
# 2. pv monitora o fluxo, esperando um total de SIZE_IN_BYTES.
# 3. head lê exatamente SIZE_IN_BYTES e fecha o pipe, interrompendo o processo.
curl -s -H "X-RNG-Auth: $HMAC" http://localhost:5001/api/v1/stream_entropy | pv -s $SIZE_IN_BYTES | head -c $SIZE_IN_BYTES > "$BINARY_DATA_FILE"

echo -e "\nPasso 3: Executando o conjunto de testes dieharder em '${BINARY_DATA_FILE}'..."
echo "Isso pode levar muito tempo (várias horas dependendo da máquina)."
echo "Os resultados serão salvos em 'dieharder_results.txt'."

# Executa todos os testes (-a) usando o arquivo binário (-f)
# e salva a saída em um arquivo de log.
dieharder -a -g 200 -f "$BINARY_DATA_FILE" > dieharder_results.txt

echo -e "\n--- Análise dos Resultados ---"
echo "Teste concluído. Verifique o arquivo 'dieharder_results.txt'."
echo "Procure por testes com status 'FAILED'."
FAILED_COUNT=$(grep -c "FAILED" dieharder_results.txt || true)
echo "Número de testes que falharam: ${FAILED_COUNT}"

echo "Um número baixo (ou zero) de falhas indica uma boa qualidade de aleatoriedade."