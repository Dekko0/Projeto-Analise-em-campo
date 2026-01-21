import streamlit as st
import os
import pandas as pd
import utils
import auth
from collections import defaultdict


# --- AUXILIARES VISUAIS & UI ---
def section_title(icon, text):
    """Renderiza um título de seção com espaçamento e estilo corporativo."""
    st.markdown(f"""
    <div style="margin-top: 20px; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
        <span class='material-symbols-outlined' style='font-size: 24px; color: #fafafa;'>{icon}</span>
        <span style='font-size: 18px; font-weight: 600; color: #fafafa;'>{text}</span>
    </div>
    """, unsafe_allow_html=True)

def main_header(icon, text):
    """Cabeçalho principal da página."""
    st.markdown(f"""
    <div style="border-bottom: 1px solid #ddd; padding-bottom: 10px; margin-bottom: 20px;">
        <h2 style='display: flex; align-items: center; gap: 10px; margin: 0; font-size: 26px;'>
            <span class='material-symbols-outlined' style='font-size: 32px;'>{icon}</span> {text}
        </h2>
    </div>
    """, unsafe_allow_html=True)

# --- MODAIS E DIALOGS (Lógica preservada, ajuste visual de textos) ---
@st.dialog("Campos em Branco")
def confirmar_salvamento_incompleto(novo_registro):
    st.warning("Alguns campos do formulário não foram preenchidos.")
    st.write("Deseja salvar o registro assim mesmo?")
    
    col_sim, col_nao = st.columns(2)
    
    if col_sim.button("Sim, Salvar", use_container_width=True, type="primary"):
        st.session_state['db_formularios'].append(novo_registro)
        utils.salvar_dados_locais(st.session_state['db_formularios'])
        st.session_state['form_id'] += 1
        st.session_state['sucesso_salvamento'] = True 
        
        keys_to_clear = [k for k in st.session_state.keys() if k.startswith("resp_") or k.startswith("nome_foto_")]
        for k in keys_to_clear: del st.session_state[k]
        st.rerun()
    
    if col_nao.button("Não, Cancelar", use_container_width=True):
        st.rerun()

@st.dialog("Confirmar Exclusão")
def confirmar_exclusao_dialog(indices_alvo=None, tipo="item"):
    """
    indices_alvo: Lista de índices (inteiros) para remover do db_formularios.
    tipo: 'item' (remove indices especificos) ou 'tudo' (limpa o banco).
    """
    st.markdown("### Ação Irreversível")
    st.warning("Você está prestes a remover registros permanentemente.")
    
    if indices_alvo and len(indices_alvo) > 1:
        st.info(f"Quantidade de itens selecionados para exclusão: {len(indices_alvo)}")
    
    senha = st.text_input("Digite sua senha para confirmar", type="password")
    
    col_confirm, col_cancel = st.columns(2)
    if col_confirm.button("Confirmar Exclusão", type="primary", use_container_width=True):
        u_db = auth.carregar_usuarios()
        hash_armazenado = u_db.get(st.session_state['usuario_ativo'])
        
        valido, _ = auth.verificar_senha(senha, hash_armazenado)
        
        if valido:
            if tipo == "tudo":
                st.session_state['db_formularios'] = []
            elif indices_alvo:
                # Remove itens de trás para frente
                for i in sorted(indices_alvo, reverse=True):
                    if 0 <= i < len(st.session_state['db_formularios']):
                        st.session_state['db_formularios'].pop(i)
            
            utils.salvar_dados_locais(st.session_state['db_formularios'])
            st.rerun()
        else: st.error("Senha incorreta.")
    
    if col_cancel.button("Cancelar", use_container_width=True):
        st.rerun()

@st.dialog("Excluir Usuário")
def excluir_usuario_dialog(nome_usuario):
    st.error(f"Remover acesso do técnico: {nome_usuario}?")
    senha_admin = st.text_input("Senha de Administrador", type="password")
    if st.button("Confirmar Exclusão", type="primary", use_container_width=True):
        admin_hash = auth.carregar_usuarios().get("Admin")
        valido, _ = auth.verificar_senha(senha_admin, admin_hash)
        if valido:
            if auth.excluir_usuario(nome_usuario):
                st.success("Usuário removido.")
                st.rerun()
            else: st.error("Erro ao remover usuário.")
        else: st.error("Senha incorreta.")

