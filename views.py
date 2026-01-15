import streamlit as st
import os
import pandas as pd
import utils
import auth

# AUXILIARES VISUAIS
def icon_header(icon_name, text):
    """renderiza um cabeçalho H2 com ícone do Google Fonts."""
    st.markdown(f"## <span class='material-symbols-outlined icon-text'>{icon_name}</span> {text}", unsafe_allow_html=True)

def icon_subheader(icon_name, text):
    """renderiza um cabeçalho H3 com ícone do Google Fonts."""
    st.markdown(f"### <span class='material-symbols-outlined icon-text'>{icon_name}</span> {text}", unsafe_allow_html=True)

# MODAIS E DIALOGS

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
        
        keys_to_clear = [k for k in st.session_state.keys() if k.startswith("resp_")]
        for k in keys_to_clear: del st.session_state[k]
        st.rerun()
    
    if col_nao.button("Não, Cancelar", use_container_width=True):
        st.rerun()

@st.dialog("Confirmar Exclusão")
def confirmar_exclusao_dialog(index=None, tipo="individual"):
    st.warning("Esta ação não pode ser desfeita.")
    senha = st.text_input("Confirme sua senha para prosseguir", type="password")
    if st.button("Confirmar Exclusão", type="primary", use_container_width=True):
        u_db = auth.carregar_usuarios()
        hash_armazenado = u_db.get(st.session_state['usuario_ativo'])
        
        valido, _ = auth.verificar_senha(senha, hash_armazenado)
        
        if valido:
            if tipo == "individual": st.session_state['db_formularios'].pop(index)
            else: st.session_state['db_formularios'] = []
            utils.salvar_dados_locais(st.session_state['db_formularios'])
            st.rerun()
        else: st.error("Senha incorreta.")

@st.dialog("Excluir Usuário")
def excluir_usuario_dialog(nome_usuario):
    st.error(f"Tem certeza que deseja remover o técnico: **{nome_usuario}**?")
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
    st.warning(f"ATENÇÃO: Você vai apagar: **{caminho_arquivo}**")
    st.markdown("Esta ação remove o arquivo físico do servidor. **Não há como desfazer.**")
    
    senha = st.text_input("Senha Master (Admin)", type="password")
    
    if st.button("CONFIRMAR EXCLUSÃO", type="primary", use_container_width=True):
        admin_db = auth.carregar_usuarios()
        admin_hash = admin_db.get("Admin")
        valido, _ = auth.verificar_senha(senha, admin_hash)
        
        if valido:
            try:
                if os.path.exists(caminho_arquivo):
                    os.remove(caminho_arquivo)
                    st.success(f"Arquivo {caminho_arquivo} excluído com sucesso!")
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Erro: O arquivo não foi encontrado.")
            except PermissionError:
                st.error("Erro de Permissão: O arquivo está em uso.")
            except Exception as e:
                st.error(f"Erro inesperado ao excluir: {e}")
        else:
            st.error("Senha de Admin incorreta.")

@st.dialog("Alterar Senha")
def alterar_senha_dialog():
    usuario = st.session_state['usuario_ativo']
    st.markdown(f"Alterando senha para: **{usuario}**")
    
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
            else:
                st.error("A senha atual está incorreta.")

# PAGINAS
def render_configurar_modelo():
    # Ícone: settings (Configurações) ou tune (Ajustes)
    icon_header("tune", "Gerenciamento de Modelo")
    
    with st.container(border=True):
        icon_subheader("search", "Configuração Atual")
        st.write(f"Origem do Modelo: **{st.session_state.get('origem_modelo', 'Padrão')}**")
        if st.session_state.get('origem_modelo') == "Pessoal":
            if st.button("Restaurar para Modelo Padrão"):
                path = utils.get_user_template_path()
                if os.path.exists(path): os.remove(path)
                utils.carregar_modelo_atual()
                st.rerun()

    with st.container(border=True):
        icon_subheader("upload_file", "Personalizar Meu Modelo")
        st.info("Suba um arquivo Excel (.xlsx).")
        arq = st.file_uploader("Escolher arquivo", type=["xlsx"])
        if arq:
            path = utils.get_user_template_path()
            with open(path, "wb") as f: f.write(arq.getbuffer())
            st.success("Modelo personalizado carregado!")
            utils.carregar_modelo_atual()
            st.rerun()

