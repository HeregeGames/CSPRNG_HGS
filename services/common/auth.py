import os
import hmac
import hashlib

# Busca a chave do ambiente. Se não estiver definida, o script falhará.
API_AUTH_KEY_STR = os.getenv("API_AUTH_KEY")

if not API_AUTH_KEY_STR:
    raise ValueError("A variável de ambiente 'API_AUTH_KEY' não está definida. O sistema não pode operar de forma segura.")

API_AUTH_KEY = API_AUTH_KEY_STR.encode('utf-8')

def create_hmac(data: bytes) -> str:
    """Cria um digest HMAC-SHA256 para os dados fornecidos."""
    return hmac.new(API_AUTH_KEY, data, hashlib.sha256).hexdigest()

def verify_hmac(received_hmac: str, data: bytes) -> bool:
    """Verifica um HMAC recebido contra um calculado."""
    expected_hmac = create_hmac(data)
    return hmac.compare_digest(received_hmac, expected_hmac)
