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

### Gerar um Número Aleatório Simples

Retorna um número aleatório de 64 bits como um inteiro.

-   **Endpoint**: `GET /api/v1/random`
-   **Exemplo com `curl`**:
    ```bash
    curl http://localhost:5001/api/v1/random
    ```
-   **Resposta Esperada**:
    ```json
    {
      "random_number": 8360311362399349423
    }
    ```

### Gerar um Número com Pesos (Sorteio Ponderado)

Sorteia um item de uma lista com base em probabilidades definidas.

-   **Endpoint**: `POST /api/v1/biased-random`
-   **Corpo da Requisição (JSON)**: Um dicionário onde as chaves são os itens e os valores são seus pesos (probabilidades).
-   **Exemplo com `curl`**:
    ```bash
    curl -X POST -H "Content-Type: application/json" \
      -d '{"bronze": 0.7, "prata": 0.2, "ouro": 0.1}' \
      http://localhost:5001/api/v1/biased-random
    ```
-   **Resposta Esperada**:
    ```json
    {
      "result": "bronze"
    }
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
