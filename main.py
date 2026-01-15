import streamlit as st
import styles
import auth
import views

# configuração da pagina
st.set_page_config(page_title="Levantamento de Cargas", layout="wide", page_icon="⚡")

# aplicar estilos
styles.apply_custom_style()

# inicializar session state
if 'usuario_ativo' not in st.session_state: st.session_state['usuario_ativo'] = None
if 'form_id' not in st.session_state: st.session_state['form_id'] = 0

# 4. verificar login
if not st.session_state['usuario_ativo']:
    auth.tela_login()

# 5. sidebar e navegação
with st.sidebar:
    # icone google energy_savings_leaf
    st.markdown("## <span class='material-symbols-outlined'>energy_savings_leaf</span> PoupEnergia", unsafe_allow_html=True)
    # icone google person
    st.markdown(f"<span class='material-symbols-outlined'>person</span> **{st.session_state['usuario_ativo']}**", unsafe_allow_html=True)
    
    if st.button("Alterar Senha", use_container_width=True):
        views.alterar_senha_dialog()
    
    st.divider()
    
    # opções limpas
    opts = ["Configurar Modelo", "Preenchimento", "Exportar & Listar"]
    if st.session_state['usuario_ativo'] == "Admin": opts.append("Painel Admin")
    
    menu = st.radio("Navegação", opts)
    st.divider()
    
    if st.button("Sair / Logout", use_container_width=True):
        st.session_state['usuario_ativo'] = None
        st.rerun()

# roteamento de paginas
if menu == "Configurar Modelo":
    views.render_configurar_modelo()
elif menu == "Preenchimento":
    views.render_preenchimento()
elif menu == "Exportar & Listar":
    views.render_exportar_listar()
elif menu == "Painel Admin":
    views.render_admin_panel()
