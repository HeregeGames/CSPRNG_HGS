import requests
import hashlib
import time
from datetime import datetime

# --- Configurações ---
MIXER_SERVER_URL = "http://mixer:5000"
# Nova API pública do BlockCypher para os últimos blocos do Bitcoin
API_URL = "https://api.blockcypher.com/v1/btc/main"

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


def get_entropy_from_blockchain():
    """
    Coleta os hashes dos blocos mais recentes da blockchain do Bitcoin e gera um hash.
    """
    try:
        print(f"[{datetime.now()}] Acessando dados da API da Blockchain...")
        
        response = requests.get(API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data or 'hash' not in data:
            print(f"[{datetime.now()}] Falha ao coletar dados. API retornou um formato inesperado.")
            return None
        
        latest_block_hash = data['hash']
        
        print(f"[{datetime.now()}] Hash do bloco mais recente coletado: {latest_block_hash}")
        
        data_bytes = latest_block_hash.encode('utf-8')
        sha256_hash = hashlib.sha256(data_bytes).hexdigest()
        
        return sha256_hash
        
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] Erro na requisição HTTP: {e}")
        return None
    except Exception as e:
        print(f"[{datetime.now()}] Ocorreu um erro ao processar os dados: {e}")
        return None

if __name__ == "__main__":
    while True:
        generated_hash = get_entropy_from_blockchain()
        
        if generated_hash:
            print("\n--- Hash de Entropia Gerado ---")
            print(generated_hash)
            send_hash_to_mixer(generated_hash)
        else:
            print("\nFalha ao gerar o hash. A entropia não foi coletada.")
        
        # Intervalo ajustado para 5 minutos (300 segundos)
        # Isso respeita o limite da API e ainda captura novos blocos
        time.sleep(300)
