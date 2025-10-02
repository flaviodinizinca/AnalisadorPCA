# services/preferencias.py
import json
import os

PREFERENCIAS_PATH = 'preferencias.json'

def get_default_preferences():
    """Retorna a estrutura padrão de preferências com os dados iniciais."""
    return {
        "data_sources": {},
        "config": {
            "uasg_padrao": "250052", # Mantém um padrão inicial
            "ultima_verificacao_automatica": "2000-01-01"
        },
        "colunas_visiveis": {}
    }

def carregar_preferencias():
    """Carrega as preferências do usuário do arquivo JSON."""
    if not os.path.exists(PREFERENCIAS_PATH):
        default_prefs = get_default_preferences()
        salvar_preferencias(default_prefs)
        return default_prefs
    try:
        with open(PREFERENCIAS_PATH, 'r', encoding='utf-8') as f:
            prefs = json.load(f)
            # Garante que as chaves principais existam para evitar erros
            if 'config' not in prefs:
                prefs['config'] = get_default_preferences()['config']
            if 'colunas_visiveis' not in prefs:
                prefs['colunas_visiveis'] = get_default_preferences()['colunas_visiveis']
            if 'data_sources' not in prefs:
                 prefs['data_sources'] = get_default_preferences()['data_sources']
            # Garante que a chave uasg_padrao exista dentro de config
            if 'uasg_padrao' not in prefs['config']:
                prefs['config']['uasg_padrao'] = get_default_preferences()['config']['uasg_padrao']
            return prefs
    except (json.JSONDecodeError, FileNotFoundError):
        return get_default_preferences()

def salvar_preferencias(preferencias):
    """Salva as preferências do usuário no arquivo JSON."""
    try:
        with open(PREFERENCIAS_PATH, 'w', encoding='utf-8') as f:
            json.dump(preferencias, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar preferências: {e}")