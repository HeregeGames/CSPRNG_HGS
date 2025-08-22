import os
import requests
import hashlib
import time
from datetime import datetime
import json
from common.auth import create_hmac, API_AUTH_KEY
import hmac
# --- Configurações ---
MIXER_SERVER_URL = "http://mixer:5000"
API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

API_AUTH_KEY = os.getenv("API_AUTH_KEY", "SUA_CHAVE_SECRETA_MUITO_FORTE_AQUI").encode('utf-8')


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


def get_entropy_from_currency():
    """
    Coleta dados de taxas de câmbio de uma API e gera um hash.
    """
    try:
        print(f"[{datetime.now()}] Acessando API de taxas de câmbio...")
        response = requests.get(API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Converte o dicionário de taxas de câmbio para uma string e adiciona timestamp
        rates_string = json.dumps(data.get('rates', {}), sort_keys=True)
        timestamp = str(int(time.time()))
        
        combined_data = f"{rates_string}{timestamp}".encode('utf-8')
        
        # Gera o hash SHA256 dos dados combinados
        hash_object = hashlib.sha256(combined_data)
        return hash_object.hexdigest()
        
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] Erro ao coletar entropia de taxas de câmbio: {e}")
        return None

if __name__ == "__main__":
    if API_AUTH_KEY == b"SUA_CHAVE_SECRETA_MUITO_FORTE_AQUI":
        print("AVISO: Usando a chave secreta padrão. Altere a variável de ambiente 'API_AUTH_KEY' para uma chave segura!")
    while True:
        hash_data = get_entropy_from_currency()
        if hash_data:
            send_hash_to_mixer(hash_data)
        time.sleep(300) # 5 minutos