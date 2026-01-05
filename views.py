import streamlit as st
import os
import pandas as pd
import utils
import auth

# --- MODAIS E DIALOGS ---

# 1. Dialog para salvar com campos vazios
@st.dialog("Campos em Branco")
def confirmar_salvamento_incompleto(novo_registro):
    st.warning("Alguns campos do formulário não foram preenchidos.")
    st.write("Deseja salvar o levantamento mesmo assim?")
    
    col_sim, col_nao = st.columns(2)
    
    if col_sim.button("Sim, Salvar", use_container_width=True, type="primary"):
        st.session_state['db_formularios'].append(novo_registro)
        utils.salvar_dados_locais(st.session_state['db_formularios'])
        st.session_state['form_id'] += 1
        st.session_state['sucesso_salvamento'] = True 
        st.rerun()
    
    if col_nao.button("Não, Cancelar", use_container_width=True):
        st.rerun()

# 2. Dialog para excluir registro de levantamento
@st.dialog("Confirmar Exclusão")
def confirmar_exclusao_dialog(index=None, tipo="individual"):
    st.warning("⚠️ Esta ação não pode ser desfeita.")
    senha = st.text_input("Confirme sua senha para prosseguir", type="password")
    if st.button("Confirmar Exclusão", type="primary", use_container_width=True):
        u_db = auth.carregar_usuarios()
        hash_armazenado = u_db.get(st.session_state['usuario_ativo'])
        
        # Verifica Hash
        valido, _ = auth.verificar_senha(senha, hash_armazenado)
        
        if valido:
            if tipo == "individual": st.session_state['db_formularios'].pop(index)
            else: st.session_state['db_formularios'] = []
            utils.salvar_dados_locais(st.session_state['db_formularios'])
            st.rerun()
        else: st.error("Senha incorreta.")

# 3. Dialog para excluir USUÁRIO (Admin)
@st.dialog("Excluir Usuário")
def excluir_usuario_dialog(nome_usuario):
    st.error(f"⚠️ Tem certeza que deseja remover o técnico: **{nome_usuario}**?")
    senha_admin = st.text_input("Senha Master (Admin)", type="password")
    
    if st.button("Confirmar Exclusão", type="primary", use_container_width=True):
        admin_hash = auth.carregar_usuarios().get("Admin")
        valido, _ = auth.verificar_senha(senha_admin, admin_hash)
        
        if valido:
            if auth.excluir_usuario(nome_usuario):
                st.success(f"Usuário {nome_usuario} removido!")
                st.rerun()
            else:
                st.error("Erro ao remover usuário.")
        else:
            st.error("Senha de Admin incorreta.")

@st.dialog("Exclusão Permanente de Arquivo")
def excluir_arquivo_permanente_dialog(caminho_arquivo):
    st.warning(f"🔥 ATENÇÃO: Você vai apagar: **{caminho_arquivo}**")
    st.markdown("Esta ação remove o arquivo físico do servidor. **Não há como desfazer.**")
    
    senha = st.text_input("Senha Master (Admin)", type="password")
    
    if st.button("CONFIRMAR EXCLUSÃO", type="primary", use_container_width=True):
        # 1. Carrega a senha do Admin
        admin_db = auth.carregar_usuarios()
        admin_hash = admin_db.get("Admin")
        
        # 2. Verifica a senha (usando a nova lógica segura do auth.py)
        valido, _ = auth.verificar_senha(senha, admin_hash)
        
        if valido:
            try:
                # 3. Tenta excluir com proteção de erro
                if os.path.exists(caminho_arquivo):
                    os.remove(caminho_arquivo)
                    st.success(f"Arquivo {caminho_arquivo} excluído com sucesso!")
                    
                    # Força uma atualização da página após 1 segundo para limpar o cache visual
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Erro: O arquivo não foi encontrado no disco (talvez já tenha sido excluído).")
            except PermissionError:
                st.error("Erro de Permissão: O arquivo está aberto ou em uso pelo sistema.")
            except Exception as e:
                st.error(f"Erro inesperado ao excluir: {e}")
        else:
            st.error("Senha de Admin incorreta.")