@st.dialog("Exclusão Permanente de Arquivo")
def excluir_arquivo_permanente_dialog(caminho_arquivo):
    st.warning(f"Excluir arquivo físico: {caminho_arquivo}")
    st.caption("Esta ação não pode ser desfeita.")
    senha = st.text_input("Senha de Administrador", type="password")
    if st.button("Confirmar Exclusão", type="primary", use_container_width=True):
        admin_db = auth.carregar_usuarios()
        admin_hash = admin_db.get("Admin")
        valido, _ = auth.verificar_senha(senha, admin_hash)
        if valido:
            try:
                if os.path.exists(caminho_arquivo):
                    os.remove(caminho_arquivo)
                    st.success("Arquivo excluído.")
                    import time; time.sleep(1)
                    st.rerun()
                else: st.error("Arquivo não encontrado.")
            except Exception as e: st.error(f"Erro: {e}")
        else: st.error("Senha incorreta.")

@st.dialog("Alterar Senha")
def alterar_senha_dialog():
    usuario = st.session_state['usuario_ativo']
    st.markdown(f"Alterar credenciais para: **{usuario}**")
    senha_atual = st.text_input("Senha Atual", type="password")
    nova_senha = st.text_input("Nova Senha", type="password")
    confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
    if st.button("Atualizar", type="primary", use_container_width=True):
        if not senha_atual or not nova_senha: st.error("Preencha todos os campos.")
        elif nova_senha != confirmar_senha: st.error("Senhas não coincidem.")
        else:
            sucesso = auth.alterar_senha(usuario, senha_atual, nova_senha)
            if sucesso: st.success("Senha atualizada!")
            else: st.error("Senha atual incorreta.")

# --- PÁGINAS DO SISTEMA ---

def render_configurar_modelo():
    main_header("tune", "Gerenciamento de Modelo")
    
    # Seção: Status Atual
    with st.container(border=True):
        section_title("info", "Status da Configuração")
        col_stat1, col_stat2 = st.columns([3, 1])
        with col_stat1:
            st.markdown(f"Origem do Modelo: **{st.session_state.get('origem_modelo', 'Padrão')}**")
            st.caption("Define a estrutura de campos e abas do formulário.")
        
        with col_stat2:
            if st.session_state.get('origem_modelo') == "Pessoal":
                if st.button("Restaurar Padrão", use_container_width=True):
                    path = utils.get_user_template_path()
                    if os.path.exists(path): os.remove(path)
                    utils.carregar_modelo_atual()
                    st.rerun()

    # Seção: Upload
    with st.container(border=True):
        section_title("upload_file", "Carregar Novo Modelo")
        st.markdown("Suba um arquivo Excel (.xlsx) para personalizar os campos de coleta.")
        
        arq = st.file_uploader("Selecionar arquivo", type=["xlsx"], label_visibility="collapsed")
        
        if arq:
            path = utils.get_user_template_path()
            with open(path, "wb") as f: f.write(arq.getbuffer())
            st.success("Modelo personalizado aplicado com sucesso!")
            utils.carregar_modelo_atual()
            st.rerun()

