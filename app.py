# app.py
import streamlit as st
import pandas as pd
from services.parser import load_all_years
from services.preferencias import carregar_preferencias, salvar_preferencias
import os

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="Analisador de PCA")

# --- Gerenciamento de Estado e Cache ---

# Inicializa o session_state para guardar as colunas visíveis de cada aba
if 'colunas_visiveis' not in st.session_state:
    st.session_state.colunas_visiveis = {}

@st.cache_data(ttl=3600)  # Cache de 1 hora
def carregar_dados():
    """Carrega os dados de todos os anos e os armazena em cache."""
    return load_all_years()

def refresh_all():
    """Limpa todos os caches e reinicia a aplicação para refletir novas configurações."""
    st.cache_data.clear()
    st.rerun()

# --- Funções de Lógica ---

def adicionar_ano(ano: str, url: str):
    """Adiciona um novo ano e URL às preferências e salva."""
    if ano and url:
        prefs = carregar_preferencias()
        prefs['data_sources'][ano] = url
        salvar_preferencias(prefs)
        st.success(f"Ano {ano} adicionado com sucesso!")
        refresh_all()

def excluir_ano(ano: str):
    """Exclui um ano das preferências e o arquivo de dados associado."""
    if ano:
        prefs = carregar_preferencias()
        if ano in prefs['data_sources']:
            del prefs['data_sources'][ano]
            
            if ano in prefs.get('colunas_visiveis', {}):
                del prefs['colunas_visiveis'][ano]
                
            salvar_preferencias(prefs)
            
            caminho_arquivo = f"data/pca_{ano}.csv"
            if os.path.exists(caminho_arquivo):
                try:
                    os.remove(caminho_arquivo)
                except OSError as e:
                    st.error(f"Não foi possível remover o arquivo local {caminho_arquivo}: {e}")

            st.success(f"Ano {ano} excluído com sucesso!")
            refresh_all()

def salvar_selecao_colunas(ano: str, colunas: list):
    """Salva a seleção de colunas do usuário no arquivo de preferências."""
    prefs = carregar_preferencias()
    prefs['colunas_visiveis'][ano] = colunas
    salvar_preferencias(prefs)
    st.success(f"Seleção de colunas para o ano {ano} salva!")


# --- Interface do Usuário (Sidebar) ---

st.sidebar.title("Opções")

# --- NOVO BOTÃO DE ATUALIZAÇÃO ---
# Adicionamos um botão proeminente para o usuário. Ao ser clicado,
# ele invoca a função `refresh_all`, que é o gatilho central para a nossa lógica.
# O `type="primary"` destaca a importância da ação.
if st.sidebar.button("🔄 Atualizar Todos os Dados", type="primary", help="Recarrega os dados dos CSVs e do Google Sheets"):
    # Envolvemos a chamada em um 'spinner' para dar feedback visual ao usuário,
    # indicando que uma operação demorada está em andamento.
    with st.spinner("Buscando os dados mais recentes..."):
        refresh_all()

st.sidebar.divider()

# Filtros Globais
st.sidebar.header("Filtros")
preferencias = carregar_preferencias()
uasg_padrao = preferencias.get("config", {}).get("uasg_padrao", "")
filtro_uasg = st.sidebar.text_input(
    "Filtrar por UASG (fixo para todas as abas)",
    value=uasg_padrao
)

filtro_geral = st.sidebar.text_input(
    "Filtro por DFD ou Valor Estimado",
    help="Este filtro busca especificamente no 'Número do DFD' ou no 'Valor Total Estimado'."
)

st.sidebar.divider()

# Seção de Gerenciamento
with st.sidebar.expander("Gerenciamento de Dados"):
    with st.form("form_adicionar_ano", clear_on_submit=True):
        st.subheader("Adicionar Novo Ano")
        novo_ano = st.text_input("Ano (ex: 2026)")
        nova_url = st.text_input("URL do arquivo CSV")
        submitted_add = st.form_submit_button("Adicionar")
        if submitted_add:
            adicionar_ano(novo_ano, nova_url)

    anos_existentes = list(preferencias.get("data_sources", {}).keys())
    if anos_existentes:
        with st.form("form_excluir_ano"):
            st.subheader("Excluir um Ano")
            ano_a_excluir = st.selectbox("Selecione o ano para excluir", options=anos_existentes)
            submitted_del = st.form_submit_button("Excluir", type="primary")
            if submitted_del:
                excluir_ano(ano_a_excluir)

# --- Interface Principal ---

st.title("Analisador de Planos de Contratação Anual (PCA)")

df_por_ano = carregar_dados()

if not df_por_ano:
    st.warning("Nenhuma fonte de dados encontrada. Adicione um ano na barra lateral para começar.")
    st.stop()

anos = sorted(df_por_ano.keys())
tabs = st.tabs(anos)

for i, ano in enumerate(anos):
    with tabs[i]:
        st.header(f"Dados de {ano}")
        df = df_por_ano[ano]

        if df.empty:
            st.warning(f"Nenhum dado disponível para o ano de {ano}.")
            continue
            
        with st.expander("Selecionar Colunas Visíveis"):
            todas_colunas = df.columns.tolist()
            colunas_salvas = preferencias.get('colunas_visiveis', {}).get(ano, df.columns.tolist())
            
            colunas_selecionadas = st.multiselect(
                "Escolha as colunas para exibir:",
                options=todas_colunas,
                default=colunas_salvas,
                key=f"multiselect_{ano}"
            )
            if st.button("Salvar Seleção de Colunas", key=f"save_cols_{ano}"):
                salvar_selecao_colunas(ano, colunas_selecionadas)

        df_para_exibir = df[colunas_selecionadas]

        # --- Aplicação dos Filtros ---
        df_filtrado = df_para_exibir.copy()

        if 'UASG' in df_filtrado.columns and filtro_uasg:
            df_filtrado = df_filtrado[df_filtrado['UASG'].str.contains(filtro_uasg, case=False, na=False)]

        if filtro_geral:
            colunas_alvo = ['DFD', 'Valor Total Estimado (R$)']
            colunas_para_busca = [col for col in colunas_alvo if col in df_filtrado.columns]

            if colunas_para_busca:
                mask = df_filtrado[colunas_para_busca].apply(
                    lambda col: col.astype(str).str.contains(filtro_geral, case=False, na=False)
                ).any(axis=1)
                df_filtrado = df_filtrado[mask]

        # --- Exibição dos Dados ---
        st.dataframe(df_filtrado, use_container_width=True)

        # --- Métricas ---
        total_registros = len(df_filtrado)
        valor_total_estimado = 0
        if 'Valor Total Estimado (R$)' in df_filtrado.columns:
            df_filtrado_copy = df_filtrado.copy()
            df_filtrado_copy['Valor Total Estimado (R$)'] = df_filtrado_copy['Valor Total Estimado (R$)'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            
            valor_total_estimado = pd.to_numeric(
                df_filtrado_copy['Valor Total Estimado (R$)'], 
                errors='coerce'
            ).sum()

        col1, col2 = st.columns(2)
        col1.metric("Registros Exibidos", total_registros)
        col2.metric("Valor Total Estimado (Filtrado)", f"R$ {valor_total_estimado:,.2f}")
