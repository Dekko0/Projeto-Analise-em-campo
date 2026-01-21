import streamlit as st
import os
import pandas as pd
import utils
import auth
from collections import defaultdict


# AUXILIARES VISUAIS
def icon_header(icon_name, text):
    st.markdown(f"## <span class='material-symbols-outlined icon-text'>{icon_name}</span> {text}", unsafe_allow_html=True)

def icon_subheader(icon_name, text):
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
    st.warning("Esta ação não pode ser desfeita.")
    if indices_alvo and len(indices_alvo) > 1:
        st.write(f"Você está prestes a excluir **{len(indices_alvo)} itens** deste levantamento.")
    
    senha = st.text_input("Confirme sua senha para prosseguir", type="password")
    
    if st.button("Confirmar Exclusão", type="primary", use_container_width=True):
        u_db = auth.carregar_usuarios()
        hash_armazenado = u_db.get(st.session_state['usuario_ativo'])
        
        valido, _ = auth.verificar_senha(senha, hash_armazenado)
        
        if valido:
            if tipo == "tudo":
                st.session_state['db_formularios'] = []
            elif indices_alvo:
                # Remove itens de trás para frente para não afetar os índices dos anteriores
                for i in sorted(indices_alvo, reverse=True):
                    if 0 <= i < len(st.session_state['db_formularios']):
                        st.session_state['db_formularios'].pop(i)
            
            utils.salvar_dados_locais(st.session_state['db_formularios'])
            st.rerun()
        else: st.error("Senha incorreta.")

@st.dialog("Excluir Usuário")
def excluir_usuario_dialog(nome_usuario):
    # ... (Manter código original) ...
    st.error(f"Tem certeza que deseja remover o técnico: **{nome_usuario}**?")
    senha_admin = st.text_input("Senha Master (Admin)", type="password")
    if st.button("Confirmar Exclusão", type="primary", use_container_width=True):
        admin_hash = auth.carregar_usuarios().get("Admin")
        valido, _ = auth.verificar_senha(senha_admin, admin_hash)
        if valido:
            if auth.excluir_usuario(nome_usuario):
                st.success(f"Usuário {nome_usuario} removido!")
                st.rerun()
            else: st.error("Erro ao remover usuário.")
        else: st.error("Senha de Admin incorreta.")

@st.dialog("Exclusão Permanente de Arquivo")
def excluir_arquivo_permanente_dialog(caminho_arquivo):
    # ... (Manter código original) ...
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
                    import time; time.sleep(1)
                    st.rerun()
                else: st.error("Erro: O arquivo não foi encontrado.")
            except Exception as e: st.error(f"Erro inesperado: {e}")
        else: st.error("Senha de Admin incorreta.")

@st.dialog("Alterar Senha")
def alterar_senha_dialog():
    # ... (Manter código original) ...
    usuario = st.session_state['usuario_ativo']
    st.markdown(f"Alterando senha para: **{usuario}**")
    senha_atual = st.text_input("Senha Atual", type="password")
    nova_senha = st.text_input("Nova Senha", type="password")
    confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
    if st.button("Atualizar Senha", type="primary", use_container_width=True):
        if not senha_atual or not nova_senha: st.error("Preencha todos os campos.")
        elif nova_senha != confirmar_senha: st.error("A nova senha e a confirmação não coincidem.")
        else:
            sucesso = auth.alterar_senha(usuario, senha_atual, nova_senha)
            if sucesso: st.success("Senha alterada com sucesso!")
            else: st.error("A senha atual está incorreta.")

