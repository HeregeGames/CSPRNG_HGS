import requests
import hashlib
import time
from datetime import datetime
import hmac
import os
import json

# --- Configurações ---
MIXER_SERVER_URL = "http://mixer:5000"
API_AUTH_KEY = os.getenv("API_AUTH_KEY", "SUA_CHAVE_SECRETA_MUITO_FORTE_AQUI").encode('utf-8')
API_URL = "https://api.open-meteo.com/v1/forecast"

# Lista de cidades com suas coordenadas (latitude e longitude)
CITIES = [
    {"name": "London", "latitude": 51.5074, "longitude": -0.1278},
    {"name": "New York", "latitude": 40.7128, "longitude": -74.0060},
    {"name": "Tokyo", "latitude": 35.6895, "longitude": 139.6917},
    {"name": "Sydney", "latitude": -33.8688, "longitude": 151.2093},
    {"name": "Florianopolis", "latitude": -27.5935, "longitude": -48.5585},
    {"name": "Dubai", "latitude": 25.2048, "longitude": 55.2708},
    {"name": "Moscow", "latitude": 55.7558, "longitude": 37.6173}
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


def get_entropy_from_weather():
    """
    Coleta dados meteorológicos de múltiplas cidades e gera um hash.
    """
    try:
        concatenated_data = ""
        for city in CITIES:
            print(f"[{datetime.now()}] Acessando dados meteorológicos para: {city['name']}")
            params = {
                "latitude": city['latitude'],
                "longitude": city['longitude'],
                "current_weather": True,
                "timezone": "auto"
            }
            
            try:
                response = requests.get(API_URL, params=params, timeout=20)
                response.raise_for_status()
                data = response.json()
                
                if 'current_weather' in data:
                    weather_data = data['current_weather']
                    concatenated_data += f"{weather_data['temperature']}{weather_data['windspeed']}"
                
            except requests.exceptions.RequestException as e:
                print(f"[{datetime.now()}] Falha na requisição para {city['name']}: {e}. Pulando para a próxima cidade.")
                continue

        if not concatenated_data:
            print(f"[{datetime.now()}] Falha ao coletar dados de todas as cidades especificadas.")
            return None
            
        print(f"[{datetime.now()}] Dados meteorológicos coletados: {concatenated_data[:50]}...")
        
        concatenated_data += str(time.time())
        
        data_bytes = concatenated_data.encode('utf-8')
        sha256_hash = hashlib.sha256(data_bytes).hexdigest()
        
        return sha256_hash
        
    except Exception as e:
        print(f"[{datetime.now()}] Ocorreu um erro ao processar os dados: {e}")
        return None

if __name__ == "__main__":
    if API_AUTH_KEY == b"SUA_CHAVE_SECRETA_MUITO_FORTE_AQUI":
        print("AVISO: Usando a chave secreta padrão. Altere a variável de ambiente 'API_AUTH_KEY' para uma chave segura!")
    while True:
        generated_hash = get_entropy_from_weather()
        
        if generated_hash:
            print("\n--- Hash de Entropia Gerado ---")
            print(generated_hash)
            send_hash_to_mixer(generated_hash)
        else:
            print("\nFalha ao gerar o hash. A entropia não foi coletada.")
        
        time.sleep(300) # 5 minutos