def render_preenchimento():
    # Ícone: edit_document (Edição de Documento)
    icon_header("edit_document", "Registro de Equipamento")
    
    if 'sucesso_salvamento' in st.session_state and st.session_state['sucesso_salvamento']:
        st.success("Levantamento Salvo com Sucesso!")
        st.session_state['sucesso_salvamento'] = False 

    if 'step_atual' not in st.session_state: st.session_state['step_atual'] = 0
    
    if 'estrutura_modelo' in st.session_state and st.session_state['estrutura_modelo']:
        with st.container(border=True):
            c_top1, c_top2 = st.columns([2, 1])
            tipo = c_top1.selectbox("Selecione o Equipamento", options=list(st.session_state['estrutura_modelo'].keys()))
            uc = c_top2.text_input("Código da Instalação / UC", placeholder="Ex: 312312", key=f"uc_main_{st.session_state['form_id']}")
            
            # Opções de texto puro, icones apenas ilustrativos fora do componente
            modo_view = st.radio("Estilo de Preenchimento:", ["Formulário", "Sequencial"], horizontal=True)

        campos = st.session_state['estrutura_modelo'][tipo]
        respostas = {}

        if modo_view == "Formulário":
            with st.form(key=f"form_{st.session_state['form_id']}", border=True):
                icon_subheader("description", "Detalhamento Técnico")
                cols = st.columns(2)
                for i, c in enumerate(campos):
                    target = cols[i % 2]
                    key_name = f"resp_{c['nome']}"
                    default_val = st.session_state.get(key_name, "")
                    
                    if c['tipo'] == 'selecao':
                        idx_sel = 0
                        if default_val in c['opcoes']: idx_sel = c['opcoes'].index(default_val)
                        respostas[c['nome']] = target.selectbox(c['nome'], options=c['opcoes'], index=idx_sel)
                    else:
                        respostas[c['nome']] = target.text_input(c['nome'], value=default_val)
                
                st.markdown("<br>", unsafe_allow_html=True)
                submit_btn = st.form_submit_button("Salvar no Levantamento", use_container_width=True, type="primary")

                if submit_btn:
                    processar_salvamento(uc, tipo, respostas)

        else: # Sequencial
            total_passos = len(campos)
            if st.session_state['step_atual'] >= total_passos:
                st.session_state['step_atual'] = 0

            lista_perguntas = [c['nome'] for c in campos]
            passo_selecionado = st.selectbox(
                "Ir para pergunta:", 
                options=range(total_passos), 
                format_func=lambda x: f"{x+1}. {lista_perguntas[x]}",
                index=st.session_state['step_atual']
            )
            
            if passo_selecionado != st.session_state['step_atual']:
                st.session_state['step_atual'] = passo_selecionado
                st.rerun()

            campo_atual = campos[st.session_state['step_atual']]
            key_name = f"resp_{campo_atual['nome']}" 

            with st.container(border=True):
                st.progress((st.session_state['step_atual'] + 1) / total_passos)
                st.caption(f"Pergunta {st.session_state['step_atual'] + 1} de {total_passos}")

                st.markdown(f"<h2 style='color:#4A90E2;'>{campo_atual['nome']}</h2>", unsafe_allow_html=True)
                
                if campo_atual['tipo'] == 'selecao':
                    st.session_state[key_name] = st.selectbox(
                        "Selecione a opção:",
                        options=campo_atual['opcoes'],
                        index=campo_atual['opcoes'].index(st.session_state[key_name]) if key_name in st.session_state and st.session_state[key_name] in campo_atual['opcoes'] else 0,
                        key=key_name + "_widget"
                    )
                    st.session_state[key_name] = st.session_state[key_name + "_widget"]

                else:
                    val_atual = st.session_state.get(key_name, "")
                    novo_valor = st.text_area(
                        "Digite a resposta abaixo:",
                        value=val_atual,
                        height=700,
                        key=key_name + "_widget",
                        placeholder="Escreva aqui..."
                    )
                    st.session_state[key_name] = novo_valor

            c_prev, c_next = st.columns([1, 1])
            
            if st.session_state['step_atual'] > 0:
                if c_prev.button("Anterior", use_container_width=True):
                    st.session_state['step_atual'] -= 1
                    st.rerun()
            
            if st.session_state['step_atual'] < total_passos - 1:
                if c_next.button("Próxima", use_container_width=True):
                    st.session_state['step_atual'] += 1
                    st.rerun()
            else:
                if c_next.button("Finalizar e Salvar", use_container_width=True, type="primary"):
                    respostas_finais = {}
                    for c in campos:
                        k = f"resp_{c['nome']}"
                        respostas_finais[c['nome']] = st.session_state.get(k, "")
                    
                    processar_salvamento(uc, tipo, respostas_finais)

    else:
        st.warning("Carregue um modelo em 'Configurar Modelo' antes de iniciar.")

