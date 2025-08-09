import requests
import hashlib
import time
import random
from datetime import datetime

# --- Configurações ---
MIXER_SERVER_URL = "http://127.0.0.1:5000"
API_URL = "http://worldtimeapi.org/api/timezone/"

# Lista de fusos horários para coletar dados
TIMEZONES = [
    "Europe/London", "America/New_York", "Asia/Tokyo", "Australia/Sydney",
    "Africa/Johannesburg", "America/Sao_Paulo", "Atlantic/Reykjavik",
    "Europe/Berlin", "Asia/Dubai", "Pacific/Fiji"
]

def send_hash_to_mixer(hash_value):
    """
    Envia o hash gerado para o Servidor Mixer.
    """
    url = f"{MIXER_SERVER_URL}/api/v1/entropy"
    payload = {"hash": hash_value}
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        print(f"[{datetime.now()}] Hash enviado com sucesso para o Mixer. Resposta: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] Erro ao enviar hash para o Mixer: {e}")

def get_entropy_from_time_data():
    """
    Coleta dados de hora de um fuso horário aleatório e gera um hash.
    """
    try:
        random_timezone = random.choice(TIMEZONES)
        full_url = f"{API_URL}{random_timezone}"
        
        print(f"[{datetime.now()}] Acessando dados da API para o fuso horário: {random_timezone}")
        
        response = requests.get(full_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Concatena os dados relevantes da resposta em uma string
        concatenated_data = f"{data['datetime']}{data['unixtime']}{data['timezone']}"
        
        print(f"[{datetime.now()}] Dados coletados: {concatenated_data}")
        
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
        generated_hash = get_entropy_from_time_data()
        
        if generated_hash:
            print("\n--- Hash de Entropia Gerado ---")
            print(generated_hash)
            send_hash_to_mixer(generated_hash)
        else:
            print("\nFalha ao gerar o hash. A entropia não foi coletada.")
        
        time.sleep(15)
