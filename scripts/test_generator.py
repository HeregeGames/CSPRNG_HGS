import requests
import time
import os
from datetime import datetime

# --- Configurações ---
GENERATOR_URL = "http://127.0.0.1:5001/api/v1/stream_entropy"
OUTPUT_FILE = "raw_entropy.bin"
TARGET_SIZE_MB = 1
TARGET_SIZE_BYTES = TARGET_SIZE_MB * 1024 * 1024

if __name__ == "__main__":
    print(f"[{datetime.now()}] Aguardando 10 segundos para que o mixer colete entropia...")
    time.sleep(10)

    print(f"[{datetime.now()}] Iniciando a coleta de {TARGET_SIZE_MB}MB de entropia bruta em um único fluxo...")
    
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    start_time = time.time()
    total_bytes_collected = 0

    try:
        response = requests.get(GENERATOR_URL, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(OUTPUT_FILE, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    total_bytes_collected += len(chunk)
        
        print("\n--- Coleta Concluída ---")
        print(f"Total de bytes salvos em '{OUTPUT_FILE}': {total_bytes_collected}")
        print(f"Tempo total de execução: {time.time() - start_time:.2f} segundos")
        print("O arquivo está pronto para ser usado em testes de aleatoriedade.")
            
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        print("A coleta falhou.")
