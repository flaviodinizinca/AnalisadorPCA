# services/downloader.py
import pandas as pd
import requests
from .preferencias import carregar_preferencias

def download_csv_por_ano(ano_especifico=None):
    """
    Lê os arquivos CSV das URLs e os salva localmente.
    Se um ano específico for fornecido, baixa apenas os dados para aquele ano.
    """
    preferencias = carregar_preferencias()
    urls = preferencias.get("data_sources", {})
    
    urls_a_processar = {ano_especifico: urls[ano_especifico]} if ano_especifico and ano_especifico in urls else urls

    for ano, url in urls_a_processar.items():
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            # Salva o conteúdo em um arquivo
            with open(f"data/pca_{ano}.csv", "w", encoding="utf-8") as f:
                f.write(response.text)
                
        except requests.RequestException as e:
            print(f"Erro ao baixar dados de {ano}: {e}")

def ler_csv_da_url(url: str) -> pd.DataFrame:
    """
    Lê um arquivo CSV diretamente de uma URL e o retorna como um DataFrame.
    """
    try:
        return pd.read_csv(url, sep=';', encoding='utf-8', dtype=str)
    except Exception as e:
        st.error(f"Erro ao ler dados da URL: {e}")
        return pd.DataFrame()