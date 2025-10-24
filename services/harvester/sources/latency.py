import time
import ping3
from .base import BaseSource

class Latency(BaseSource):
    def __init__(self):
        super().__init__()
        self.servers_to_ping = [
            "8.8.8.8",        # Google DNS
            "1.1.1.1",        # Cloudflare DNS
            "9.9.9.9",        # Quad9 DNS
            "208.67.222.222"  # OpenDNS
        ]
        self.interval = 10  # 10 segundos

    def get_entropy(self) -> bytes | None:
        combined_data = ""
        for server in self.servers_to_ping:
            try:
                # ping3 requer privilégios, o que é resolvido no Dockerfile
                delay = ping3.ping(server, unit='ms', timeout=1)
                if delay is not None and delay is not False:
                    # Usamos a representação de string de alta precisão do float
                    combined_data += f"{delay:.15f}"
                    self.logger.debug(f"Ping to {server} successful: {delay:.2f}ms")
            except Exception as e:
                # Captura permissões ou outros erros de ping
                self.logger.warning(f"Error pinging {server}: {e}", extra={'event': 'ping_failure', 'server': server})

        if not combined_data:
            self.logger.warning("Failed to collect any latency data.", extra={'event': 'latency_collection_failed'})
            return None

        return combined_data.encode('utf-8')
