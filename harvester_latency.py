import requests
import hashlib
import time
from datetime import datetime

# --- Configurações ---
MIXER_SERVER_URL = "http://mixer:5000"


# Lista de servidores globais para testar a latência
SERVERS = [
    "https://www.google.com",
    "https://www.cloudflare.com",
    "https://www.amazon.com",
    "https://www.microsoft.com",
    "https://www.wikipedia.org"
]

def send_hash_to_mixer(hash_value):
    """Envia o hash gerado para o Servidor Mixer como bytes puros."""
    url = f"{MIXER_SERVER_URL}/api/v1/entropy"
    try:
        data_bytes = bytes.fromhex(hash_value)
        response = requests.post(url, data=data_bytes, timeout=5)
        response.raise_for_status()
        # O mixer retorna JSON, então `response.json()` é seguro
        print(f"[{datetime.now()}] Hash enviado com sucesso para o Mixer. Resposta: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] Erro ao enviar hash para o Mixer: {e}")


def get_entropy_from_latency():
    """
    Mede a latência de múltiplos servidores globais e gera um hash.
    """
    try:
        concatenated_data = ""
        for server in SERVERS:
            print(f"[{datetime.now()}] Testando latência para: {server}")
            
            try:
                # Faz uma requisição e mede o tempo de resposta em segundos
                response = requests.get(server, timeout=10)
                latency_ms = int(response.elapsed.total_seconds() * 1000)
                concatenated_data += str(latency_ms)
                print(f"Latência para {server}: {latency_ms} ms")
            except requests.exceptions.RequestException as e:
                print(f"[{datetime.now()}] Falha na requisição para {server}: {e}. Pulando...")
                continue
                
        if not concatenated_data:
            print(f"[{datetime.now()}] Falha ao coletar dados de latência de todos os servidores.")
            return None
            
        print(f"[{datetime.now()}] Dados de latência coletados: {concatenated_data}")
        
        # Adiciona um timestamp para mais unicidade
        concatenated_data += str(time.time())
        
        data_bytes = concatenated_data.encode('utf-8')
        sha256_hash = hashlib.sha256(data_bytes).hexdigest()
        
        return sha256_hash
        
    except Exception as e:
        print(f"[{datetime.now()}] Ocorreu um erro ao processar os dados: {e}")
        return None

if __name__ == "__main__":
    while True:
        generated_hash = get_entropy_from_latency()
        
        if generated_hash:
            print("\n--- Hash de Entropia Gerado ---")
            print(generated_hash)
            send_hash_to_mixer(generated_hash)
        else:
            print("\nFalha ao gerar o hash. A entropia não foi coletada.")
        
        # Pausa para dar tempo de as latências variarem naturalmente
        time.sleep(60) # 1 minuto
