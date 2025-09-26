# Desenvolvido por: Leandro M. da Costa (HG Studios)
#

import requests
import hashlib
import time
import logging
import logging.config
from common.auth import create_hmac
from common.logging_config import LOGGING_CONFIG

# --- Configuration ---
MIXER_SERVER_URL = "http://mixer:5000"
# A public radio stream URL. Streams with less compression or more talk/variety are often better sources.
RADIO_STREAM_URL = "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service"
CHUNK_SIZE = 4096  # How many bytes to read from the stream at a time
CAPTURE_DURATION_SECONDS = 2  # Capture 2 seconds of audio for each hash

# --- Logging Configuration ---
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

def send_hash_to_mixer(hash_value):
    """Sends the generated hash to the Mixer Server with HMAC authentication."""
    url = f"{MIXER_SERVER_URL}/api/v1/entropy"
    try:
        data_bytes = bytes.fromhex(hash_value)
        hmac_digest = create_hmac(data_bytes)
        
        headers = {'X-RNG-Auth': hmac_digest}
        response = requests.post(url, data=data_bytes, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info("Hash sent to mixer successfully.", extra={'event': 'send_hash_success', 'response': response.json()})
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending hash to mixer: {e}", extra={'event': 'send_hash_failure'})

def extract_lsb_entropy(audio_data: bytes) -> bytes:
    """
    Extracts the Least Significant Bit (LSB) from each byte of the audio data.
    This concentrates the noise, which is a better source of entropy than raw audio.
    """
    bits = [byte & 1 for byte in audio_data]

    # Pack bits into a bytearray for hashing
    entropy_bytes = bytearray()
    for i in range(0, len(bits), 8):
        byte_chunk = bits[i:i+8]
        byte_val = 0
        for bit in byte_chunk:
            byte_val = (byte_val << 1) | bit
        entropy_bytes.append(byte_val)
        
    return bytes(entropy_bytes)

def get_entropy_from_radio():
    """Captures audio from an online radio stream and extracts entropy from it."""
    try:
        logger.info("Connecting to radio stream...", extra={'event': 'radio_stream_connect', 'url': RADIO_STREAM_URL})
        with requests.get(RADIO_STREAM_URL, stream=True, timeout=10) as response:
            response.raise_for_status()
            
            audio_data = bytearray()
            start_time = time.time()
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                audio_data.extend(chunk)
                if time.time() - start_time > CAPTURE_DURATION_SECONDS:
                    break
            
            if not audio_data:
                logger.warning("No data received from radio stream.", extra={'event': 'radio_stream_empty'})
                return None

            noise_data = extract_lsb_entropy(audio_data)
            return hashlib.sha256(noise_data).hexdigest()

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to radio stream: {e}", extra={'event': 'radio_stream_failure'})
        return None

if __name__ == "__main__":
    logger.info("Radio harvester starting up...")
    while True:
        if generated_hash := get_entropy_from_radio():
            send_hash_to_mixer(generated_hash)
        time.sleep(60) # 1 minute interval