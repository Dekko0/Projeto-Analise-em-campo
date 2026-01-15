import streamlit as st
import json
import os
import bcrypt
from utils import carregar_dados_locais, carregar_modelo_atual

USUARIOS_FILE = "usuarios.json"

# CRIPTOGRAFIA 
def hash_senha(senha_plana):
    return bcrypt.hashpw(senha_plana.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_senha(senha_plana, hash_armazenado):
    try:
        if bcrypt.checkpw(senha_plana.encode('utf-8'), hash_armazenado.encode('utf-8')):
            return True, False
    except (ValueError, TypeError):
        if senha_plana == hash_armazenado:
            return True, True
    return False, False

# PERSISTENCIA
def carregar_usuarios():
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, "r") as f: return json.load(f)
    return {"Admin": "admin2026"}

def salvar_usuarios(usuarios):
    with open(USUARIOS_FILE, "w") as f: json.dump(usuarios, f)

def excluir_usuario(nome_usuario):
    users = carregar_usuarios()
    if nome_usuario in users:
        del users[nome_usuario]
        salvar_usuarios(users)
        return True
    return False

# FUNÇÕES DE LOGICA
def alterar_senha(usuario, senha_atual, nova_senha):
    users = carregar_usuarios()
    hash_armazenado = users.get(usuario)
    valido, _ = verificar_senha(senha_atual, hash_armazenado)
    if valido:
        users[usuario] = hash_senha(nova_senha)
        salvar_usuarios(users)
        return True
    return False

def tela_login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    l, c, r = st.columns([1, 1.2, 1])
    with c:
        with st.container(border=True):
            # icone Google (raio)
            st.markdown("<h1 style='text-align: center; color: #16FA34;'><span class='material-symbols-outlined' style='font-size: 40px;'>bolt</span> PoupEnergia</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center;'>Sistema de Levantamento de Cargas</p>", unsafe_allow_html=True)
            
            u_db = carregar_usuarios()
            u = st.selectbox("Técnico Responsável", options=["Selecione..."] + list(u_db.keys()))
            p = st.text_input("Senha de Acesso", type="password")
            
            # icone no botão
            if st.button("Acessar Sistema", use_container_width=True, type="primary"):
                if u in u_db:
                    is_valid, precisa_migrar = verificar_senha(p, u_db[u])
                    if is_valid:
                        if precisa_migrar:
                            u_db[u] = hash_senha(p)
                            salvar_usuarios(u_db)
                        
                        st.session_state['usuario_ativo'] = u
                        st.session_state['db_formularios'] = carregar_dados_locais()
                        carregar_modelo_atual()
                        st.rerun()
                    else:
                        st.error("Senha inválida.")
                else: 
                    st.error("Usuário não encontrado.")
    st.stop()