# --- NOVO DIALOG: ALTERAR SENHA ---
@st.dialog("Alterar Senha")
def alterar_senha_dialog():
    usuario = st.session_state['usuario_ativo']
    st.write(f"Alterando senha para: **{usuario}**")
    
    senha_atual = st.text_input("Senha Atual", type="password")
    nova_senha = st.text_input("Nova Senha", type="password")
    confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
    
    if st.button("Atualizar Senha", type="primary", use_container_width=True):
        if not senha_atual or not nova_senha:
            st.error("Preencha todos os campos.")
        elif nova_senha != confirmar_senha:
            st.error("A nova senha e a confirmação não coincidem.")
        else:
            sucesso = auth.alterar_senha(usuario, senha_atual, nova_senha)
            if sucesso:
                st.success("Senha alterada com sucesso!")
                # Opcional: Deslogar para testar a nova senha
            else:
                st.error("A senha atual está incorreta.")

# --- FUNÇÕES DE PÁGINA (Mantenha o resto do código igual ao anterior) ---
def render_configurar_modelo():
    # ... (código existente sem alterações) ...
    st.header("📋 Gerenciamento de Modelo")
    with st.container(border=True):
        st.markdown("### 🔍 Configuração Atual")
        st.write(f"Origem do Modelo: **{st.session_state.get('origem_modelo', 'Padrão')}**")
        if st.session_state.get('origem_modelo') == "Pessoal":
            if st.button("Restaurar para Modelo Padrão"):
                os.remove(utils.get_user_template_path())
                utils.carregar_modelo_atual()
                st.rerun()

    with st.container(border=True):
        st.markdown("### ⏫ Personalizar Meu Modelo")
        st.info("Suba um arquivo Excel (.xlsx) para que o sistema gere formulários baseados nas suas abas e colunas.")
        arq = st.file_uploader("Escolher arquivo", type=["xlsx"])
        if arq:
            path = utils.get_user_template_path()
            with open(path, "wb") as f: f.write(arq.getbuffer())
            st.success("Modelo personalizado carregado!")
            utils.carregar_modelo_atual()
            st.rerun()

def render_preenchimento():
    # ... (código existente sem alterações) ...
    st.header("📝 Registro de Equipamento")
    
    if 'sucesso_salvamento' in st.session_state and st.session_state['sucesso_salvamento']:
        st.success("Levantamento Salvo com Sucesso!")
        st.session_state['sucesso_salvamento'] = False 

    if 'estrutura_modelo' in st.session_state and st.session_state['estrutura_modelo']:
        with st.container(border=True):
            col1, col2 = st.columns(2)
            tipo = col1.selectbox("Selecione o Equipamento", options=list(st.session_state['estrutura_modelo'].keys()))
            uc = col2.text_input("Código da Instalação / UC", placeholder="Ex: 312312", key=f"uc_{st.session_state['form_id']}")
        
        campos = st.session_state['estrutura_modelo'][tipo]
        respostas = {}
        
        with st.form(key=f"form_{st.session_state['form_id']}", border=True):
            st.markdown("#### Detalhamento Técnico")
            cols = st.columns(2)
            for i, c in enumerate(campos):
                target = cols[i % 2]
                if c['tipo'] == 'selecao':
                    respostas[c['nome']] = target.selectbox(c['nome'], options=c['opcoes'])
                else:
                    respostas[c['nome']] = target.text_input(c['nome'])
            
            submit_btn = st.form_submit_button("✅ SALVAR NO LEVANTAMENTO", use_container_width=True, type="primary")

            if submit_btn:
                if uc:
                    novo_registro = {
                        "cod_instalacao": uc, 
                        "tipo_equipamento": tipo, 
                        "data_hora": utils.get_data_hora_br().strftime("%d/%m/%Y %H:%M:%S"), 
                        "dados": respostas
                    }
                    campos_vazios = [k for k, v in respostas.items() if str(v).strip() == ""]
                    if campos_vazios:
                        confirmar_salvamento_incompleto(novo_registro)
                    else:
                        st.session_state['db_formularios'].append(novo_registro)
                        utils.salvar_dados_locais(st.session_state['db_formularios'])
                        st.session_state['form_id'] += 1
                        st.session_state['sucesso_salvamento'] = True 
                        st.rerun()
                else: 
                    st.error("A Unidade Consumidora (UC) é obrigatória.")
    else:
        st.warning("Carregue um modelo em 'Configurar Modelo' antes de iniciar.")

