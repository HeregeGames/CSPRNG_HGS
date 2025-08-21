import os
import hashlib
from flask import Flask, request, jsonify, Response
import requests
import time
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import threading
import json
import random
import hmac

app = Flask(__name__)

# --- Configurações ---
MIXER_SERVER_URL = "http://mixer:5000"
API_AUTH_KEY = os.getenv("API_AUTH_KEY", "f8a2344b1d77a87560dd8f8d40982ff3b4fcb0e0b4dd0cb6a8f722a3ba4d274c").encode('utf-8')
REKEY_INTERVAL_MB = 100

class DeterministicCSPRNG:
    def __init__(self, seed: bytes):
        self._seed = seed
        self._bytes_generated = 0
        self._lock = threading.Lock()
        self._rekey()

    def _rekey(self):
        """Deriva uma nova chave e nonce da semente para ressincronização."""
        self._key = hashlib.sha256(self._seed).digest()
        self._nonce = hashlib.sha512(self._seed).digest()[32:48]
        self._backend = default_backend()
        
        cipher = Cipher(algorithms.AES(self._key), modes.CTR(self._nonce), backend=self._backend)
        self._encryptor = cipher.encryptor()
        
        self._bytes_generated = 0
        print(f"[{datetime.now()}] CSPRNG re-sincronizado com uma nova semente.")

    def generate(self, num_bytes: int) -> bytes:
        with self._lock:
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
            hmac_digest = hmac.new(API_AUTH_KEY, b'', hashlib.sha256).hexdigest()
            headers = {'X-RNG-Auth': hmac_digest}
            
            response = requests.get(f"{MIXER_SERVER_URL}/api/v1/seed", headers=headers, timeout=5)
            response.raise_for_status()
            
            new_seed = response.content
            return new_seed
        except requests.exceptions.RequestException as e:
            retries -= 1
            print(f"[{datetime.now()}] Erro ao buscar semente do Mixer: {e}. Tentando novamente... ({retries} retries restantes)")
            time.sleep(1)
    
    print(f"[{datetime.now()}] Falha crítica: Não foi possível conectar ao Mixer após várias tentativas.")
    return None

def perform_weighted_draw(symbols: list, num_draws: int, csprng: DeterministicCSPRNG):
    """
    Realiza um sorteio ponderado de símbolos usando o CSPRNG.
    """
    drawn_symbols = []
    
    weighted_list = []
    for symbol in symbols:
        weighted_list.extend([symbol['name']] * symbol['weight'])
        
    required_bytes = num_draws * 4
    random_bytes = csprng.generate(required_bytes)
    
    list_size = len(weighted_list)
    
    for i in range(num_draws):
        sub_bytes = random_bytes[i*4 : (i+1)*4]
        random_value = int.from_bytes(sub_bytes, 'big')
        
        index = random_value % list_size
        drawn_symbols.append(weighted_list[index])
    
    return drawn_symbols

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

@app.route("/api/v1/games/draw_symbols", methods=["POST"])
def draw_symbols_from_config():
    request_data = request.json
    symbols_config = request_data.get("symbols")
    
    if not symbols_config or not isinstance(symbols_config, list):
        return jsonify({"status": "error", "message": "Invalid symbols configuration provided."}), 400
    
    new_seed = fetch_new_seed_with_retry()
    if not new_seed:
        return jsonify({"status": "error", "message": "Generator not initialized."}), 500
    
    try:
        csprng = DeterministicCSPRNG(new_seed)
        drawn_symbols = perform_weighted_draw(symbols_config, 15, csprng)
        
        return jsonify({
            "status": "success",
            "drawn_symbols": drawn_symbols
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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
    if API_AUTH_KEY == b"f8a2344b1d77a87560dd8f8d40982ff3b4fcb0e0b4dd0cb6a8f722a3ba4d274c":
        print("AVISO: Usando a chave secreta padrão. Altere a variável de ambiente 'API_AUTH_KEY' para uma chave segura!")
    app.run(host="0.0.0.0", port=5001, debug=True)