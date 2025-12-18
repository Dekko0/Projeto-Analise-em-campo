import streamlit as st
import pd
import io
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from openpyxl import load_workbook
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Levantamento de Cargas", layout="wide", page_icon="⚡")

PLANILHA_PADRAO = "Levantamento_Base.xlsx"

# --- CONFIGURAÇÃO DE USUÁRIOS E SENHAS ---
# Altere as senhas abaixo conforme necessário
USUARIOS_SENHAS = {
    "Lívia Aguiar": "livia123",
    "Rafael Argolo": "rafael123",
    "Adelmo Santana": "adelmo123",
    "Admin": "cargas2024"
}
LISTA_TECNICOS = ["Selecione..."] + list(USUARIOS_SENHAS.keys())

# --- FUNÇÕES DE PERSISTÊNCIA INDIVIDUALIZADA ---

def get_user_db_path():
    if 'usuario_ativo' in st.session_state and st.session_state['usuario_ativo']:
        nome_limpo = "".join(filter(str.isalnum, st.session_state['usuario_ativo']))
        return f"dados_{nome_limpo}.json"
    return None

def salvar_dados_locais(dados):
    path = get_user_db_path()
    if path:
        with open(path, "w") as f:
            json.dump(dados, f)

def carregar_dados_locais():
    path = get_user_db_path()
    if path and os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def limpar_dados_locais():
    path = get_user_db_path()
    if path and os.path.exists(path):
        os.remove(path)
    st.session_state['db_formularios'] = []

# --- MODAL DE CONFIRMAÇÃO DE EXCLUSÃO ---

@st.dialog("Confirmar Exclusão")
def confirmar_exclusao_dialog(index):
    item = st.session_state['db_formularios'][index]
    st.write(f"Tem certeza que deseja excluir o levantamento da UC: **{item['cod_instalacao']}**?")
    
    if st.button("Sim, excluir permanentemente", type="primary", use_container_width=True):
        st.session_state['db_formularios'].pop(index)
        salvar_dados_locais(st.session_state['db_formularios'])
        st.success("Item removido!")
        st.rerun()

# --- FUNÇÕES DE EMAIL E EXCEL ---

def enviar_email(arquivo_buffer, destinatario):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_REMETENTE = "levantamento.poupenergia@gmail.com"
    SENHA_REMETENTE = "kiqplowxqprcugjc" 
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = destinatario
        msg['Subject'] = f"Levantamento {st.session_state['usuario_ativo']} - {datetime.now().strftime('%d/%m/%Y')}"
        msg.attach(MIMEText("Segue em anexo a planilha de levantamento.", 'plain'))
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(arquivo_buffer.getvalue())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename=levantamento.xlsx')
        msg.attach(part)
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_REMETENTE)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erro no e-mail: {e}")
        return False

def analisar_modelo_excel(file_content):
    if isinstance(file_content, bytes): buffer = io.BytesIO(file_content)
    else: buffer = io.BytesIO(file_content.getvalue())
    wb = load_workbook(buffer, data_only=True)
    estrutura = {}
    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        headers = []
        for cell in sheet[1]:
            if cell.value:
                headers.append({"nome": str(cell.value), "col_letter": cell.column_letter, "tipo": "texto", "opcoes": []})
        for dv in sheet.data_validations.dataValidation:
            if dv.type == "list":
                for ref in str(dv.sqref).split():
                    col_letter = "".join(filter(str.isalpha, ref.split(':')[0]))
                    for h in headers:
                        if h["col_letter"] == col_letter:
                            h["tipo"] = "selecao"
                            formula = dv.formula1
                            if formula and formula.startswith('"'): h["opcoes"] = formula.strip('"').split(',')
        estrutura[sheet_name] = [{"nome": h["nome"], "tipo": h["tipo"], "opcoes": h["opcoes"]} for h in headers]
    return estrutura

# --- LOGIN / IDENTIFICAÇÃO COM SENHA ---

if 'usuario_ativo' not in st.session_state:
    st.session_state['usuario_ativo'] = None

if not st.session_state['usuario_ativo']:
    st.markdown("<h1 style='text-align: center;'>⚡ Sistema de Cargas</h1>", unsafe_allow_html=True)
    
    with st.container():
        col_l, col_c, col_r = st.columns([1, 2, 1])
        with col_c:
            st.subheader("🔐 Acesso Restrito")
            user_input = st.selectbox("Selecione o Técnico", options=LISTA_TECNICOS)
            password_input = st.text_input("Senha", type="password")
            
            if st.button("Entrar", use_container_width=True):
                if user_input != "Selecione...":
                    senha_correta = USUARIOS_SENHAS.get(user_input)
                    if password_input == senha_correta:
                        st.session_state['usuario_ativo'] = user_input
                        st.session_state['db_formularios'] = carregar_dados_locais()
                        st.success("Login realizado!")
                        st.rerun()
                    else:
                        st.error("Senha incorreta. Tente novamente.")
                else:
                    st.warning("Selecione um usuário.")
    st.stop() # Bloqueia o resto do app até logar