def processar_salvamento(uc, tipo, respostas):
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
            st.session_state['step_atual'] = 0 
            
            keys_to_clear = [k for k in st.session_state.keys() if k.startswith("resp_")]
            for k in keys_to_clear: del st.session_state[k]

            st.rerun()
    else: 
        st.error("A Unidade Consumidora (UC) é obrigatória.")

def render_exportar_listar():
    # Ícone: table_view (Tabela)
    icon_header("table_view", "Seus Levantamentos")
    st.metric("Total de Itens", len(st.session_state['db_formularios']))
    
    if st.session_state['db_formularios']:
        for idx, item in enumerate(st.session_state['db_formularios']):
            with st.container(border=True):
                c_info, c_del = st.columns([0.9, 0.1])
                with c_info:
                    i1, i2, i3 = st.columns(3)
                    # Usando ícones inline
                    i1.markdown(f"<span class='material-symbols-outlined icon-text' style='font-size:16px'>location_on</span> **UC:** `{item['cod_instalacao']}`", unsafe_allow_html=True)
                    i2.markdown(f"<span class='material-symbols-outlined icon-text' style='font-size:16px'>settings</span> **Tipo:** {item['tipo_equipamento']}", unsafe_allow_html=True)
                    i3.markdown(f"<span class='material-symbols-outlined icon-text' style='font-size:16px'>calendar_today</span> **Data:** {item['data_hora']}", unsafe_allow_html=True)
                with c_del:
                    # Botão Delete simples (ou use type="primary" e um texto curto)
                    if st.button("Excluir", key=f"del_{idx}"): confirmar_exclusao_dialog(index=idx)

        st.divider()
        excel_data = utils.exportar_para_excel(st.session_state['db_formularios'])
        ex1, ex2 = st.columns(2)
        with ex1:
            if excel_data:
                st.download_button("Baixar Excel", data=excel_data, file_name="levantamento_poup.xlsx", use_container_width=True, type="primary")
        with ex2:
            target_mail = st.text_input("Enviar para:", placeholder="exemplo@email.com")
            if st.button("Enviar por E-mail", use_container_width=True):
                if target_mail and excel_data and utils.enviar_email(excel_data, target_mail):
                    st.success("Relatório enviado!")
    else:
        st.info("Nenhum registro encontrado.")

def render_admin_panel():
    # Ícone: admin_panel_settings
    icon_header("admin_panel_settings", "Administração Geral")
    
    # Abas com nomes limpos (não suporta HTML nativamente sem componentes extras, então deixamos texto)
    tab_users, tab_audit, tab_master = st.tabs(["Gestão de Equipe", "Auditoria", "Modelo Padrão"])
    
    with tab_users:
        icon_subheader("person_add", "Novo Técnico")
        with st.container(border=True):
            with st.form("novo_user_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                new_u = c1.text_input("Nome do Usuário")
                new_p = c2.text_input("Senha", type="password")
                
                if st.form_submit_button("Cadastrar Técnico", use_container_width=True, type="primary"):
                    if new_u and new_p:
                        d = auth.carregar_usuarios()
                        d[new_u] = auth.hash_senha(new_p) 
                        auth.salvar_usuarios(d)
                        st.success("Novo Técnico Cadastrado com Sucesso!")
                    else:
                        st.error("Preencha nome e senha.")

        st.divider()
        icon_subheader("group", "Técnicos Cadastrados")
        users = auth.carregar_usuarios()
        if users:
            for nome, senha in users.items():
                with st.container(border=True):
                    col_nome, col_btn = st.columns([0.8, 0.2])
                    col_nome.markdown(f"<span class='material-symbols-outlined icon-text'>person</span> **{nome}**", unsafe_allow_html=True)
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
                 c_act1.download_button("Baixar Backup", data=rec_excel, file_name=f"backup_{sel}.xlsx", use_container_width=True, type="primary")

            if c_act2.button("Apagar do Servidor", use_container_width=True):
                excluir_arquivo_permanente_dialog(sel)
    
    with tab_master:
        icon_subheader("description", "Configuração Estrutural")
        with st.container(border=True):
            st.warning("O arquivo padrão define o formulário inicial.")
            mestre = st.file_uploader("Substituir Modelo Base (xlsx)", type=["xlsx"])
            if mestre:
                with open(utils.PLANILHA_PADRAO_ADMIN, "wb") as f: f.write(mestre.getbuffer())
                st.success("Modelo Padrão atualizado!")
