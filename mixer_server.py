import os
import threading
import time
import hashlib
from flask import Flask, request, jsonify, Response
from datetime import datetime

app = Flask(__name__)

# Configurações
SEED_SIZE = 32                 # Tamanho da semente em bytes para o gerador
ENTROPY_POOL_SIZE = 4096       # Tamanho do pool de entropia

# Política de Warm-up
MIN_HARVESTER_CONTRIBUTIONS = 3
WARMUP_MAX_SECONDS = 30

# Estado global
entropy_pool = bytearray(os.urandom(ENTROPY_POOL_SIZE))
pool_lock = threading.Lock()
_start_time = time.time()
_contrib_count = 0
_counter = 0  # Contador monotônico para unicidade

def _increment_counter():
    """Incrementa o contador global de forma segura."""
    global _counter
    with pool_lock:
        _counter += 1
        return _counter

def _mix_bytes(data: bytes):
    """
    Mistura dados no pool usando um algoritmo de mistura robusto (hash + XOR com múltiplas iterações).
    """
    global entropy_pool
    with pool_lock:
        # Use o pool, a nova entropia e um sal temporário para misturar o hash
        hasher = hashlib.sha512()
        hasher.update(entropy_pool)
        hasher.update(data)
        hasher.update(os.urandom(SEED_SIZE))
        
        # Mistura em várias iterações para garantir a difusão da entropia
        for _ in range(5):
            hasher.update(hasher.digest())
        
        digest = hasher.digest()

        # XOR o hash final com o pool para uma mistura completa e uniforme
        for i in range(ENTROPY_POOL_SIZE):
            entropy_pool[i] ^= digest[i % len(digest)]
        
        
def mix_entropy_periodically():
    """Re-mistura o pool com entropia local (chamada interna / periódica)."""
    while True:
        _mix_bytes(os.urandom(SEED_SIZE))
        time.sleep(3)

# Inicia o thread de mistura de entropia
mixer_thread = threading.Thread(target=mix_entropy_periodically, daemon=True)
mixer_thread.start()


@app.route("/api/v1/seed", methods=["GET"])
def get_seed():
    """
    Retorna um seed de SEED_SIZE bytes.
    Enquanto o mixer estiver em warm-up, retorna 503.
    """
    global _start_time, _contrib_count

    elapsed = time.time() - _start_time
    if _contrib_count < MIN_HARVESTER_CONTRIBUTIONS and elapsed < WARMUP_MAX_SECONDS:
        return jsonify({"status": "warming_up", "message": "Mixer warming up: waiting for external entropy contributions."}), 503

    _increment_counter()
    _mix_bytes(os.urandom(SEED_SIZE))

    with pool_lock:
        seed = bytes(entropy_pool[:SEED_SIZE])
        # Rotaciona o pool para que a semente recém-usada não seja reutilizada imediatamente
        entropy_pool[:] = entropy_pool[SEED_SIZE:] + entropy_pool[:SEED_SIZE]

    return Response(seed, mimetype='application/octet-stream')


@app.route("/api/v1/entropy", methods=["POST"])
def add_entropy():
    """
    Recebe entropia dos harvesters como bytes brutos.
    """
    global _contrib_count
    data = request.get_data()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    _mix_bytes(data)

    _contrib_count += 1
    return jsonify({"status": "success", "message": f"{len(data)} bytes mixed into pool."})


if __name__ == "__main__":
    print(f"[{datetime.now()}] Mixer iniciado. Pool de entropia de {ENTROPY_POOL_SIZE} bytes inicializado.")
    app.run(host="0.0.0.0", port=5000, debug=True)
