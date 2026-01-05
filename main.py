import streamlit as st
import styles
import auth
import views

# 1. Configuração da Página
st.set_page_config(page_title="Levantamento de Cargas", layout="wide", page_icon="⚡")

# 2. Aplicar Estilos (Padrão)
styles.apply_custom_style()

# 3. Inicializar Session State
if 'usuario_ativo' not in st.session_state: st.session_state['usuario_ativo'] = None
if 'form_id' not in st.session_state: st.session_state['form_id'] = 0

# 4. Verificar Login
if not st.session_state['usuario_ativo']:
    auth.tela_login()

# 5. Sidebar e Navegação
with st.sidebar:
    st.title("PoupEnergia")
    st.write(f"👤 **{st.session_state['usuario_ativo']}**")
    
    # --- NOVO BOTÃO DE ALTERAR SENHA ---
    if st.button("🔑 Alterar Senha", use_container_width=True):
        views.alterar_senha_dialog()
    # -----------------------------------
    
    st.divider()
    
    opts = ["📋 Configurar Modelo", "📝 Preenchimento", "📤 Exportar & Listar"]
    if st.session_state['usuario_ativo'] == "Admin": opts.append("⚙️ Painel Admin")
    
    menu = st.radio("Navegação", opts)
    st.divider()
    
    if st.button("Sair", use_container_width=True):
        st.session_state['usuario_ativo'] = None
        st.rerun()

# 6. Roteamento de Páginas
if menu == "📋 Configurar Modelo":
    views.render_configurar_modelo()
elif menu == "📝 Preenchimento":
    views.render_preenchimento()
elif menu == "📤 Exportar & Listar":
    views.render_exportar_listar()
elif menu == "⚙️ Painel Admin":
    views.render_admin_panel()