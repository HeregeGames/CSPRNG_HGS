import requests
import hashlib
import time
from datetime import datetime

# Substitua 'YOUR_API_KEY' pela sua chave de API do Alpha Vantage
API_KEY = "CTEQLIRAO8SZTSNG" 

def get_entropy_from_market_data(api_key, symbol='BTC', market='USD'):
    """
    Coleta dados de cotação de criptomoedas e gera um hash.
    
    Args:
        api_key (str): Chave de API do Alpha Vantage.
        symbol (str): Símbolo da criptomoeda (ex: 'BTC').
        market (str): Símbolo da moeda de referência (ex: 'USD').

    Returns:
        str: O hash SHA-256 gerado ou None em caso de falha.
    """
    try:
        base_url = "https://www.alphavantage.co/query"
        params = {
            "function": "DIGITAL_CURRENCY_INTRADAY",
            "symbol": symbol,
            "market": market,
            "apikey": api_key
        }
        
        print(f"[{datetime.now()}] Acessando dados da API para o símbolo: {symbol}/{market}")
        
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "Error Message" in data:
            print(f"[{datetime.now()}] Erro da API: {data['Error Message']}")
            return None
        
        time_series_key = f"Time Series (Digital Currency Intraday)"
        if time_series_key not in data:
            print(f"[{datetime.now()}] Erro: A chave '{time_series_key}' não está na resposta da API.")
            return None

        latest_timestamp = list(data[time_series_key].keys())[0]
        latest_data = data[time_series_key][latest_timestamp]

        # Use os dados da cotação em USD
        concatenated_data = f"{latest_timestamp}{latest_data['1a. price (USD)']}{latest_data['1b. volume (USD)']}"
        
        print(f"[{datetime.now()}] Dados coletados: {concatenated_data[:50]}...")
        
        data_bytes = concatenated_data.encode('utf-8')
        sha256_hash = hashlib.sha256(data_bytes).hexdigest()
        
        return sha256_hash
        
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] Erro na requisição HTTP: {e}")
        return None
    except Exception as e:
        print(f"[{datetime.now()}] Ocorreu um erro ao processar os dados: {e}")
        return None

if __name__ == "__main__":
    if API_KEY == "SUA_CHAVE_DE_API_AQUI":
        print("Por favor, obtenha e insira sua chave de API do Alpha Vantage no script.")
    else:
        while True:
            generated_hash = get_entropy_from_market_data(API_KEY, symbol='BTC', market='USD')
            
            if generated_hash:
                print("\n--- Hash de Entropia Gerado ---")
                print(generated_hash)
            else:
                print("\nFalha ao gerar o hash. A entropia não foi coletada.")
            
            time.sleep(15)
