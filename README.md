# CSPRNG - Gerador de Números Aleatórios Criptograficamente Seguro

[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)](https://github.com/herege/CSPRNG_HGS)

Um sistema distribuído e resiliente para a geração de números aleatórios de alta qualidade, ideal para aplicações que exigem segurança e imprevisibilidade, como criptografia, sorteios e jogos.

## Índice

- [Arquitetura](#arquitetura)
- [Principais Funcionalidades](#principais-funcionalidades)
- [Como Executar o Projeto](#como-executar-o-projeto)
  - [Pré-requisitos](#pré-requisitos)
  - [Configuração](#configuração)
  - [Iniciando os Serviços](#iniciando-os-serviços)
- [Uso da API](#uso-da-api)
  - [Gerar um Número Aleatório Simples](#gerar-um-número-aleatório-simples)
  - [Gerar um Número com Pesos (Sorteio Ponderado)](#gerar-um-número-com-pesos-sorteio-ponderado)
- [Estrutura do Projeto](#estrutura-do-projeto)

---

## Arquitetura

O sistema é construído sobre uma arquitetura de microserviços orquestrada com Docker, garantindo isolamento, resiliência e escalabilidade.

1.  **Harvesters (Coletores de Entropia)**:
    -   **Propósito**: Scripts Python independentes que capturam dados de fontes imprevisíveis do mundo real (rádio, clima, latência de rede, taxas de câmbio).
    -   **Função**: Convertem esses dados em hashes `SHA-256` e os enviam para o Mixer.

2.  **Mixer (Pool de Entropia)**:
    -   **Propósito**: O coração do sistema. Recebe hashes dos Harvesters e os mistura continuamente em um "pool" de entropia de 512 bits usando `SHA-512`.
    -   **Função**: Fornece "sementes" (seeds) de alta qualidade para o Gerador, garantindo que a aleatoriedade seja uma combinação de múltiplas fontes.

3.  **Generator (Gerador CSPRNG)**:
    -   **Propósito**: O serviço final que expõe a API para o consumo dos números aleatórios.
    -   **Função**: Utiliza as sementes do Mixer para inicializar e re-semear um gerador `AES-CTR`, produzindo números aleatórios criptograficamente seguros.

## Principais Funcionalidades

-   **Segurança Criptográfica**: A aleatoriedade é continuamente alimentada por fontes do mundo real, protegendo contra ataques de previsão.
-   **Resiliência**: A arquitetura com múltiplos Harvesters garante que o sistema continue operando mesmo se uma das fontes falhar.
-   **Modularidade**: A estrutura de serviços permite a fácil adição de novas fontes de entropia ou novas lógicas de sorteio.
-   **Escalabilidade**: A conteinerização com Docker permite que o sistema seja facilmente implantado e escalado horizontalmente.

---

## Como Executar o Projeto

### Pré-requisitos

-   Docker
-   Docker Compose

### Configuração

1.  **Clone o repositório:**
    ```bash
    git clone <URL_DO_SEU_REPOSITORIO>
    cd CSPRNG_HGS
    ```

2.  **Crie o arquivo de ambiente:**
    Copie o arquivo de exemplo `.env.example` para um novo arquivo chamado `.env`.
    ```bash
    cp .env.example .env
    ```

3.  **Defina a Chave de API:**
    Abra o arquivo `.env` e substitua `SUA_CHAVE_SECRETA_MUITO_FORTE_AQUI` por uma chave segura. Você pode gerar uma com o seguinte comando:
    ```bash
    openssl rand -hex 32
    ```
    Esta chave é usada para autenticar a comunicação entre os serviços (Harvesters, Mixer e Generator) usando HMAC.

### Iniciando os Serviços

Com o Docker em execução, suba todos os contêineres com o Docker Compose:

```bash
docker-compose up --build
```

Os serviços estarão disponíveis nas seguintes portas:
-   **Mixer**: `http://localhost:5000` (uso interno)
-   **Generator**: `http://localhost:5001` (API pública)

---

## Uso da API

Todas as requisições são feitas ao serviço **Generator** na porta `5001`.

### Verificar a Saúde do Serviço (Health Check)

Antes de fazer requisições, é uma boa prática verificar se o serviço está pronto.

-   **Endpoint**: `GET /api/v1/health`
-   **Exemplo com `curl`**:
    ```bash
    curl http://localhost:5001/api/v1/health
    ```
-   **Resposta Esperada (Pronto)**:
    ```json
    {
      "status": "ok",
      "message": "Gerador está pronto."
    }
    ```
-   **Resposta Esperada (Inicializando)**:
    ```json
    {
      "status": "error",
      "message": "Gerador está inicializando."
    }
    ```

### Gerar Números para Jogo (Slot 5x3)

Retorna 15 números aleatórios para um jogo de slot. **Requer autenticação.**

-   **Endpoint**: `GET /api/v1/games/slot_5x3`
-   **Autenticação**: Header `X-RNG-Auth` com um HMAC-SHA256 do corpo vazio.
-   **Exemplo com `curl`**:
    ```bash
    # Gere o HMAC para um corpo vazio e adicione ao header
    curl -H "X-RNG-Auth: <HMAC_GERADO_AQUI>" http://localhost:5001/api/v1/games/slot_5x3
    ```
-   **Resposta Esperada**:
    ```json
    {
      "game": "slot_5x3",
      "drawn_numbers": [ 1, 8, 0, 5, 3, 9, 2, 7, 6, 4, 8, 2, 1, 5, 7 ],
      "status": "success"
    }
    ```

### Realizar Sorteio com Pesos

Sorteia itens de uma lista com base em probabilidades definidas. **Requer autenticação.**

-   **Endpoint**: `POST /api/v1/games/draw_symbols`
-   **Autenticação**: Header `X-RNG-Auth` com um HMAC-SHA256 do corpo da requisição JSON.
-   **Corpo da Requisição (JSON)**: Uma lista de dicionários com `name` e `weight`.
-   **Exemplo com `curl`**:
    ```bash
    # Corpo da requisição
    BODY='{"symbols":[{"name":"bronze","weight":70},{"name":"prata","weight":20},{"name":"ouro","weight":10}]}'
    # Gere o HMAC para o corpo do JSON e adicione ao header
    curl -X POST -H "Content-Type: application/json" \
      -H "X-RNG-Auth: <HMAC_GERADO_AQUI_PARA_O_BODY>" \
      -d "$BODY" \
      http://localhost:5001/api/v1/games/draw_symbols
    ```
-   **Resposta Esperada**:
    ```json
    {
      "status": "success",
      "drawn_symbols": [ "bronze", "bronze", "prata", "bronze", "ouro", "bronze", "bronze", "bronze", "prata", "bronze", "bronze", "bronze", "bronze", "prata", "bronze" ]
    }
    ```

### Baixar Logs de Auditoria

-   Retorna o arquivo de log de auditoria (`audit.log`). **Requer autenticação.**

-   **Endpoint**: `GET /api/v1/audit/logs`
-   **Autenticação**: Header `X-RNG-Auth` com um HMAC-SHA256 do corpo vazio.
-   **Exemplo com `curl` e Python**:
    ```bash
    # 1. Obtenha sua chave secreta do arquivo .env
    API_KEY="sua_chave_secreta_aqui"

    # 2. Gere o HMAC usando Python
    HMAC=$(python -c "import hmac, hashlib; print(hmac.new(b'$API_KEY', b'', hashlib.sha256).hexdigest())")

    # 3. Faça a requisição com o HMAC gerado
    curl -H "X-RNG-Auth: $HMAC" http://localhost:5001/api/v1/audit/logs -o audit.log
    ```

---

## Estrutura do Projeto

O projeto está organizado em uma estrutura de microserviços para maior clareza e manutenibilidade.

```
CSPRNG_HGS/
├── docker-compose.yml     # Orquestrador dos serviços
├── .env.example           # Exemplo de arquivo de configuração
├── services/              # Contém o código de todos os serviços
│   ├── common/            # Código compartilhado (ex: autenticação)
│   ├── generator/         # Serviço Gerador (API pública)
│   ├── mixer/             # Serviço Mixer (Pool de Entropia)
│   └── harvester_*/       # Múltiplos serviços de coleta de entropia
└── README.md              # Esta documentação
```
