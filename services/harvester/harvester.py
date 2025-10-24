import os
import time
import hashlib
import requests
import threading
import importlib
import logging
import logging.config
from common.auth import create_hmac
from common.logging_config import LOGGING_CONFIG

# --- Configuração ---
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("harvester.main")

MIXER_SERVER_URL = "http://mixer:5000"
# Lê as fontes da variável de ambiente, separadas por vírgula
ENABLED_SOURCES_STR = os.getenv("HARVESTER_SOURCES", "latency,radio")
ENABLED_SOURCES = [s.strip() for s in ENABLED_SOURCES_STR.split(',') if s.strip()]

def send_hash_to_mixer(hash_value: str, source_name: str):
    """Envia o hash gerado para o Servidor Mixer com autenticação HMAC."""
    url = f"{MIXER_SERVER_URL}/api/v1/entropy"
    try:
        data_bytes = bytes.fromhex(hash_value)
        hmac_digest = create_hmac(data_bytes)
        
        headers = {'X-RNG-Auth': hmac_digest}
        response = requests.post(url, data=data_bytes, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"Hash from '{source_name}' sent to mixer successfully.", extra={'event': 'send_hash_success', 'source': source_name})
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending hash from '{source_name}' to mixer: {e}", extra={'event': 'send_hash_failure', 'source': source_name})

def run_source(source_instance):
    """Função alvo para a thread, executa uma única fonte em loop."""
    source_name = source_instance.name
    logger.info(f"Starting source: {source_name} with interval {source_instance.interval}s")
    while True:
        try:
            entropy_data = source_instance.get_entropy()
            
            if entropy_data:
                # Adiciona um timestamp para garantir unicidade mesmo se a fonte retornar dados idênticos
                entropy_data += str(time.time_ns()).encode('utf-8')
                
                # Gera o hash SHA256 dos dados
                final_hash = hashlib.sha256(entropy_data).hexdigest()
                send_hash_to_mixer(final_hash, source_name)
            else:
                logger.warning(f"Source '{source_name}' did not return entropy data.", extra={'event': 'no_entropy_data', 'source': source_name})

        except Exception as e:
            logger.error(f"An unhandled error occurred in source '{source_name}': {e}", extra={'event': 'source_runtime_error', 'source': source_name}, exc_info=True)
        
        time.sleep(source_instance.interval)

def main():
    """Carrega dinamicamente e inicia as fontes de entropia habilitadas."""
    if not ENABLED_SOURCES:
        logger.critical("No harvester sources enabled. Set the HARVESTER_SOURCES environment variable.", extra={'event': 'no_sources_enabled'})
        return

    logger.info(f"Harvester starting up with sources: {', '.join(ENABLED_SOURCES)}", extra={'event': 'harvester_startup', 'sources': ENABLED_SOURCES})
    
    threads = []
    for source_name in ENABLED_SOURCES:
        try:
            # Importa dinamicamente o módulo da fonte
            module = importlib.import_module(f"sources.{source_name}")
            # A classe deve ter o mesmo nome do módulo, capitalizado (ex: latency -> Latency)
            SourceClass = getattr(module, source_name.capitalize())
            source_instance = SourceClass()
            
            # Cria e inicia uma thread para a fonte
            thread = threading.Thread(target=run_source, args=(source_instance,), daemon=True)
            thread.start()
            threads.append(thread)
            
        except (ImportError, AttributeError) as e:
            logger.error(f"Could not load source '{source_name}': {e}. Check if 'services/harvester/sources/{source_name}.py' and class '{source_name.capitalize()}' exist.", extra={'event': 'source_load_failure', 'source': source_name})

    # Mantém o processo principal vivo enquanto as threads (daemon) rodam
    try:
        while True:
            time.sleep(3600) # Dorme por um longo tempo, o trabalho é feito nas threads
    except KeyboardInterrupt:
        logger.info("Harvester shutting down.")

if __name__ == "__main__":
    main()