def render_exportar_listar():
    # ... (código existente sem alterações, já com a correção do 'F') ...
    st.header("📊 Seus Levantamentos")
    st.metric("Total de Itens", len(st.session_state['db_formularios']))
    
    if st.session_state['db_formularios']:
        for idx, item in enumerate(st.session_state['db_formularios']):
            with st.container(border=True):
                c_info, c_del = st.columns([0.9, 0.1])
                with c_info:
                    i1, i2, i3 = st.columns(3)
                    i1.markdown(f"**📍 UC:** `{item['cod_instalacao']}`")
                    i2.markdown(f"**⚙️ Tipo:** {item['tipo_equipamento']}")
                    i3.markdown(f"**📅 Data:** {item['data_hora']}")
                with c_del:
                    if st.button("🗑️", key=f"del_{idx}"): confirmar_exclusao_dialog(index=idx)

        st.divider()
        excel_data = utils.exportar_para_excel(st.session_state['db_formularios'])
        ex1, ex2 = st.columns(2)
        with ex1:
            st.download_button("⬇️ Baixar Excel", data=excel_data, file_name="levantamento_poup.xlsx", use_container_width=True, type="primary")
        with ex2:
            target_mail = st.text_input("Enviar para:", placeholder="exemplo@email.com")
            if st.button("📧 Enviar por E-mail", use_container_width=True):
                if target_mail and utils.enviar_email(excel_data, target_mail):
                    st.success("Relatório enviado!")
    else:
        st.info("Nenhum registro encontrado.")

def render_admin_panel():
    # ... (código existente sem alterações) ...
    st.title("⚙️ Administração Geral")
    tab_users, tab_audit, tab_master = st.tabs(["👥 Gestão de Equipe", "📂 Auditoria", "📄 Modelo Padrão"])
    
    with tab_users:
        st.subheader("Novo Técnico")
        with st.container(border=True):
            with st.form("novo_user_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                new_u = c1.text_input("Nome do Usuário")
                new_p = c2.text_input("Senha", type="password")
                
                if st.form_submit_button("Cadastrar Novo Técnico", use_container_width=True, type="primary"):
                    if new_u and new_p:
                        d = auth.carregar_usuarios()
                        # --- MUDANÇA AQUI: CRIPTOGRAFA ANTES DE SALVAR ---
                        d[new_u] = auth.hash_senha(new_p) 
                        # -------------------------------------------------
                        auth.salvar_usuarios(d)
                        st.success("Novo Técnico Cadastrado com Sucesso!")
                    else:
                        st.error("Preencha nome e senha.")

        st.divider()
        st.subheader("Técnicos Cadastrados")
        users = auth.carregar_usuarios()
        if users:
            for nome, senha in users.items():
                with st.container(border=True):
                    col_nome, col_btn = st.columns([0.8, 0.2])
                    col_nome.markdown(f"👤 **{nome}**")
                    if nome != "Admin": 
                        if col_btn.button("Excluir", key=f"del_user_{nome}"):
                            excluir_usuario_dialog(nome)
                    else:
                        col_btn.markdown("*(Admin)*")
        else:
            st.info("Nenhum usuário encontrado.")

    with tab_audit:
        arquivos = sorted([f for f in os.listdir(".") if f.startswith("dados_") and f.endswith(".json")])
        if arquivos:
            sel = st.selectbox("Selecione um arquivo:", arquivos)
            dados_rec = utils.carregar_dados_locais(path_especifico=sel)
            m1, m2 = st.columns(2)
            m1.metric("Registros", len(dados_rec))
            m2.metric("Tamanho", f"{(os.path.getsize(sel)/1024):.2f} KB")
            
            df = pd.DataFrame([{"UC": d.get('cod_instalacao'), "Tipo": d.get('tipo_equipamento'), "Data": d.get('data_hora')} for d in dados_rec])
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            c_act1, c_act2 = st.columns(2)
            rec_excel = utils.exportar_para_excel(dados_rec)
            if rec_excel:
                 c_act1.download_button("⬇️ Baixar Backup", data=rec_excel, file_name=f"backup_{sel}.xlsx", use_container_width=True, type="primary")

            if c_act2.button("🔥 APAGAR DO SERVIDOR", use_container_width=True):
                excluir_arquivo_permanente_dialog(sel)
    
    with tab_master:
        st.subheader("Configuração Estrutural")
        with st.container(border=True):
            st.warning("⚠️ O arquivo padrão define o formulário inicial.")
            mestre = st.file_uploader("Substituir Modelo Base (xlsx)", type=["xlsx"])
            if mestre:
                with open(utils.PLANILHA_PADRAO_ADMIN, "wb") as f: f.write(mestre.getbuffer())
                st.success("Modelo Padrão atualizado!")