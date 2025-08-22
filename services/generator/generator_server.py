import os
import hashlib
from flask import Flask, request, jsonify, Response, send_from_directory
import requests
import time
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import threading
from functools import wraps
import logging
import logging.config
from common.auth import create_hmac, verify_hmac
from common.logging_config import LOGGING_CONFIG, LOG_DIR

# --- Configuração de Logging ---
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Configurações ---
MIXER_SERVER_URL = "http://mixer:5000"
REKEY_INTERVAL_MB = 100 # Re-key after 100MB of data generated

# --- Global CSPRNG Instance ---
# Esta variável irá conter nossa única instância thread-safe do CSPRNG.
csprng_instance = None
csprng_lock = threading.Lock()

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
        logger.info("CSPRNG re-keyed with a new seed.", extra={'event': 'rekey'})

    def generate(self, num_bytes: int) -> bytes:
        with self._lock:
            if self._bytes_generated >= REKEY_INTERVAL_MB * 1024 * 1024:
                logger.warning(f"Rekey threshold of {REKEY_INTERVAL_MB}MB reached. Fetching new seed.", extra={'event': 'rekey_threshold'})
                new_seed = fetch_new_seed_with_retry()
                if new_seed:
                    self._seed = new_seed
                    self._rekey()
                else:
                    raise RuntimeError("Falha crítica ao re-sincronizar a chave do CSPRNG após múltiplas tentativas.")

            chunk = self._encryptor.update(b'\x00' * num_bytes)
            self._bytes_generated += len(chunk)
            return chunk

def fetch_new_seed_with_retry():
    retries = 10
    while retries > 0:
        try:
            hmac_digest = create_hmac(b'')
            headers = {'X-RNG-Auth': hmac_digest}
            
            response = requests.get(f"{MIXER_SERVER_URL}/api/v1/seed", headers=headers, timeout=5)
            response.raise_for_status()
            logger.info("Successfully fetched new seed from mixer.", extra={'event': 'fetch_seed_success'})
            new_seed = response.content
            return new_seed
        except requests.exceptions.RequestException as e:
            retries -= 1
            logger.error(f"Failed to fetch seed from mixer: {e}. Retries left: {retries}", extra={'event': 'fetch_seed_failure'})
            time.sleep(1)
    
    logger.critical("CRITICAL: Could not connect to Mixer after multiple retries.", extra={'event': 'fetch_seed_critical_failure'})
    return None

def initialize_csprng():
    """Inicializa a instância global do CSPRNG em uma thread de background."""
    global csprng_instance
    logger.info("Tentando inicializar a instância global do CSPRNG...")
    initial_seed = fetch_new_seed_with_retry()
    if initial_seed:
        with csprng_lock:
            csprng_instance = DeterministicCSPRNG(initial_seed)
        logger.info("Instância global do CSPRNG inicializada com sucesso.")
    else:
        logger.critical("Falha ao inicializar a instância global do CSPRNG. O serviço não poderá gerar números.")

