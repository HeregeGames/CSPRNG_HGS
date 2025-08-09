import requests
import hashlib
import time
from datetime import datetime

# --- Configurações ---
MIXER_SERVER_URL = "http://mixer:5000"
# Usamos uma API pública e gratuita.
API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

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


def get_entropy_from_currency_rates():
    """
    Coleta dados de taxas de câmbio e gera um hash.
    """
    try:
        print(f"[{datetime.now()}] Acessando dados da API de câmbio...")
        
        response = requests.get(API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # O API Key é opcional para esta API de exemplo, mas é bom ter uma em mente.
        
        # Concatena as taxas de câmbio das moedas mais voláteis para gerar a entropia
        rates = data['rates']
        
        if not rates:
            print(f"[{datetime.now()}] Falha ao coletar dados. API retornou taxas vazias.")
            return None
        
        # Concatena os valores das taxas de câmbio mais populares
        concatenated_data = ""
        for currency in ['EUR', 'JPY', 'GBP', 'AUD', 'CAD', 'CHF', 'BRL']:
            if currency in rates:
                concatenated_data += str(rates[currency])
        
        # Adiciona um timestamp para mais unicidade, caso as taxas não mudem rapidamente
        concatenated_data += str(time.time())

        if not concatenated_data:
             print(f"[{datetime.now()}] Falha ao coletar dados para as moedas especificadas.")
             return None
        
        print(f"[{datetime.now()}] Dados de câmbio coletados: {concatenated_data[:50]}...")
        
        data_bytes = concatenated_data.encode('utf-8')
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
        generated_hash = get_entropy_from_currency_rates()
        
        if generated_hash:
            print("\n--- Hash de Entropia Gerado ---")
            print(generated_hash)
            send_hash_to_mixer(generated_hash)
        else:
            print("\nFalha ao gerar o hash. A entropia não foi coletada.")
        
        # Pausa de 30 segundos para respeitar o limite de requisições da API
        time.sleep(30)
