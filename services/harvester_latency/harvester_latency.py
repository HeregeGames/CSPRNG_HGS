# Desenvolvido por: Leandro M. da Costa (HG Studios)
#

import requests
import hashlib
import time
from datetime import datetime
import hmac
import os
import ping3

# --- Configurações ---
MIXER_SERVER_URL = "http://mixer:5000"
API_AUTH_KEY = os.getenv("API_AUTH_KEY", "SUA_CHAVE_SECRETA_MUITO_FORTE_AQUI").encode('utf-8')
SERVERS_TO_PING = [
    "8.8.8.8",   # Google DNS
    "1.1.1.1",   # Cloudflare DNS
    "9.9.9.9",   # Quad9 DNS
    "208.67.222.222" # OpenDNS
]

def send_hash_to_mixer(hash_value):
    """Envia o hash gerado para o Servidor Mixer com autenticação HMAC."""
    url = f"{MIXER_SERVER_URL}/api/v1/entropy"
    try:
        data_bytes = bytes.fromhex(hash_value)
        hmac_digest = hmac.new(API_AUTH_KEY, data_bytes, hashlib.sha256).hexdigest()
        
        headers = {'X-RNG-Auth': hmac_digest}
        response = requests.post(url, data=data_bytes, headers=headers, timeout=5)
        response.raise_for_status()
        print(f"[{datetime.now()}] Hash enviado com sucesso para o Mixer. Resposta: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] Erro ao enviar hash para o Mixer: {e}")

def get_entropy_from_latency():
    """
    Mede a latência para uma lista de servidores e gera um hash a partir dos resultados.
    """
    combined_data = ""
    for server in SERVERS_TO_PING:
        try:
            delay = ping3.ping(server, unit='ms', timeout=1)
            if delay is not None and delay is not False:
                # Usa o tempo de resposta e o timestamp para adicionar mais entropia
                combined_data += f"{delay:.6f}{int(time.time() * 1000)}"
        except Exception as e:
            print(f"[{datetime.now()}] Erro ao pingar {server}: {e}")
    
    if not combined_data:
        print(f"[{datetime.now()}] Falha ao coletar dados de latência.")
        return None

    hash_object = hashlib.sha256(combined_data.encode('utf-8'))
    return hash_object.hexdigest()

if __name__ == "__main__":
    if API_AUTH_KEY == b"SUA_CHAVE_SECRETA_MUITO_FORTE_AQUI":
        print("AVISO: Usando a chave secreta padrão. Altere a variável de ambiente 'API_AUTH_KEY' para uma chave segura!")
    while True:
        hash_data = get_entropy_from_latency()
        if hash_data:
            send_hash_to_mixer(hash_data)
        time.sleep(10)  # Coleta a cada 10 segundos