import requests
import hashlib
from bs4 import BeautifulSoup
from datetime import datetime

def get_entropy_from_news(url):
    """
    Acessa uma URL de notícias, extrai comentários e gera um hash.

    Args:
        url (str): A URL da página de notícias.

    Returns:
        str: O hash SHA-256 gerado a partir dos comentários ou None em caso de falha.
    """
    try:
        # 1. Faz a requisição HTTP para a URL
        print(f"[{datetime.now()}] Acessando a URL: {url}")
        headers = {'User-Agent': 'Mozilla/5.0'} # Headers para evitar bloqueio
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Lança um erro para status de resposta ruins (4xx ou 5xx)

        # 2. Analisa o conteúdo HTML com BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # 3. Encontra e coleta os comentários
        # Esta é a parte mais crítica e pode precisar de ajuste para cada site.
        # Exemplo: buscando divs com uma classe específica de comentário.
        comments = soup.find_all('div', class_='comment-text')

        if not comments:
            print("Nenhum comentário encontrado. Tentando outra classe...")
            # Tentativa de buscar por outra classe comum
            comments = soup.find_all('p', class_='comment-body')
            
        if not comments:
            print("Nenhum comentário encontrado. Retornando None.")
            return None

        # 4. Concatena o texto dos comentários
        concatenated_text = " ".join([comment.get_text(strip=True) for comment in comments])
        
        if not concatenated_text:
            print("Comentários encontrados, mas sem texto. Retornando None.")
            return None
            
        print(f"[{datetime.now()}] Texto coletado. Tamanho: {len(concatenated_text)} caracteres.")

        # 5. Converte o texto para bytes e gera o hash SHA-256
        data_bytes = concatenated_text.encode('utf-8')
        sha256_hash = hashlib.sha256(data_bytes).hexdigest()
        
        return sha256_hash

    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        return None
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        return None

if __name__ == "__main__":
    # URL de exemplo (substitua por uma real)
    example_url = "https://www.exemplo-de-noticias.com/noticia-com-comentarios"
    
    generated_hash = get_entropy_from_news(example_url)
    
    if generated_hash:
        print("\n--- Hash de Entropia Gerado ---")
        print(generated_hash)
    else:
        print("\nFalha ao gerar o hash. A entropia não foi coletada.")
