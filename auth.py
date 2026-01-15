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

# --- ADICIONE ISSO AO FINAL DO ARQUIVO auth.py ---

def alterar_senha(usuario, senha_atual, nova_senha):
    users = carregar_usuarios()
    hash_armazenado = users.get(usuario)
    
    # Verifica se a senha atual está correta
    valido, _ = verificar_senha(senha_atual, hash_armazenado)
    
    if valido:
        # Atualiza com a nova senha hashada
        users[usuario] = hash_senha(nova_senha)
        salvar_usuarios(users)
        return True
    return False

def tela_login():
    # Cria uma coluna centralizada para ficar visualmente melhor
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("## 🔐 Acesso ao Sistema")
        with st.form(key="login_form"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            
            submit = st.form_submit_button("Entrar", type="primary", use_container_width=True)
            
            if submit:
                users_db = carregar_usuarios()
                hash_armazenado = users_db.get(usuario)
                
                if hash_armazenado:
                    valido, precisa_rehash = verificar_senha(senha, hash_armazenado)
                    if valido:
                        st.success(f"Bem-vindo, {usuario}!")
                        st.session_state['usuario_ativo'] = usuario
                        
                        # Se for senha antiga (texto plano), atualiza para hash agora
                        if precisa_rehash:
                            users_db[usuario] = hash_senha(senha)
                            salvar_usuarios(users_db)
                            
                        st.rerun()
                    else:
                        st.error("Senha incorreta.")
                else:
                    st.error("Usuário não encontrado.")