def render_preenchimento():
    # CSS para limpar inputs desabilitados (UI fix)
    st.markdown("""
        <style>
        div[data-baseweb="select"] input {
            readonly: readonly;
            pointer-events: none;
        }
        </style>
        """, unsafe_allow_html=True)
    
    main_header("edit_document", "Registro de Equipamento")
    
    # Init Session States
    if 'fotos_temp' not in st.session_state: st.session_state['fotos_temp'] = []
    if 'loc_uc' not in st.session_state: st.session_state['loc_uc'] = ""
    if 'loc_pav' not in st.session_state: st.session_state['loc_pav'] = ""
    if 'loc_amb' not in st.session_state: st.session_state['loc_amb'] = ""
    if 'loc_pred' not in st.session_state: st.session_state['loc_pred'] = ""
    
    # Feedback de sucesso
    if 'sucesso_salvamento' in st.session_state and st.session_state['sucesso_salvamento']:
        st.success("Registro salvo com sucesso.")
        st.session_state['sucesso_salvamento'] = False 

    if 'step_atual' not in st.session_state: st.session_state['step_atual'] = 0
    
    if 'estrutura_modelo' in st.session_state and st.session_state['estrutura_modelo']:
        
        # --- BLOC 1: LOCALIZAÇÃO (PERSISTENTE) ---
        with st.container(border=True):
            section_title("location_on", "Dados de Localização")
            st.caption("Estes dados serão mantidos para os próximos registros conforme sua ação de salvamento.")
            
            col_l1, col_l2 = st.columns(2)
            st.session_state['loc_uc'] = col_l1.text_input("Unidade Consumidora *", value=st.session_state['loc_uc'])
            st.session_state['loc_pav'] = col_l2.text_input("Pavimento *", value=st.session_state['loc_pav'])
            
            col_l3, col_l4 = st.columns(2)
            st.session_state['loc_amb'] = col_l3.text_input("Ambiente *", value=st.session_state['loc_amb'])
            st.session_state['loc_pred'] = col_l4.text_input("Prédio/Bloco (Opcional)", value=st.session_state['loc_pred'])

        # --- BLOC 2: SELEÇÃO DO TIPO ---
        st.markdown("<br>", unsafe_allow_html=True)
        tipo_opcoes = list(st.session_state['estrutura_modelo'].keys())
        tipo = st.selectbox("Selecione o Tipo de Equipamento", options=tipo_opcoes)

        # Preparação dos campos dinâmicos
        todos_campos = st.session_state['estrutura_modelo'][tipo]
        campos_reservados = [
            "Nome da Unidade Consumidora", "Pavimento", "Ambiente", 
            "Código do Prédio/Bloco", "Código de Instalação", "Local de instalação"
        ]
        campos_tecnicos = [c for c in todos_campos if c['nome'] not in campos_reservados]
        respostas = {}

        # --- BLOC 3: FORMULÁRIO TÉCNICO ---
        with st.form(key=f"form_{st.session_state['form_id']}", border=True):
            section_title("description", "Especificações Técnicas")
            
            if not campos_tecnicos:
                st.info("Não há campos técnicos adicionais configurados para este tipo.")
            
            # Grid dinâmico de campos
            cols = st.columns(2)
            for i, c in enumerate(campos_tecnicos):
                target = cols[i % 2]
                key_name = f"resp_{c['nome']}"
                default_val = st.session_state.get(key_name, "")
                
                if c['tipo'] == 'selecao':
                    idx_sel = 0
                    if default_val in c['opcoes']: idx_sel = c['opcoes'].index(default_val)
                    respostas[c['nome']] = target.selectbox(c['nome'], options=c['opcoes'], index=idx_sel)
                else:
                    respostas[c['nome']] = target.text_input(c['nome'], value=default_val)
            
            st.markdown("---")
            
            # --- ÁREA DE AÇÕES (DENTRO DO FORM) ---
            st.caption("Selecione a ação desejada para salvar este registro:")
            
            c_act_1, c_act_2, c_act_3 = st.columns(3)
            
            # Botões com ícones via help ou texto, mantendo layout limpo
            btn_novo_equip = c_act_1.form_submit_button("Salvar e Adicionar Item", help="Mantém Localização", use_container_width=True)
            btn_novo_amb = c_act_2.form_submit_button("Salvar e Mudar Ambiente", help="Mantém UC, limpa Ambiente", use_container_width=True)
            btn_salvar_full = c_act_3.form_submit_button("Salvar e Finalizar", help="Limpa todo o formulário", use_container_width=True, type="primary")

        # --- BLOC 4: FOTOS (FORA DO FORM) ---
        with st.container(border=True):
            section_title("camera_alt", "Registro Fotográfico")
            st.caption("Anexe evidências visuais antes de salvar o formulário acima.")

            tab_upl, tab_cam = st.tabs(["Carregar Arquivo", "Capturar Agora"])
            
            img_buffer = None
            origem = ""
            
            with tab_upl:
                col_u1, col_u2 = st.columns([3, 1])
                foto_upl = col_u1.file_uploader("Selecionar imagem", type=['png', 'jpg', 'jpeg'], key="uploader_galeria", label_visibility="collapsed")
                if foto_upl:
                    img_buffer = foto_upl
                    origem = "upload"

            with tab_cam:
                # Controle de Câmera
                if 'camera_facing' not in st.session_state:
                    st.session_state['camera_facing'] = 'environment'

                c_cam_ctrl, c_cam_view = st.columns([0.3, 0.7])
                
                with c_cam_ctrl:
                    icon_cam = "photo_camera_back" if st.session_state['camera_facing'] == 'environment' else "person"
                    label_cam = "Traseira" if st.session_state['camera_facing'] == 'environment' else "Frontal"
                    
                    st.markdown(f"**Câmera Ativa:** {label_cam}")
                    if st.button("Alternar Câmera", icon=":material/sync:", use_container_width=True):
                        st.session_state['camera_facing'] = 'user' if st.session_state['camera_facing'] == 'environment' else 'environment'
                        st.rerun()

                with c_cam_view:
                    key_camera = f"camera_input_{st.session_state['camera_facing']}"
                    foto_cam = st.camera_input("Visor", key=key_camera, label_visibility="collapsed")
                
                if foto_cam:
                    img_buffer = foto_cam
                    origem = "camera"

            # Input e Botão de Adicionar
            st.markdown("<br>", unsafe_allow_html=True)
            col_nome, col_add = st.columns([3, 1])
            nome_foto_atual = col_nome.text_input("Descrição da Imagem", placeholder="Ex: Etiqueta do motor", key="input_nome_foto")
            
            # Alinhamento vertical do botão
            col_add.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
            if col_add.button("Anexar Imagem", icon=":material/add_a_photo:", use_container_width=True):
                if img_buffer:
                    st.session_state['fotos_temp'].append({
                        "arquivo": img_buffer,
                        "nome": nome_foto_atual if nome_foto_atual else f"Foto {len(st.session_state['fotos_temp'])+1}",
                        "origem": origem
                    })
                    st.success("Imagem anexada.")
                    st.rerun()
                else:
                    st.warning("Nenhuma imagem selecionada.")

            # Galeria de Miniaturas
            if st.session_state['fotos_temp']:
                st.markdown("---")
                st.markdown("**Imagens em espera:**")
                for idx, item in enumerate(st.session_state['fotos_temp']):
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([0.1, 0.7, 0.2])
                        c1.image(item['arquivo'], width=60)
                        c2.markdown(f"**{item['nome']}**")
                        if c3.button("Remover", key=f"rm_foto_{idx}", icon=":material/delete:", use_container_width=True):
                            st.session_state['fotos_temp'].pop(idx)
                            st.rerun()

        # --- PROCESSAMENTO DOS BOTÕES ---
        action_type = None
        if btn_novo_equip: action_type = "novo_equip"
        elif btn_novo_amb: action_type = "novo_amb"
        elif btn_salvar_full: action_type = "full"

        if action_type:
            loc_data = {
                "Nome da Unidade Consumidora": st.session_state['loc_uc'],
                "Pavimento": st.session_state['loc_pav'],
                "Ambiente": st.session_state['loc_amb'],
                "Código do Prédio/Bloco": st.session_state['loc_pred']
            }
            
            # Validação
            if not loc_data["Nome da Unidade Consumidora"] or not loc_data["Pavimento"] or not loc_data["Ambiente"]:
                st.error("Campos obrigatórios de localização não preenchidos.")
            else:
                processar_salvamento(loc_data, tipo, respostas, st.session_state['fotos_temp'], action_type)

    else:
        st.warning("Modelo de dados não carregado. Vá em 'Configurações'.")

