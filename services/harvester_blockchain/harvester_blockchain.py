import os
import requests
import hashlib
import time
from datetime import datetime
import logging
import logging.config
from common.auth import create_hmac
from common.logging_config import LOGGING_CONFIG

# --- Configuração de Logging ---
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
# --- Configurações ---
MIXER_SERVER_URL = "http://mixer:5000"
# Nova API pública do BlockCypher para os últimos blocos do Bitcoin
API_URL = "https://api.blockcypher.com/v1/btc/main"

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


def get_entropy_from_blockchain():
    """
    Coleta os hashes dos blocos mais recentes da blockchain do Bitcoin e gera um hash.
    """
    try:
        logger.info("Accessing blockchain API...", extra={'event': 'fetch_blockchain_data'})
        
        response = requests.get(API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data or 'hash' not in data:
            logger.warning("Failed to collect data. API returned unexpected format.", extra={'event': 'fetch_blockchain_data_failure', 'response_data': data})
            return None
        
        latest_block_hash = data['hash']
        
        logger.info(f"Latest block hash collected: {latest_block_hash}", extra={'event': 'fetch_blockchain_data_success'})
        
        data_bytes = latest_block_hash.encode('utf-8')
        sha256_hash = hashlib.sha256(data_bytes).hexdigest()
        
        return sha256_hash
        
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request error: {e}", extra={'event': 'fetch_blockchain_http_error'})
        return None
    except Exception as e:
        logger.error(f"An error occurred while processing data: {e}", extra={'event': 'fetch_blockchain_processing_error'}, exc_info=True)
        return None

if __name__ == "__main__":
    logger.info("Blockchain harvester starting up...")
    while True:
        generated_hash = get_entropy_from_blockchain()
        
        if generated_hash:
            send_hash_to_mixer(generated_hash)
        
        # Intervalo ajustado para 5 minutos (300 segundos)
        # Isso respeita o limite da API e ainda captura novos blocos
        time.sleep(300)
