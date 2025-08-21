import requests
import hashlib
import time
from datetime import datetime
import hmac
import os
import wave
import pyaudio

# --- Configurações ---
MIXER_SERVER_URL = "http://mixer:5000"
API_AUTH_KEY = os.getenv("API_AUTH_KEY", "SUA_CHAVE_SECRETA_MUITO_FORTE_AQUI").encode('utf-8')
# URL de um stream de áudio estável para demonstração
RADIO_STREAM_URL = "http://radio.garden/api/tune/I4yFz9pM"
CHUNK_SIZE = 1024 * 16  # 16 KB de dados por coleta

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

def get_entropy_from_radio():
    """
    Coleta dados binários de um stream de rádio e gera um hash.
    Requer a instalação de 'pyaudio'.
    """
    try:
        print(f"[{datetime.now()}] Conectando ao stream de rádio...")
        
        response = requests.get(RADIO_STREAM_URL, stream=True)
        response.raise_for_status()
        
        hash_object = hashlib.sha256()
        
        # Lê um pedaço de dados do stream
        chunk = next(response.iter_content(CHUNK_SIZE))
        if not chunk:
            print(f"[{datetime.now()}] Falha ao coletar dados do stream.")
            return None
            
        hash_object.update(chunk)
        return hash_object.hexdigest()
        
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] Erro ao coletar entropia do rádio: {e}")
        return None

if __name__ == "__main__":
    if API_AUTH_KEY == b"SUA_CHAVE_SECRETA_MUITO_FORTE_AQUI":
        print("AVISO: Usando a chave secreta padrão. Altere a variável de ambiente 'API_AUTH_KEY' para uma chave segura!")
    while True:
        hash_data = get_entropy_from_radio()
        if hash_data:
            send_hash_to_mixer(hash_data)
        time.sleep(60)  # Coleta a cada 60 segundos