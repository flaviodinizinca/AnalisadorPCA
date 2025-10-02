# services/parser.py
import pandas as pd
from .preferencias import carregar_preferencias
from .google_sheets import get_google_sheets_data
from .downloader import ler_csv_da_url
import streamlit as st

def load_all_years() -> dict[str, pd.DataFrame]:
    """
    Carrega todos os arquivos CSV definidos nas preferências a partir de suas URLs
    e os enriquece com os dados do Google Sheets (DFD).
    """
    df_dfd = get_google_sheets_data()
    if df_dfd is None:
        st.error("Não foi possível carregar os dados do Google Sheets. A coluna 'DFD' não estará disponível.")

    preferencias = carregar_preferencias()
    urls = preferencias.get("data_sources", {})
    
    dataframes = {}
    for ano, url in urls.items():
        df = ler_csv_da_url(url)
        if df.empty:
            dataframes[ano] = pd.DataFrame()
            continue

        df.fillna('', inplace=True)

        if df_dfd is not None and 'Identificador da Futura Contratação' in df.columns:
            com_prefixo = df['Identificador da Futura Contratação'].str.contains('-', na=False)
            df['chave_contratacao'] = ''

            df.loc[com_prefixo, 'chave_contratacao'] = df.loc[com_prefixo, 'Identificador da Futura Contratação'].str.split('-', n=1).str[1].str.strip()
            df.loc[~com_prefixo, 'chave_contratacao'] = df.loc[~com_prefixo, 'Identificador da Futura Contratação'].str.strip()

            df = pd.merge(df, df_dfd, on='chave_contratacao', how='left')
            df['DFD'] = df['DFD'].fillna('Não encontrado')
            df.drop(columns=['chave_contratacao'], inplace=True)
        else:
            df['DFD'] = 'N/A'
            
        dataframes[ano] = df
            
    return dataframes