# PAGINAS
def render_configurar_modelo():
    # ... (Manter código original) ...
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
    st.markdown("""
        <style>
        /* Tenta impedir o foco de digitação em campos de seleção */
        div[data-baseweb="select"] input {
            readonly: readonly;
            pointer-events: none;
        }
        </style>
        """, unsafe_allow_html=True)
    icon_header("edit_document", "Registro de Equipamento")
    
    # Inicializar lista temporária de fotos se não existir
    if 'fotos_temp' not in st.session_state: st.session_state['fotos_temp'] = []
    
    # Inicializar campos de localização se não existirem
    if 'loc_uc' not in st.session_state: st.session_state['loc_uc'] = ""
    if 'loc_pav' not in st.session_state: st.session_state['loc_pav'] = ""
    if 'loc_amb' not in st.session_state: st.session_state['loc_amb'] = ""
    if 'loc_pred' not in st.session_state: st.session_state['loc_pred'] = ""
    
    if 'sucesso_salvamento' in st.session_state and st.session_state['sucesso_salvamento']:
        st.success("Levantamento Salvo com Sucesso!")
        st.session_state['sucesso_salvamento'] = False 

    if 'step_atual' not in st.session_state: st.session_state['step_atual'] = 0
    
    if 'estrutura_modelo' in st.session_state and st.session_state['estrutura_modelo']:
        
        # --- SELEÇÃO DO TIPO DE EQUIPAMENTO ---
        tipo_opcoes = list(st.session_state['estrutura_modelo'].keys())
        tipo = st.selectbox("Selecione o Equipamento", options=tipo_opcoes)
        
        # --- DADOS DE LOCALIZAÇÃO (FIXOS E PERSISTENTES) ---
        st.divider()
        icon_subheader("location_on", "Dados de Localização")
        with st.container(border=True):
            col_l1, col_l2 = st.columns(2)
            # Unidade Consumidora e Pavimento
            st.session_state['loc_uc'] = col_l1.text_input("Nome da Unidade Consumidora *", value=st.session_state['loc_uc'])
            st.session_state['loc_pav'] = col_l2.text_input("Pavimento *", value=st.session_state['loc_pav'])
            
            col_l3, col_l4 = st.columns(2)
            # Ambiente e Código Prédio
            st.session_state['loc_amb'] = col_l3.text_input("Ambiente *", value=st.session_state['loc_amb'])
            st.session_state['loc_pred'] = col_l4.text_input("Código do Prédio/Bloco (Opcional)", value=st.session_state['loc_pred'])

        # Obter todos os campos do modelo para este tipo
        todos_campos = st.session_state['estrutura_modelo'][tipo]
        
        # FILTRAR: Remover campos de localização da lista de campos técnicos para não duplicar
        campos_reservados = [
            "Nome da Unidade Consumidora", 
            "Pavimento", 
            "Ambiente", 
            "Código do Prédio/Bloco",
            "Código de Instalação", 
            "Local de instalação"
        ]
        
        # Mantém apenas os campos que NÃO estão na lista de reservados
        campos_tecnicos = [c for c in todos_campos if c['nome'] not in campos_reservados]
        
        respostas = {}

        # --- FORMULÁRIO TÉCNICO ---
        with st.form(key=f"form_{st.session_state['form_id']}", border=True):
            icon_subheader("description", "Detalhamento Técnico")
            cols = st.columns(2)
            
            if not campos_tecnicos:
                st.info("Nenhum campo técnico adicional encontrado para este equipamento além da localização.")
            
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
            
            # --- ÁREA DE FOTOS ---
            submit_placeholder = st.empty() 
            
            # BOTÕES DE AÇÃO
            st.markdown("<br>", unsafe_allow_html=True)
            c_btn1, c_btn2, c_btn3 = st.columns(3)
            
            btn_novo_equip = c_btn1.form_submit_button("➕ Novo Equipamento", use_container_width=True)
            btn_novo_amb = c_btn2.form_submit_button("Novo Ambiente", use_container_width=True)
            btn_salvar_full = c_btn3.form_submit_button("Salvar Levantamento Completo", use_container_width=True, type="primary")

        # --- ÁREA DE FOTOS (FORA DO st.form) ---
        st.divider()
        icon_subheader("camera_alt", "Registro Fotográfico")
        
        with st.container(border=True):
            st.info("Adicione as fotos uma a uma, nomeando-as antes de salvar o formulário acima.")
            
            tab_upl, tab_cam = st.tabs(["Upload Arquivo", "Usar Câmera"])
            
            img_buffer = None
            origem = ""
            
            with tab_upl:
                foto_upl = st.file_uploader("Escolher da galeria", type=['png', 'jpg', 'jpeg'], key="uploader_galeria")
                if foto_upl:
                    img_buffer = foto_upl
                    origem = "upload"

            with tab_cam:
                foto_cam = st.camera_input("Tirar foto agora", key="camera_input_direto")
                if foto_cam:
                    img_buffer = foto_cam
                    origem = "camera"

            col_nome, col_add = st.columns([3, 1])
            nome_foto_atual = col_nome.text_input("Nome desta foto:", placeholder="Ex: Placa de identificação", key="input_nome_foto")
            
            if col_add.button("➕ Adicionar Foto", use_container_width=True):
                if img_buffer:
                    st.session_state['fotos_temp'].append({
                        "arquivo": img_buffer,
                        "nome": nome_foto_atual if nome_foto_atual else f"Foto {len(st.session_state['fotos_temp'])+1}",
                        "origem": origem
                    })
                    st.success("Foto adicionada à lista!")
                    st.rerun()
                else:
                    st.warning("Selecione um arquivo ou tire uma foto primeiro.")

        # --- LISTAGEM DAS FOTOS JÁ ADICIONADAS ---
        if st.session_state['fotos_temp']:
            st.markdown("#### Fotos Anexadas:")
            for idx, item in enumerate(st.session_state['fotos_temp']):
                c1, c2, c3 = st.columns([0.2, 0.6, 0.2])
                c1.image(item['arquivo'], width=50) 
                c2.write(f"**{item['nome']}**")
                if c3.button("Remover", key=f"rm_foto_{idx}"):
                    st.session_state['fotos_temp'].pop(idx)
                    st.rerun()

        # --- LÓGICA DE PROCESSAMENTO DOS BOTÕES ---
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
            
            if not loc_data["Nome da Unidade Consumidora"] or not loc_data["Pavimento"] or not loc_data["Ambiente"]:
                st.error("Os campos: Unidade Consumidora, Pavimento e Ambiente são obrigatórios!")
            else:
                processar_salvamento(loc_data, tipo, respostas, st.session_state['fotos_temp'], action_type)

    else:
        st.warning("Carregue um modelo em 'Configurar Modelo' antes de iniciar.")

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
    
    # --- LÓGICA DE LIMPEZA ---
    keys_tecnicas = [k for k in st.session_state.keys() if k.startswith("resp_")]
    for k in keys_tecnicas: del st.session_state[k]
    st.session_state['fotos_temp'] = [] 

    if action_type == "novo_equip":
        pass
    elif action_type == "novo_amb":
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
    icon_header("table_view", "Seus Levantamentos")
    
    registros = st.session_state['db_formularios']
    
    if not registros:
        st.info("Nenhum registro encontrado.")
        return

    # Ação Global: Apagar Tudo
    col_total, col_del_all = st.columns([0.8, 0.2])
    col_total.metric("Total de Equipamentos", len(registros))
    if col_del_all.button("Limpar Tudo", type="primary"):
        confirmar_exclusao_dialog(indices_alvo=None, tipo="tudo")

    st.divider()

    # Agrupar por Unidade Consumidora (Simulando "Levantamento")
    grupos_uc = defaultdict(list)
    for idx, item in enumerate(registros):
        # Usa 'cod_instalacao' ou fallback para 'Nome da Unidade Consumidora' dentro de dados
        uc_nome = item.get('cod_instalacao') or item.get('dados', {}).get('Nome da Unidade Consumidora', 'UC Indefinida')
        grupos_uc[uc_nome].append((idx, item))

    # Renderizar os Grupos como Expandable Sidebar Items
    for uc, lista_itens in grupos_uc.items():
        # Calcular Resumo do Levantamento
        qtd_equipamentos = len(lista_itens)
        qtd_fotos_total = sum(len(i[1].get('fotos', [])) for i in lista_itens)
        
        # Pega a data mais recente ou a primeira disponível
        datas = [i[1].get('data_hora', '-') for i in lista_itens]
        data_resumo = datas[0].split()[0] if datas else "-"

        # Label do Expander (Resumido)
        expander_label = f"📍 {uc} | {data_resumo} | {qtd_equipamentos} Equip."

        with st.expander(expander_label, expanded=False):
            # Header detalhado dentro do expander
            c_head1, c_head2, c_head3, c_head4 = st.columns([0.3, 0.2, 0.3, 0.2])
            
            c_head1.markdown(f"**<span class='material-symbols-outlined icon-text'>calendar_today</span> Data:** {data_resumo}", unsafe_allow_html=True)
            c_head2.markdown(f"**<span class='material-symbols-outlined icon-text'>photo_library</span> Fotos:** {qtd_fotos_total}", unsafe_allow_html=True)
            c_head3.markdown(f"**<span class='material-symbols-outlined icon-text'>inventory_2</span> Equipamentos:** {qtd_equipamentos}", unsafe_allow_html=True)
            
            # Botão para excluir LEVANTAMENTO COMPLETO (todos os itens desta UC)
            indices_grupo = [i[0] for i in lista_itens]
            if c_head4.button("Excluir Levantamento", key=f"del_group_{uc}", use_container_width=True):
                confirmar_exclusao_dialog(indices_alvo=indices_grupo, tipo="item")

            st.divider()
            
            # Listar Equipamentos (Itens Individuais)
            for real_idx, item in lista_itens:
                dados = item.get('dados', {})
                tipo = item.get('tipo_equipamento', 'Equipamento')
                data_hora = item.get('data_hora', '-')
                fotos = item.get('fotos', [])
                
                # Contexto de Localização Específico do Item
                pav = dados.get('Pavimento', '-')
                amb = dados.get('Ambiente', '-')

                with st.container(border=True):
                    row1, row2, row3 = st.columns([0.5, 0.4, 0.1])
                    
                    # Coluna 1: Identificação
                    with row1:
                        st.markdown(f"**<span class='material-symbols-outlined icon-text'>bolt</span> {tipo}**", unsafe_allow_html=True)
                        st.caption(f"Local: {pav} > {amb}")
                    
                    # Coluna 2: Dados de Registro
                    with row2:
                        st.markdown(f"<span class='material-symbols-outlined icon-text'>schedule</span> {data_hora}", unsafe_allow_html=True)
                        if fotos:
                            st.markdown(f"<span class='material-symbols-outlined icon-text'>image</span> {len(fotos)} foto(s)", unsafe_allow_html=True)
                    
                    # Coluna 3: Excluir Individual
                    with row3:
                        if st.button("🗑️", key=f"del_item_{real_idx}", help="Excluir este equipamento"):
                            confirmar_exclusao_dialog(indices_alvo=[real_idx], tipo="item")
                    
                    # Mostrar miniaturas das fotos se houver (expansível opcional ou direto)
                    if fotos:
                        with st.popover("Ver Fotos Anexadas"):
                            cols_foto = st.columns(3)
                            for idx_f, f in enumerate(fotos):
                                with cols_foto[idx_f % 3]:
                                    st.image(f['caminho_fisico'], caption=f['nome_exportacao'], use_container_width=True)

    st.divider()
    
    # GERAR ZIP AO INVÉS DE APENAS EXCEL
    zip_data = utils.gerar_zip_exportacao(st.session_state['db_formularios'])
    
    ex1, ex2 = st.columns(2)
    with ex1:
        if zip_data:
            st.download_button(
                "Baixar Tudo (ZIP)", 
                data=zip_data, 
                file_name="levantamento_poup.zip", 
                mime="application/zip",
                use_container_width=True, 
                type="primary"
            )
    with ex2:
        target_mail = st.text_input("Enviar para:", placeholder="exemplo@email.com")
        if st.button("Enviar por E-mail", use_container_width=True):
            if target_mail and zip_data and utils.enviar_email(zip_data, target_mail, is_zip=True):
                st.success("Relatório enviado!")

# ... (Restante do arquivo permanece igual) ...

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
