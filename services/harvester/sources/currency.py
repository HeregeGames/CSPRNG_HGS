import requests
import json
from .base import BaseSource

class Currency(BaseSource):
    def __init__(self):
        super().__init__()
        self.api_url = "https://api.exchangerate-api.com/v4/latest/USD"
        self.interval = 300  # 5 minutos

    def get_entropy(self) -> bytes | None:
        try:
            self.logger.info("Accessing currency exchange API...", extra={'event': 'fetch_currency_data'})
            response = requests.get(self.api_url, timeout=30)
            response.raise_for_status()
            data = response.json()

            rates_string = json.dumps(data.get('rates', {}), sort_keys=True)
            return rates_string.encode('utf-8')

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error collecting entropy from currency exchange: {e}", extra={'event': 'fetch_currency_failure'})
            return None