def auth_required(f):
    """Decorator para proteger endpoints com autenticação HMAC."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('X-RNG-Auth')
        if not auth_header:
            logger.warning("Cabeçalho X-RNG-Auth ausente.", extra={'event': 'auth_failure', 'ip': request.remote_addr, 'path': request.path})
            return jsonify({"error": "Authentication required"}), 401
        
        # Para requisições GET, o HMAC é sobre o corpo vazio. Para POST, é sobre o corpo da requisição.
        data_to_auth = request.get_data() if request.method in ['POST', 'PUT'] else b''

        if not verify_hmac(auth_header, data_to_auth):
            logger.warning("Assinatura HMAC inválida.", extra={'event': 'auth_failure', 'ip': request.remote_addr, 'path': request.path})
            return jsonify({"error": "Invalid authentication"}), 403
        
        return f(*args, **kwargs)
    return decorated_function


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

@app.before_request
def check_csprng_initialized():
    """Antes de cada requisição, verifica se o CSPRNG está pronto."""
    # Permite que os endpoints de health check e logs passem sem a verificação
    if request.endpoint in ['health_check', 'get_audit_log']:
        return
    with csprng_lock:
        if csprng_instance is None:
            logger.error("CSPRNG não está inicializado. Não é possível processar a requisição.", extra={'event': 'csprng_not_ready', 'path': request.path})
            return jsonify({"status": "error", "message": "Serviço do gerador não está pronto. Tente novamente mais tarde."}), 503

@app.route("/api/v1/health", methods=["GET"])
def health_check():
    """Verifica se o serviço está ativo e se o CSPRNG foi inicializado."""
    with csprng_lock:
        is_ready = csprng_instance is not None
    
    if is_ready:
        return jsonify({"status": "ok", "message": "Gerador está pronto."}), 200
    else:
        return jsonify({"status": "error", "message": "Gerador está inicializando."}), 503

@app.route("/api/v1/games/slot_5x3", methods=["GET"])
@auth_required
def get_slot_5x3_numbers():
    audit_log = {
        'event': 'api_request',
        'endpoint': request.path,
        'method': request.method,
        'ip': request.remote_addr
    }
    random_bytes = csprng_instance.generate(15)
    drawn_numbers = [byte % 10 for byte in random_bytes]
    
    audit_log['status'] = 'success'
    logger.info("Slot 5x3 request processed.", extra=audit_log)
    return jsonify({
        "game": "slot_5x3",
        "drawn_numbers": drawn_numbers,
        "status": "success"
    })

@app.route("/api/v1/games/draw_symbols", methods=["POST"])
# @auth_required
def draw_symbols_from_config():
    request_data = request.json
    symbols_config = request_data.get("symbols")
    audit_log = {
        'event': 'api_request',
        'endpoint': request.path,
        'method': request.method,
        'ip': request.remote_addr,
        'request_body': request_data
    }
    
    if not symbols_config or not isinstance(symbols_config, list):
        audit_log.update({'status': 'failure', 'reason': 'Invalid symbols configuration'})
        logger.warning("Invalid symbols configuration provided.", extra=audit_log)
        return jsonify({"status": "error", "message": "Invalid symbols configuration provided."}), 400
    
    try:
        # Usa a instância global diretamente
        drawn_symbols = perform_weighted_draw(symbols_config, 15, csprng_instance)
        
        audit_log.update({'status': 'success', 'result': drawn_symbols})
        logger.info("Symbol draw request processed.", extra=audit_log)
        return jsonify({
            "status": "success",
            "drawn_symbols": drawn_symbols
        })
    except Exception as e:
        audit_log.update({'status': 'failure', 'reason': str(e)})
        logger.error(f"Error during symbol draw: {e}", extra=audit_log, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/v1/stream_entropy", methods=["GET"])
@auth_required
def get_raw_entropy_stream():
    logger.info("Requisição de stream de entropia iniciada.", extra={'event': 'stream_start', 'ip': request.remote_addr})
    def generate_stream_forever():
        while True:
            yield csprng_instance.generate(1024)

    return Response(generate_stream_forever(), mimetype='application/octet-stream')

@app.route("/api/v1/audit/logs", methods=["GET"])
@auth_required
def get_audit_log():
    """Endpoint seguro para baixar o arquivo de log de auditoria."""
    # A autenticação agora é tratada pelo decorator @auth_required
    logger.info("Audit log accessed.", extra={'event': 'audit_log_access', 'ip': request.remote_addr})
    try:
        return send_from_directory(LOG_DIR, 'audit.log', as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "Audit log file not found."}), 404

if __name__ == "__main__":
    logger.info("Generator service starting up...")
    # Inicia a inicialização do CSPRNG em uma thread de background para não bloquear o servidor
    init_thread = threading.Thread(target=initialize_csprng, daemon=True)
    init_thread.start()
    # Inicia o servidor Flask (debug=False é crucial para produção)
    app.run(host="0.0.0.0", port=5001, debug=False)