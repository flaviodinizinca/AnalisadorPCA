# services/google_sheets.py
import streamlit as st
import gspread
import pandas as pd
from typing import Optional

# Constantes
SHEET_ID = '1bb-U0KZTX0YEUTdPVv93Uqc4tTqtaxZWgkWDlPdiJbM'
WORKSHEET_NAME = 'dados'
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_data(ttl=3600) # Cache de 1 hora
def get_google_sheets_data() -> Optional[pd.DataFrame]:
    """
    Conecta-se à API do Google Sheets usando as credenciais do Streamlit Secrets,
    busca os dados e os retorna como um DataFrame.
    """
    try:
        # Usa as credenciais do Streamlit Secrets
        creds = st.secrets["gcp_service_account"]
        client = gspread.service_account_from_dict(creds, scopes=SCOPES)
        
        sheet = client.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)
        records = sheet.get_all_records()

        if not records:
            st.warning(f"Nenhum dado encontrado na aba '{WORKSHEET_NAME}' da planilha.")
            return pd.DataFrame()

        df = pd.DataFrame(records)

        # Colunas esperadas
        col_contratacao = 'Número da contratação'
        col_status = 'Status da contratação'
        col_dfd = 'Nº DFD'
        
        colunas_necessarias = [col_contratacao, col_status, col_dfd]
        if not all(col in df.columns for col in colunas_necessarias):
            st.error("Uma ou mais colunas necessárias não foram encontradas na planilha do Google Sheets.")
            return None

        df_final = df[colunas_necessarias].copy()
        df_final.rename(columns={
            col_contratacao: 'chave_contratacao',
            col_status: 'Status',
            col_dfd: 'DFD'
        }, inplace=True)

        # Limpeza e normalização
        df_final['chave_contratacao'] = df_final['chave_contratacao'].astype(str).str.strip()
        df_final['Status'] = df_final['Status'].astype(str).str.strip().fillna('Não informado')
        df_final['DFD'] = df_final['DFD'].astype(str).str.strip()
        
        df_final = df_final[df_final['chave_contratacao'] != ''].copy()
        df_final.drop_duplicates(subset=['chave_contratacao'], inplace=True)

        return df_final

    except Exception as e:
        st.error(f"Erro ao conectar ou buscar dados do Google Sheets: {e}")
        return None