Apresentação do Projeto: Gerador de Números Aleatórios Criptograficamente Seguro (CSPRNG)
Visão Geral
Este projeto é um sistema robusto e resiliente para a geração de números aleatórios de alta qualidade, projetado para aplicações que exigem máxima segurança e imprevisibilidade, como jogos de cassino, criptografia e sorteios. O sistema é construído sobre uma arquitetura híbrida que combina fontes de entropia do mundo real com algoritmos criptográficos seguros.

Arquitetura do Sistema
A solução é dividida em três componentes principais, cada um executado em seu próprio contêiner Docker para garantir isolamento e escalabilidade.

Coletores de Entropia (Harvesters)

Propósito: Capturam dados imprevisíveis de fontes externas e os convertem em "hashes" criptográficos. Essas fontes garantem que a aleatoriedade não seja previsível ou replicável.

Fontes Atuais:

Rádio: Coleta pequenos trechos de áudio de streams de rádio online.

Taxas de Câmbio: Extrai dados voláteis de APIs de câmbio globais.

Tecnologia: Scripts Python com a biblioteca requests para comunicação com APIs externas.

Servidor Mixer (Entropy Pool)

Propósito: Atua como o coração do sistema. Ele recebe os hashes dos coletores e os mistura em um "pool" de entropia, um buffer seguro de 512 bits. Esta mistura é feita usando um algoritmo criptográfico (SHA-512), garantindo que a entropia de múltiplas fontes se combine de forma imprevisível.

Mecanismo: O servidor expõe um endpoint RESTful (/api/v1/entropy) para receber os hashes e um endpoint (/api/v1/seed) para fornecer sementes para o gerador.

Tecnologia: Aplicação web com Flask em Python.

Servidor Gerador (CSPRNG)

Propósito: É o gerador de números aleatórios final. Ele consome sementes de alta qualidade do Servidor Mixer para inicializar e re-semear seu estado interno. Isso garante que os números gerados sejam imprevisíveis e resistentes a ataques.

Funcionalidades:

Geração Simples: Endpoint (/api/v1/random) para gerar um número aleatório simples.

Geração com Probabilidades: Endpoint (/api/v1/biased-random) que aceita uma distribuição de probabilidades e retorna um número com base nela.

Sorteio de Lote: Endpoint (/api/v1/draw) para sortear múltiplos números com base em um arquivo de configuração de jogo pré-definido.

Tecnologia: Aplicação web com Flask, utilizando algoritmos criptográficos para a geração de números.

Benefícios Chave
Segurança Criptográfica: A aleatoriedade é continuamente atualizada com fontes externas, protegendo contra previsões e ataques de engenharia reversa.

Resiliência: A arquitetura com múltiplas fontes de entropia garante que o sistema continue operando mesmo se um dos coletores falhar.

Flexibilidade: A API é modular e permite a fácil adição de novas fontes de entropia ou a criação de novas lógicas de jogo.

Escalabilidade: A conteinerização com Docker permite que o sistema seja facilmente implantado, escalado e gerenciado em qualquer ambiente de nuvem.

Este projeto representa uma solução completa para a geração de números aleatórios confiáveis, superando as limitações dos geradores de software padrão.
