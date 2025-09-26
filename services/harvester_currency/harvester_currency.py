import os
import requests
import hashlib
import time
from datetime import datetime
import json
import logging
import logging.config
from common.auth import create_hmac
from common.logging_config import LOGGING_CONFIG

# --- Configurações ---
MIXER_SERVER_URL = "http://mixer:5000"
API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

# --- Configuração de Logging ---
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

def send_hash_to_mixer(hash_value):
    """Envia o hash gerado para o Servidor Mixer com autenticação HMAC."""
    url = f"{MIXER_SERVER_URL}/api/v1/entropy"
    try:
        data_bytes = bytes.fromhex(hash_value)
        hmac_digest = create_hmac(data_bytes)
        
        headers = {'X-RNG-Auth': hmac_digest}
        response = requests.post(url, data=data_bytes, headers=headers, timeout=5)
        response.raise_for_status()
        logger.info("Hash sent to mixer successfully.", extra={'event': 'send_hash_success', 'response': response.json()})
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending hash to mixer: {e}", extra={'event': 'send_hash_failure'})


def get_entropy_from_currency():
    """
    Coleta dados de taxas de câmbio de uma API e gera um hash.
    """
    try:
        logger.info("Accessing currency exchange API...", extra={'event': 'fetch_currency_data'})
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
        logger.error(f"Error collecting entropy from currency exchange: {e}", extra={'event': 'fetch_currency_failure'})
        return None

if __name__ == "__main__":
    logger.info("Currency harvester starting up...")
    while True:
        hash_data = get_entropy_from_currency()
        if hash_data:
            send_hash_to_mixer(hash_data)
        time.sleep(300) # 5 minutos