def processar_salvamento(loc_data, tipo, respostas, lista_fotos_temp, action_type):
    uc = loc_data["Nome da Unidade Consumidora"]
    dados_completos = loc_data.copy()
    dados_completos.update(respostas)

    meta_fotos = utils.salvar_fotos_local(lista_fotos_temp, uc)
    
    novo_registro = {
        "cod_instalacao": uc, 
        "tipo_equipamento": tipo, 
        "data_hora": utils.get_data_hora_br().strftime("%d/%m/%Y %H:%M:%S"), 
        "dados": dados_completos,
        "fotos": meta_fotos
    }
    
    st.session_state['db_formularios'].append(novo_registro)
    utils.salvar_dados_locais(st.session_state['db_formularios'])
    st.session_state['form_id'] += 1
    st.session_state['sucesso_salvamento'] = True 
    
    # Limpeza Técnica
    keys_tecnicas = [k for k in st.session_state.keys() if k.startswith("resp_")]
    for k in keys_tecnicas: del st.session_state[k]
    st.session_state['fotos_temp'] = [] 

    # Limpeza Contextual
    if action_type == "novo_amb":
        st.session_state['loc_pav'] = ""
        st.session_state['loc_amb'] = ""
        st.session_state['loc_pred'] = ""
    elif action_type == "full":
        st.session_state['loc_uc'] = ""
        st.session_state['loc_pav'] = ""
        st.session_state['loc_amb'] = ""
        st.session_state['loc_pred'] = ""

    st.rerun()