# --- CARREGAMENTO DO MODELO AUTOMÁTICO ---

if 'planilha_modelo' not in st.session_state or st.session_state['planilha_modelo'] is None:
    if os.path.exists(PLANILHA_PADRAO):
        with open(PLANILHA_PADRAO, "rb") as f:
            content = f.read()
            st.session_state['planilha_modelo'] = io.BytesIO(content)
            st.session_state['estrutura_modelo'] = analisar_modelo_excel(content)

# --- INTERFACE PRINCIPAL ---

st.sidebar.title(f"👤 {st.session_state['usuario_ativo']}")
if st.sidebar.button("Sair / Trocar Usuário"):
    st.session_state['usuario_ativo'] = None
    st.rerun()

menu = st.sidebar.radio("Navegação", ["1. Configuração", "2. Preenchimento", "3. Exportar & Listar"])

# MÓDULO 2: PREENCHIMENTO
if menu == "2. Preenchimento":
    st.header("📝 Novo Levantamento")
    col1, col2 = st.columns(2)
    cod_instalacao = col1.text_input("Código de Instalação (UC)")
    
    opcoes_abas = list(st.session_state.get('estrutura_modelo', {}).keys())
    tipo_equipamento = st.selectbox("Tipo de Equipamento", options=opcoes_abas)

    if tipo_equipamento:
        campos = st.session_state['estrutura_modelo'][tipo_equipamento]
        respostas = {}
        with st.form("form_tecnico"):
            cols = st.columns(2)
            for i, campo in enumerate(campos):
                col_atual = cols[i % 2]
                if campo['tipo'] == 'selecao':
                    respostas[campo['nome']] = col_atual.selectbox(campo['nome'], options=campo['opcoes'])
                else:
                    respostas[campo['nome']] = col_atual.text_input(campo['nome'])
            
            if st.form_submit_button("➕ Salvar Equipamento"):
                if cod_instalacao:
                    novo = {
                        "cod_instalacao": cod_instalacao,
                        "tipo_equipamento": tipo_equipamento,
                        "responsavel": st.session_state['usuario_ativo'],
                        "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "dados": respostas
                    }
                    st.session_state['db_formularios'].append(novo)
                    salvar_dados_locais(st.session_state['db_formularios'])
                    st.success("Salvo com sucesso!")
                else:
                    st.error("Informe a UC.")

# MÓDULO 3: EXPORTAR E EXCLUIR
elif menu == "3. Exportar & Listar":
    st.header("📋 Itens Levantados por Você")
    
    if not st.session_state['db_formularios']:
        st.info("Sua lista está vazia.")
    else:
        for idx, item in enumerate(st.session_state['db_formularios']):
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 3, 1])
                c1.write(f"**UC:** {item['cod_instalacao']}")
                c2.write(f"**Equipamento:** {item['tipo_equipamento']}")
                if c3.button("🗑️", key=f"del_{idx}"):
                    confirmar_exclusao_dialog(idx)
        
        st.divider()
        st.subheader("Gerar Relatório")
        
        col_down, col_mail = st.columns(2)
        
        def exportar_para_excel():
            st.session_state['planilha_modelo'].seek(0)
            book = load_workbook(st.session_state['planilha_modelo'])
            for registro in st.session_state['db_formularios']:
                if registro['tipo_equipamento'] in book.sheetnames:
                    sheet = book[registro['tipo_equipamento']]
                    colunas_excel = [cell.value for cell in sheet[1]]
                    nova_linha = [registro['dados'].get(col, "") for col in colunas_excel]
                    sheet.append(nova_linha)
            out = io.BytesIO()
            book.save(out)
            return out

        excel_final = exportar_para_excel()
        col_down.download_button("⬇️ Baixar Sua Planilha", data=excel_final, file_name=f"levantamento_{st.session_state['usuario_ativo']}.xlsx")
        
        email_dest = col_mail.text_input("E-mail do Destinatário")
        if col_mail.button("📧 Enviar por E-mail"):
            if email_dest and enviar_email(excel_final, email_dest):
                st.success("Planilha enviada com sucesso!")

        if st.button("⚠️ LIMPAR MEUS DADOS LOCALMENTE", use_container_width=True):
            limpar_dados_locais()
            st.rerun()

# MÓDULO 1: CONFIGURAÇÃO
elif menu == "1. Configuração":
    st.header("📂 Configuração do Sistema")
    st.write(f"Modelo atual em uso: **{PLANILHA_PADRAO}**")
    arquivo_novo = st.file_uploader("Substituir planilha modelo temporariamente (.xlsx)", type=["xlsx"])
    if arquivo_novo:
        st.session_state['planilha_modelo'] = arquivo_novo
        st.session_state['estrutura_modelo'] = analisar_modelo_excel(arquivo_novo)
        st.success("Modelo atualizado para esta sessão!")
