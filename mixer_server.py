import os
import threading
import time
import hashlib
import hmac
from flask import Flask, request, jsonify, Response
from datetime import datetime

app = Flask(__name__)

# --- Configurações ---
SEED_SIZE = 32
ENTROPY_POOL_SIZE = 4096
API_AUTH_KEY = os.getenv("API_AUTH_KEY", "SUA_CHAVE_SECRETA_MUITO_FORTE_AQUI").encode('utf-8')

# Política de Warm-up
MIN_HARVESTER_CONTRIBUTIONS = 3
WARMUP_MAX_SECONDS = 30

# Estado global
entropy_pool = bytearray(os.urandom(ENTROPY_POOL_SIZE))
pool_lock = threading.Lock()
_start_time = time.time()
_contrib_count = 0
_counter = 0

def _increment_counter():
    global _counter
    with pool_lock:
        _counter += 1
        return _counter

def _mix_bytes(data: bytes):
    global entropy_pool
    with pool_lock:
        temp_data = bytearray(data)
        temp_data.extend(entropy_pool)
        temp_data.extend(os.urandom(SEED_SIZE))
        
        for _ in range(5):
            hasher = hashlib.sha512()
            hasher.update(temp_data)
            digest_sha512 = hasher.digest()
            
            hasher = hashlib.sha256()
            hasher.update(temp_data)
            digest_sha256 = hasher.digest()
            
            digest = digest_sha512 + digest_sha256
            
            for i in range(ENTROPY_POOL_SIZE):
                entropy_pool[i] ^= digest[i % len(digest)]
            
            temp_data = bytearray(entropy_pool)

def mix_entropy_periodically():
    while True:
        _mix_bytes(os.urandom(SEED_SIZE))
        time.sleep(3)

# Inicia o thread de mistura de entropia
mixer_thread = threading.Thread(target=mix_entropy_periodically, daemon=True)
mixer_thread.start()

# --- Funções de Autenticação ---
def create_hmac(data: bytes):
    return hmac.new(API_AUTH_KEY, data, hashlib.sha256).hexdigest()

def verify_hmac(received_hmac: str, data: bytes):
    expected_hmac = create_hmac(data)
    return hmac.compare_digest(received_hmac, expected_hmac)


# --- Rotas da API ---
@app.route("/api/v1/seed", methods=["GET"])
def get_seed():
    """
    Retorna um seed de SEED_SIZE bytes após autenticação.
    """
    received_hmac = request.headers.get('X-RNG-Auth')
    if not received_hmac:
        return jsonify({"status": "error", "message": "Authentication header missing"}), 401

    if not verify_hmac(received_hmac, b''):
        return jsonify({"status": "error", "message": "Authentication failed"}), 401

    global _start_time, _contrib_count

    elapsed = time.time() - _start_time
    if _contrib_count < MIN_HARVESTER_CONTRIBUTIONS and elapsed < WARMUP_MAX_SECONDS:
        return jsonify({"status": "warming_up", "message": "Mixer warming up: waiting for external entropy contributions."}), 503

    _increment_counter()
    _mix_bytes(os.urandom(SEED_SIZE))

    with pool_lock:
        seed = bytes(entropy_pool[:SEED_SIZE])
        entropy_pool[:] = entropy_pool[SEED_SIZE:] + entropy_pool[:SEED_SIZE]

    return Response(seed, mimetype='application/octet-stream')

@app.route("/api/v1/entropy", methods=["POST"])
def add_entropy():
    """
    Recebe entropia dos harvesters como bytes brutos após autenticação.
    """
    data = request.get_data()
    received_hmac = request.headers.get('X-RNG-Auth')

    if not received_hmac or not data:
        return jsonify({"status": "error", "message": "Authentication header or data missing"}), 401

    if not verify_hmac(received_hmac, data):
        return jsonify({"status": "error", "message": "Authentication failed"}), 401

    global _contrib_count
    _mix_bytes(data)
    _contrib_count += 1
    return jsonify({"status": "success", "message": f"{len(data)} bytes mixed into pool."})


if __name__ == "__main__":
    if API_AUTH_KEY == b"SUA_CHAVE_SECRETA_MUITO_FORTE_AQUI":
        print("AVISO: Usando a chave secreta padrão. Altere a variável de ambiente 'API_AUTH_KEY' para uma chave segura!")
    print(f"[{datetime.now()}] Mixer iniciado. Pool de entropia de {ENTROPY_POOL_SIZE} bytes inicializado.")
    app.run(host="0.0.0.0", port=5000, debug=True)