def render_exportar_listar():
    main_header("table_view", "Gerenciamento de Levantamentos")
    
    registros = st.session_state['db_formularios']
    
    if not registros:
        st.info("Nenhum registro encontrado no banco de dados local.")
        return

    # Painel de Controle Geral
    with st.container(border=True):
        c_tot, c_act = st.columns([0.7, 0.3])
        c_tot.metric("Total de Equipamentos Coletados", len(registros))
        if c_act.button("Excluir Tudo", type="primary", use_container_width=True, icon=":material/delete_forever:"):
            confirmar_exclusao_dialog(indices_alvo=None, tipo="tudo")

    st.markdown("### Levantamentos por Unidade")

    # Agrupamento
    grupos_uc = defaultdict(list)
    for idx, item in enumerate(registros):
        uc_nome = item.get('cod_instalacao') or item.get('dados', {}).get('Nome da Unidade Consumidora', 'UC Indefinida')
        grupos_uc[uc_nome].append((idx, item))

    # Listagem Hierárquica
    for uc, lista_itens in grupos_uc.items():
        qtd_equipamentos = len(lista_itens)
        qtd_fotos_total = sum(len(i[1].get('fotos', [])) for i in lista_itens)
        
        datas = [i[1].get('data_hora', '-') for i in lista_itens]
        data_resumo = datas[0].split()[0] if datas else "-"

        # Cabeçalho do Expander (Texto Limpo)
        expander_label = f"{uc}  |  {data_resumo}  |  {qtd_equipamentos} iten(s)"

        with st.expander(expander_label, expanded=False):
            # Header Interno
            c_h1, c_h2, c_h3, c_h4 = st.columns([3, 2, 2, 3])
            c_h1.caption("Unidade Consumidora")
            c_h1.markdown(f"**{uc}**")
            
            c_h2.caption("Data Base")
            c_h2.markdown(f"**{data_resumo}**")
            
            c_h3.caption("Fotos Totais")
            c_h3.markdown(f"**{qtd_fotos_total}**")
            
            c_h4.caption("Ações do Grupo")
            indices_grupo = [i[0] for i in lista_itens]
            if c_h4.button("Excluir Levantamento Completo", key=f"del_grp_{uc}", use_container_width=True, icon=":material/folder_delete:"):
                confirmar_exclusao_dialog(indices_alvo=indices_grupo, tipo="item")

            st.divider()
            
            # Tabela de Itens
            for real_idx, item in lista_itens:
                dados = item.get('dados', {})
                tipo = item.get('tipo_equipamento', 'Equipamento')
                data_hora = item.get('data_hora', '-')
                fotos = item.get('fotos', [])
                pav = dados.get('Pavimento', '-')
                amb = dados.get('Ambiente', '-')

                with st.container(border=True):
                    row1, row2, row3 = st.columns([0.4, 0.4, 0.2])
                    
                    with row1:
                        st.markdown(f"**{tipo}**")
                        st.caption(f"Local: {pav} > {amb}")
                    
                    with row2:
                        st.caption(f"Registro: {data_hora}")
                        if fotos:
                            st.markdown(f"📎 {len(fotos)} anexo(s)")
                    
                    with row3:
                        # Alinhamento vertical para botão
                        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
                        if st.button("Excluir", key=f"del_item_{real_idx}", icon=":material/delete:", use_container_width=True):
                            confirmar_exclusao_dialog(indices_alvo=[real_idx], tipo="item")
                    
                    # Expander de fotos discreto
                    if fotos:
                        with st.popover("Visualizar Anexos"):
                            cols_foto = st.columns(3)
                            for idx_f, f in enumerate(fotos):
                                with cols_foto[idx_f % 3]:
                                    st.image(f['caminho_fisico'], caption=f['nome_exportacao'], use_container_width=True)

    st.markdown("---")
    
    # Rodapé: Exportação
    main_header("download", "Exportação de Dados")
    
    zip_data = utils.gerar_zip_exportacao(st.session_state['db_formularios'])
    
    col_dl, col_email = st.columns(2)
    with col_dl:
        if zip_data:
            st.download_button(
                "Baixar Pacote Completo (.zip)", 
                data=zip_data, 
                file_name="levantamento_poup.zip", 
                mime="application/zip",
                use_container_width=True, 
                type="primary",
                icon=":material/archive:"
            )
        else:
            st.button("Baixar Pacote Completo", disabled=True, use_container_width=True)
            
    with col_email:
        with st.form("form_email_envio"):
            c_e1, c_e2 = st.columns([0.7, 0.3])
            email_dest = c_e1.text_input("Email", placeholder="usuario@empresa.com", label_visibility="collapsed")
            btn_env = c_e2.form_submit_button("Enviar", icon=":material/send:", use_container_width=True)
            
            if btn_env:
                if email_dest and zip_data and utils.enviar_email(zip_data, email_dest, is_zip=True):
                    st.success("Relatório enviado!")
                else:
                    st.error("Erro ao enviar ou email inválido.")

