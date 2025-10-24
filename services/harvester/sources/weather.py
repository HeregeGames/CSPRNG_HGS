import requests
from .base import BaseSource

class Weather(BaseSource):
    def __init__(self):
        super().__init__()
        self.api_url = "https://api.open-meteo.com/v1/forecast"
        self.cities = [
            {"name": "London", "latitude": 51.5074, "longitude": -0.1278},
            {"name": "New York", "latitude": 40.7128, "longitude": -74.0060},
            {"name": "Tokyo", "latitude": 35.6895, "longitude": 139.6917},
            {"name": "Sydney", "latitude": -33.8688, "longitude": 151.2093},
            {"name": "Florianopolis", "latitude": -27.5935, "longitude": -48.5585},
        ]
        self.interval = 300  # 5 minutos

    def get_entropy(self) -> bytes | None:
        concatenated_data = ""
        for city in self.cities:
            params = {
                "latitude": city['latitude'],
                "longitude": city['longitude'],
                "current_weather": True,
                "timezone": "auto"
            }
            try:
                response = requests.get(self.api_url, params=params, timeout=20)
                response.raise_for_status()
                data = response.json()
                if 'current_weather' in data:
                    weather = data['current_weather']
                    concatenated_data += f"{weather['temperature']}{weather['windspeed']}{weather['weathercode']}"
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed for {city['name']}: {e}.", extra={'event': 'fetch_weather_city_failure', 'city': city['name']})
                continue

        if not concatenated_data:
            self.logger.warning("Failed to collect weather data from any city.", extra={'event': 'fetch_weather_all_failed'})
            return None

        return concatenated_data.encode('utf-8')
