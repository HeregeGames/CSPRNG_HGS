import irc.bot
import irc.client
import irc.connection
import hashlib
import time
import threading
import ssl
from datetime import datetime

# Importe a biblioteca para fazer requisições HTTP
# Se você ainda não a tem, instale com: pip install requests
import requests 

class IRCMessageHarvester(irc.bot.SingleServerIRCBot):
    def __init__(self, channels, nickname, server, port=6697, mixer_url=None):
        ssl_context = ssl.create_default_context()
        factory = irc.connection.Factory(wrapper=lambda s: ssl_context.wrap_socket(s, server_hostname=server))
        
        irc.bot.SingleServerIRCBot.__init__(
            self, [(server, port)], nickname, nickname, connect_factory=factory
        )
        self.channels_to_join = channels
        self.mixer_url = mixer_url
        self.collected_messages = []
        self.collection_interval = 10
        self.collection_time_seconds = 10 # Aumentei o tempo de coleta para 10 segundos
        self.is_collecting = False
        self.last_collection_time = 0

    def on_welcome(self, c, e):
        print(f"[{datetime.now()}] Conectado ao servidor IRC. Entrando nos canais...")
        for channel in self.channels_to_join:
            c.join(channel)
        
        collection_thread = threading.Thread(target=self.continuous_collection_loop)
        collection_thread.daemon = True
        collection_thread.start()

    def on_pubmsg(self, c, e):
        if self.is_collecting:
            message = e.arguments[0]
            full_message = f"{e.source.nick}: {message}"
            self.collected_messages.append(full_message)

    def continuous_collection_loop(self):
        while True:
            time_to_wait = self.collection_interval - (time.time() - self.last_collection_time)
            if time_to_wait > 0:
                time.sleep(time_to_wait)
            
            self.last_collection_time = time.time()
            self.is_collecting = True
            print(f"[{datetime.now()}] Coletando mensagens por {self.collection_time_seconds} segundos...")
            time.sleep(self.collection_time_seconds)
            self.is_collecting = False
            
            generated_hash = self.generate_hash()
            self.collected_messages = []
            
            if generated_hash:
                print(f"\n--- Hash de Entropia Gerado ---")
                print(generated_hash)
                
                if self.mixer_url:
                    try:
                        response = requests.post(f"{self.mixer_url}/api/v1/entropy", json={"hash": generated_hash})
                        response.raise_for_status()
                        print(f"[{datetime.now()}] Hash enviado com sucesso para o Mixer.")
                    except requests.exceptions.RequestException as e:
                        print(f"[{datetime.now()}] Erro ao enviar hash para o Mixer: {e}")
            else:
                print(f"[{datetime.now()}] Falha ao gerar o hash. A entropia não foi coletada.")
    
    def generate_hash(self):
        concatenated_text = ""
        
        if self.collected_messages:
            concatenated_text = " ".join(self.collected_messages)
            print(f"[{datetime.now()}] Texto coletado. Tamanho: {len(concatenated_text)} caracteres.")
        else:
            # Fallback: Se não houver mensagens, use o timestamp como fonte de entropia
            concatenated_text = f"fallback_{time.time()}"
            print(f"[{datetime.now()}] Nenhum comentário coletado. Usando timestamp como fallback.")
        
        data_bytes = concatenated_text.encode('utf-8')
        sha256_hash = hashlib.sha256(data_bytes).hexdigest()
        
        return sha256_hash

if __name__ == "__main__":
    server = "irc.libera.chat"
    port = 6697
    channels = ["#libera-chat"] # Mudei para um canal mais movimentado
    nickname = f"EntropyHarvester{int(time.time())}"
    
    mixer_server = None 

    try:
        harvester = IRCMessageHarvester(channels, nickname, server, port, mixer_url=mixer_server)
        harvester.start()
            
    except irc.client.ServerConnectionError as e:
        print(f"Erro de conexão com o servidor IRC: {e}")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