def render_admin_panel():
    main_header("admin_panel_settings", "Painel Administrativo")
    
    tab_users, tab_audit, tab_master = st.tabs(["Equipe Técnica", "Auditoria de Dados", "Modelo de Dados"])
    
    with tab_users:
        with st.container(border=True):
            section_title("person_add", "Cadastrar Novo Técnico")
            with st.form("novo_user_form", clear_on_submit=True):
                c1, c2, c3 = st.columns([0.4, 0.4, 0.2])
                new_u = c1.text_input("Usuário")
                new_p = c2.text_input("Senha", type="password")
                c3.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
                if c3.form_submit_button("Adicionar", use_container_width=True, type="primary"):
                    if new_u and new_p:
                        d = auth.carregar_usuarios()
                        d[new_u] = auth.hash_senha(new_p) 
                        auth.salvar_usuarios(d)
                        st.success("Cadastrado com sucesso!")
                    else:
                        st.error("Dados incompletos.")

        st.markdown("<br>", unsafe_allow_html=True)
        section_title("group", "Técnicos Ativos")
        
        users = auth.carregar_usuarios()
        if users:
            for nome, senha in users.items():
                with st.container(border=True):
                    c_n, c_a = st.columns([0.8, 0.2])
                    c_n.markdown(f"**{nome}**")
                    if nome != "Admin": 
                        if c_a.button("Remover", key=f"del_user_{nome}", use_container_width=True):
                            excluir_usuario_dialog(nome)
                    else:
                        c_a.markdown("*Sistema*")

    with tab_audit:
        section_title("history", "Histórico de Arquivos Locais")
        arquivos = sorted([f for f in os.listdir(".") if f.startswith("dados_") and f.endswith(".json")])
        
        if arquivos:
            sel = st.selectbox("Selecione o arquivo de backup:", arquivos)
            dados_rec = utils.carregar_dados_locais(path_especifico=sel)
            
            # Métricas
            cm1, cm2 = st.columns(2)
            cm1.metric("Registros", len(dados_rec))
            cm2.metric("Tamanho", f"{(os.path.getsize(sel)/1024):.2f} KB")
            
            # Preview
            st.caption("Visualização Rápida dos Dados")
            df = pd.DataFrame([{"UC": d.get('cod_instalacao'), "Tipo": d.get('tipo_equipamento'), "Data": d.get('data_hora')} for d in dados_rec])
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Ações
            c_act1, c_act2 = st.columns(2)
            rec_excel = utils.exportar_para_excel(dados_rec)
            if rec_excel:
                 c_act1.download_button("Baixar Planilha (Excel)", data=rec_excel, file_name=f"backup_{sel}.xlsx", use_container_width=True, icon=":material/download:")

            if c_act2.button("Apagar Arquivo do Servidor", use_container_width=True, icon=":material/delete_forever:"):
                excluir_arquivo_permanente_dialog(sel)
        else:
            st.info("Nenhum arquivo de backup encontrado.")
    
    with tab_master:
        with st.container(border=True):
            section_title("settings_system_daydream", "Modelo Padrão do Sistema")
            st.warning("A substituição deste arquivo afeta todos os novos levantamentos iniciados sem modelo pessoal.")
            
            mestre = st.file_uploader("Substituir 'Levantamento_Base.xlsx'", type=["xlsx"])
            if mestre:
                with open(utils.PLANILHA_PADRAO_ADMIN, "wb") as f: f.write(mestre.getbuffer())
                st.success("Modelo Padrão atualizado com sucesso!")

