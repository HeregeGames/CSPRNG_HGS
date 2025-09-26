# CSPRNG - Cryptographically Secure Random Number Generator

[![Status](https://img.shields.io/badge/status-in%20development-yellow)]()

A distributed and resilient system for generating high-quality random numbers, ideal for applications requiring security and unpredictability, such as cryptography, raffles, and games.

## Table of Contents

- [Architecture](#architecture)
- [Key Features](#key-features)
- [How to Run the Project](#how-to-run-the-project)
  - [Prerequisites](#prerequisites)
  - [Configuration](#configuration)
  - [Starting the Services](#starting-the-services)
- [API Usage](#api-usage)
  - [Health Check](#health-check)
  - [Download Audit Logs](#download-audit-logs)

---

## Architecture

The system is built on a microservices architecture orchestrated with Docker, ensuring isolation, resilience, and scalability.

1.  **Harvesters (Entropy Collectors)**:
    -   **Purpose**: Independent Python scripts that capture data from unpredictable real-world sources (radio, weather, network latency, currency exchange rates).
    -   **Function**: They convert this data into `SHA-256` hashes and send them to the Mixer.

2.  **Mixer (Entropy Pool)**:
    -   **Purpose**: The heart of the system. It receives hashes from the Harvesters and continuously mixes them into a 512-bit entropy pool using `SHA-512`.
    -   **Function**: It provides high-quality "seeds" to the Generator, ensuring that the randomness is a combination of multiple sources.

3.  **Generator (CSPRNG Generator)**:
    -   **Purpose**: The final service that exposes the API for consuming random numbers.
    -   **Function**: It uses seeds from the Mixer to initialize and re-seed an `AES-CTR` based generator, producing cryptographically secure random numbers.

## Key Features

-   **Cryptographic Security**: Randomness is continuously fed by real-world sources, protecting against prediction attacks.
-   **Resilience**: The architecture with multiple Harvesters ensures the system continues to operate even if one of the sources fails.
-   **Modularity**: The service-based structure allows for the easy addition of new entropy sources or new drawing logic.
-   **Scalability**: Containerization with Docker allows the system to be easily deployed and scaled horizontally.

---

## How to Run the Project

### Prerequisites

-   Docker
-   Docker Compose

### Configuration

1.  **Clone the repository:**
    ```bash
    git clone <YOUR_REPOSITORY_URL>
    cd CSPRNG_HGS
    ```

2.  **Create the environment file:**
    Copy the example file `.env.example` to a new file named `.env`.
    ```bash
    cp .env.example .env
    ```

3.  **Set the API Key:**
    Open the `.env` file and replace `YOUR_VERY_STRONG_SECRET_KEY_HERE` with a secure key. You can generate one with the following command:
    ```bash
    openssl rand -hex 32
    ```
    This key is used to authenticate communication between services (Harvesters, Mixer, and Generator) using HMAC.

### Starting the Services

With Docker running, bring up all containers with Docker Compose:

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

## Licença

Este projeto é distribuído sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
