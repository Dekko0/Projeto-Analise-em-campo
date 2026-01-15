import streamlit as st
import bcrypt
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONEXÃO ---
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

# --- FUNÇÕES DE SENHA (MANTÉM IGUAL) ---
def hash_senha(senha_plana):
    return bcrypt.hashpw(senha_plana.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_senha(senha_plana, hash_armazenado):
    try:
        if bcrypt.checkpw(senha_plana.encode('utf-8'), hash_armazenado.encode('utf-8')):
            return True, False
    except (ValueError, TypeError):
        # Fallback para senhas antigas não criptografadas
        if senha_plana == hash_armazenado:
            return True, True
    return False, False

# --- PERSISTÊNCIA NO GOOGLE SHEETS ---

def carregar_usuarios():
    conn = get_connection()
    try:
        df = conn.read(worksheet="Usuarios", ttl=0)
        if df.empty:
            return {"Admin": "admin2026"} # Usuário padrão se falhar
            
        # Converte DataFrame para Dicionário {Usuario: Hash}
        # Assume que na planilha tem colunas: "usuario" e "senha_hash"
        return pd.Series(df.senha_hash.values, index=df.usuario).to_dict()
    except:
        # Se a aba não existir ou estiver vazia, cria o padrão
        salvar_usuarios({"Admin": "admin2026"})
        return {"Admin": "admin2026"}

def salvar_usuarios(dict_usuarios):
    conn = get_connection()
    
    # Transforma o dicionário {"user": "hash"} em DataFrame
    lista_users = [{"usuario": k, "senha_hash": v} for k, v in dict_usuarios.items()]
    df = pd.DataFrame(lista_users)
    
    conn.update(worksheet="Usuarios", data=df)

def excluir_usuario(nome_usuario):
    users = carregar_usuarios()
    if nome_usuario in users:
        del users[nome_usuario]
        salvar_usuarios(users)
        return True
    return False

# ... (Função alterar_senha e tela_login continuam iguais) ...
