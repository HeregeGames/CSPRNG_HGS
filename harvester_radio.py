import requests
import hashlib
from datetime import datetime
import time

# --- Configurações ---
MIXER_SERVER_URL = "http://mixer:5000"
RADIO_STREAM_URL = "https://news-stream.iowapublicradio.org/NewsLow.mp3"
CHUNK_SIZE = 4096

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


def get_entropy_from_radio(stream_url, chunk_size=4096, timeout=10):
    """
    Conecta-se a um stream de rádio online, captura dados e gera um hash.
    """
    headers = {'User-Agent': 'Python Harvester'}
    try:
        print(f"[{datetime.now()}] Conectando ao stream: {stream_url}")
        
        with requests.get(stream_url, headers=headers, stream=True, timeout=timeout) as response:
            response.raise_for_status()
            audio_chunk = response.raw.read(chunk_size)
            
            if not audio_chunk:
                print("Nenhum dado de áudio recebido. Retornando None.")
                return None
            
            print(f"[{datetime.now()}] {len(audio_chunk)} bytes de áudio coletados.")
            sha256_hash = hashlib.sha256(audio_chunk).hexdigest()
            return sha256_hash

    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        return None
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        return None

if __name__ == "__main__":
    while True:
        generated_hash = get_entropy_from_radio(RADIO_STREAM_URL, CHUNK_SIZE)
        if generated_hash:
            print("\n--- Hash de Entropia Gerado ---")
            print(generated_hash)
            send_hash_to_mixer(generated_hash)
        else:
            print("\nFalha ao gerar o hash. A entropia não foi coletada.")
        
        # Espera um pouco antes da próxima coleta
        time.sleep(15)
