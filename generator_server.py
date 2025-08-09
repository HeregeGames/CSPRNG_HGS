import os
import hashlib
from flask import Flask, request, jsonify, Response
import requests
import time
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import threading

app = Flask(__name__)

# --- Configurações ---
MIXER_SERVER_URL = "http://mixer:5000"
REKEY_INTERVAL_MB = 100 # Re-sincronizar a cada 100MB

class DeterministicCSPRNG:
    def __init__(self, seed: bytes):
        self._seed = seed
        self._bytes_generated = 0
        self._lock = threading.Lock()
        self._rekey()

    def _rekey(self):
        """Deriva uma nova chave e nonce da semente para ressincronização."""
        # Usa a semente para derivar a chave
        self._key = hashlib.sha256(self._seed).digest()
        # Usa uma parte do hash da semente e um contador para o nonce
        self._nonce = hashlib.sha512(self._seed).digest()[32:48]
        self._backend = default_backend()
        
        cipher = Cipher(algorithms.AES(self._key), modes.CTR(self._nonce), backend=self._backend)
        self._encryptor = cipher.encryptor()
        
        self._bytes_generated = 0
        print(f"[{datetime.now()}] CSPRNG re-sincronizado com uma nova semente.")

    def generate(self, num_bytes: int) -> bytes:
        with self._lock:
            # Verifica se é hora de re-sincronizar
            if self._bytes_generated >= REKEY_INTERVAL_MB * 1024 * 1024:
                print(f"[{datetime.now()}] Limite de {REKEY_INTERVAL_MB}MB atingido. Buscando nova semente...")
                new_seed = fetch_new_seed_with_retry()
                if new_seed:
                    self._seed = new_seed
                    self._rekey()
                else:
                    raise Exception("Falha ao re-sincronizar a chave do CSPRNG.")

            chunk = self._encryptor.update(b'\x00' * num_bytes)
            self._bytes_generated += len(chunk)
            return chunk

def fetch_new_seed_with_retry():
    retries = 10
    while retries > 0:
        try:
            response = requests.get(f"{MIXER_SERVER_URL}/api/v1/seed", timeout=5)
            response.raise_for_status()
            
            new_seed = response.content
            return new_seed
        except requests.exceptions.RequestException as e:
            retries -= 1
            print(f"[{datetime.now()}] Erro ao buscar semente do Mixer: {e}. Tentando novamente... ({retries} retries restantes)")
            time.sleep(1)
    
    print(f"[{datetime.now()}] Falha crítica: Não foi possível conectar ao Mixer após várias tentativas.")
    return None

# --- Rotas da API ---

@app.route("/api/v1/games/slot_5x3", methods=["GET"])
def get_slot_5x3_numbers():
    new_seed = fetch_new_seed_with_retry()
    if not new_seed:
        return jsonify({"status": "error", "message": "Generator not initialized."}), 500
    
    csprng = DeterministicCSPRNG(new_seed)
    random_bytes = csprng.generate(15)
    drawn_numbers = [byte % 10 for byte in random_bytes]
    
    return jsonify({
        "game": "slot_5x3",
        "drawn_numbers": drawn_numbers,
        "status": "success"
    })

@app.route("/api/v1/stream_entropy", methods=["GET"])
def get_raw_entropy_stream():
    new_seed = fetch_new_seed_with_retry()
    if not new_seed:
        return jsonify({"status": "error", "message": "Generator not initialized."}), 500
        
    csprng = DeterministicCSPRNG(new_seed)

    def generate_stream_forever():
        while True:
            yield csprng.generate(1024)

    return Response(generate_stream_forever(), mimetype='application/octet-stream')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
