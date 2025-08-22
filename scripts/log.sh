#!/bin/bash

# 1. Leia a chave do seu arquivo .env
API_KEY=$(grep API_AUTH_KEY .env | cut -d '=' -f2)

# 2. Use Python para gerar o HMAC para um corpo vazio
HMAC=$(python -c "import hmac, hashlib; print(hmac.new(b'$API_KEY', b'', hashlib.sha256).hexdigest())")

# 3. Faça a requisição com a assinatura HMAC correta
echo "Usando HMAC: $HMAC"
curl -H "X-RNG-Auth: $HMAC" http://localhost:5001/api/v1/audit/logs -o audit.log

# Verifique o conteúdo do arquivo baixado
echo "Conteúdo do audit.log:"
cat audit.log
