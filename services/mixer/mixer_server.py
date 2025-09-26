import hashlib
import threading
from flask import Flask, request, jsonify, Response
import logging
import logging.config
from functools import wraps

from common.auth import verify_hmac
from common.logging_config import LOGGING_CONFIG

# --- Configuração de Logging ---
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Pool de Entropia ---
# O tamanho do pool é 64 bytes (512 bits), correspondendo à saída do SHA-512.
ENTROPY_POOL_SIZE = 64
entropy_pool = bytearray(ENTROPY_POOL_SIZE)
pool_lock = threading.Lock()
MIN_ENTROPY_SOURCES = 3  # Número mínimo de hashes recebidos antes de fornecer uma semente
entropy_sources_count = 0

def auth_required(f):
    """Decorator para proteger endpoints com autenticação HMAC."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('X-RNG-Auth')
        if not auth_header:
            logger.warning("Cabeçalho X-RNG-Auth ausente.", extra={'event': 'auth_failure', 'ip': request.remote_addr, 'path': request.path})
            return jsonify({"error": "Authentication required"}), 401
        
        data_to_auth = request.get_data() if request.method in ['POST', 'PUT'] else b''

        if not verify_hmac(auth_header, data_to_auth):
            logger.warning("Assinatura HMAC inválida.", extra={'event': 'auth_failure', 'ip': request.remote_addr, 'path': request.path})
            return jsonify({"error": "Invalid authentication"}), 403
        
        return f(*args, **kwargs)
    return decorated_function

@app.route("/api/v1/health", methods=["GET"])
def health_check():
    """Verifica se o serviço está ativo e se o pool de entropia está pronto."""
    with pool_lock:
        is_ready = entropy_sources_count >= MIN_ENTROPY_SOURCES
    
    if is_ready:
        return jsonify({"status": "ok", "message": "Mixer está pronto."}), 200
    else:
        return jsonify({"status": "seeding", "message": f"Mixer está coletando entropia inicial ({entropy_sources_count}/{MIN_ENTROPY_SOURCES} fontes)."}), 503

@app.route("/api/v1/entropy", methods=["POST"])
@auth_required
def add_entropy():
    """Recebe um hash de um harvester e o mistura no pool de entropia."""
    global entropy_pool, entropy_sources_count
    
    new_entropy = request.get_data()
    if len(new_entropy) != 32: # SHA-256
        logger.warning("Entropia recebida com tamanho inválido.", extra={'event': 'invalid_entropy_size', 'size': len(new_entropy), 'ip': request.remote_addr})
        return jsonify({"status": "error", "message": "Entropy must be 32 bytes (256 bits)."}), 400

    with pool_lock:
        # Mistura a nova entropia com o pool atual usando SHA-512
        h = hashlib.sha512()
        h.update(entropy_pool)
        h.update(new_entropy)
        entropy_pool = bytearray(h.digest())
        
        if entropy_sources_count < MIN_ENTROPY_SOURCES:
            entropy_sources_count += 1
        
        logger.info("Nova entropia misturada ao pool.", extra={'event': 'entropy_mixed', 'source_ip': request.remote_addr})
        
    return jsonify({"status": "success", "message": "Entropy mixed."})

@app.route("/api/v1/seed", methods=["GET"])
@auth_required
def get_seed():
    """Fornece uma semente de 64 bytes para o gerador."""
    global entropy_pool
    
    with pool_lock:
        if entropy_sources_count < MIN_ENTROPY_SOURCES:
            logger.warning("Tentativa de obter semente antes do pool estar pronto.", extra={'event': 'seed_request_too_early'})
            return jsonify({"status": "error", "message": "Entropy pool is not sufficiently seeded."}), 503
            
        # Gera a semente de saída como um hash do pool atual.
        # Isso evita expor o estado interno diretamente.
        output_h = hashlib.sha512()
        output_h.update(entropy_pool)
        output_h.update(b'CSPRNG-SEED-V1') # Salt para a saída
        seed = output_h.digest()
        
        # Re-mistura (re-stir) o pool para o próximo pedido, garantindo que o estado futuro seja diferente.
        internal_h = hashlib.sha512()
        internal_h.update(entropy_pool)
        internal_h.update(b'CSPRNG-POOL-V1') # Salt diferente para a atualização interna
        entropy_pool = bytearray(internal_h.digest())
        
        logger.info("Semente fornecida para o gerador.", extra={'event': 'seed_provided'})

    return Response(seed, mimetype='application/octet-stream')

if __name__ == "__main__":
    logger.info("Mixer service starting up...")
    app.run(host="0.0.0.0", port=5000, debug=False)