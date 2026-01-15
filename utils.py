import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import json
from streamlit_gsheets import GSheetsConnection

# configuração de data/hora
def get_data_hora_br():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso_br)

# --- FUNÇÕES DE BANCO DE DADOS (GOOGLE SHEETS) ---

def get_connection():
    # Cria a conexão usando a biblioteca oficial
    return st.connection("gsheets", type=GSheetsConnection)

def carregar_dados_locais():
    """Lê os levantamentos da aba 'Levantamentos'"""
    conn = get_connection()
    try:
        # Lê a aba correta. O ttl=0 garante que não pegue dados velhos do cache
        df = conn.read(worksheet="Levantamentos", ttl=0)
        
        # Se a planilha estiver vazia, retorna lista vazia
        if df.empty:
            return []
            
        # Converte o DataFrame de volta para a lista de dicionários que o sistema usa
        # Precisamos converter a string JSON da coluna 'dados' de volta para dict
        lista_dados = df.to_dict(orient="records")
        
        for item in lista_dados:
            if isinstance(item.get("dados"), str):
                try:
                    item["dados"] = json.loads(item["dados"])
                except:
                    item["dados"] = {}
        
        return lista_dados
        
    except Exception as e:
        # Se der erro (ex: aba não existe ainda), retorna vazio
        return []

def salvar_dados_locais(lista_atualizada_formularios):
    """
    Recebe a lista completa de formulários e sobrescreve a planilha.
    Para sistemas pequenos, isso é seguro e fácil.
    """
    conn = get_connection()
    
    # Prepara os dados para salvar
    # Precisamos converter o dicionário de respostas ('dados') em uma string JSON
    # para caber em uma única célula do Excel/Sheets
    lista_copia = []
    for item in lista_atualizada_formularios:
        novo_item = item.copy()
        if isinstance(novo_item.get("dados"), dict):
            novo_item["dados"] = json.dumps(novo_item["dados"], ensure_ascii=False)
        lista_copia.append(novo_item)
    
    df = pd.DataFrame(lista_copia)
    
    # Escreve no Sheets (sobrescreve os dados antigos)
    conn.update(worksheet="Levantamentos", data=df)
