import streamlit as st
import pandas as pd
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

# Arquivos e Configurações de Nome
DB_FILE = "dados_temporarios.json"
PLANILHA_PADRAO = "Levantamento_Base.xlsx"

# --- LISTA DE RESPONSÁVEIS TÉCNICOS (Edite aqui) ---
LISTA_TECNICOS = ["Selecione...", "Lívia Aguiar", "Rafael Argolo", "Adelmo Santana", "Outro"]

# --- FUNÇÕES DE PERSISTÊNCIA ---

def salvar_dados_locais(dados):
    with open(DB_FILE, "w") as f:
        json.dump(dados, f)

def carregar_dados_locais():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return []

def limpar_dados_locais():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    st.session_state['db_formularios'] = []

# --- FUNÇÃO DE ENVIO DE EMAIL ---

def enviar_email(arquivo_buffer, destinatario):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_REMETENTE = "levantamento.poupenergia@gmail.com"
    SENHA_REMETENTE = "kiqplowxqprcugjc" 

    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = destinatario
        msg['Subject'] = f"Levantamento de Cargas - {datetime.now().strftime('%d/%m/%Y')}"

        body = "Segue em anexo a planilha de levantamento de cargas atualizada."
        msg.attach(MIMEText(body, 'plain'))

        part = MIMEBase('application', 'octet-stream')
        part.set_payload(arquivo_buffer.getvalue())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= levantamento.xlsx")
        msg.attach(part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_REMETENTE)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erro ao enviar email: {e}")
        return False

# --- FUNÇÕES AUXILIARES DE EXCEL ---

def analisar_modelo_excel(file_content):
    """
    Identifica colunas e extrai listas suspensas reais do Excel.
    Aceita tanto bytes quanto o objeto UploadedFile do Streamlit.
    """
    # Se receber bytes (do arquivo local), transforma em buffer
    if isinstance(file_content, bytes):
        buffer = io.BytesIO(file_content)
    else:
        buffer = io.BytesIO(file_content.getvalue())
        
    wb = load_workbook(buffer, data_only=True)
    estrutura = {}

    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        headers = []
        for cell in sheet[1]:
            if cell.value:
                headers.append({
                    "nome": str(cell.value),
                    "col_letter": cell.column_letter,
                    "tipo": "texto",
                    "opcoes": []
                })

        for dv in sheet.data_validations.dataValidation:
            if dv.type == "list":
                for ref in str(dv.sqref).split():
                    col_letter = "".join(filter(str.isalpha, ref.split(':')[0]))
                    for h in headers:
                        if h["col_letter"] == col_letter:
                            h["tipo"] = "selecao"
                            formula = dv.formula1
                            if formula:
                                if formula.startswith('"') and formula.endswith('"'):
                                    h["opcoes"] = formula.strip('"').split(',')
                                elif formula.startswith('='):
                                    try:
                                        ref_range = formula.replace('=', '').replace('$', '')
                                        if '!' in ref_range:
                                            parts = ref_range.split('!')
                                            ref_sheet = wb[parts[0].replace("'", "")]
                                            cells = ref_sheet[parts[1]]
                                        else:
                                            cells = sheet[ref_range]
                                            
                                        vals = []
                                        if isinstance(cells, tuple):
                                            for row in cells:
                                                for cell_in_row in row:
                                                    if cell_in_row.value: vals.append(str(cell_in_row.value))
                                        else:
                                            if cells.value: vals.append(str(cells.value))
                                        h["opcoes"] = list(dict.fromkeys(vals))
                                    except:
                                        h["opcoes"] = ["Erro na Lista"]
        
        estrutura[sheet_name] = [{"nome": h["nome"], "tipo": h["tipo"], "opcoes": h["opcoes"]} for h in headers]
    return estrutura

# --- ESTADO DA APLICAÇÃO E CARREGAMENTO INICIAL ---

if 'db_formularios' not in st.session_state:
    st.session_state['db_formularios'] = carregar_dados_locais()

if 'planilha_modelo' not in st.session_state:
    st.session_state['planilha_modelo'] = None
    st.session_state['estrutura_modelo'] = {}

# LOGICA DE CARREGAMENTO AUTOMÁTICO DO ARQUIVO LOCAL
if not st.session_state['planilha_modelo']:
    if os.path.exists(PLANILHA_PADRAO):
        with open(PLANILHA_PADRAO, "rb") as f:
            content = f.read()
            # Criamos um objeto que simula o UploadedFile para o restante do código
            st.session_state['planilha_modelo'] = io.BytesIO(content)
            st.session_state['estrutura_modelo'] = analisar_modelo_excel(content)
            st.session_state['usando_padrao'] = True
    else:
        st.session_state['usando_padrao'] = False

def exportar_para_excel():
    if not st.session_state['planilha_modelo']:
        return None
    
    # Reposiciona o ponteiro do buffer para o início
    st.session_state['planilha_modelo'].seek(0)
    book = load_workbook(st.session_state['planilha_modelo'])

    for registro in st.session_state['db_formularios']:
        tipo_equipamento = registro['tipo_equipamento']
        if tipo_equipamento in book.sheetnames:
            sheet = book[tipo_equipamento]
            colunas_excel = [cell.value for cell in sheet[1]]
            nova_linha = []
            for col_nome in colunas_excel:
                valor = registro['dados'].get(col_nome, "")
                nova_linha.append(valor)
            sheet.append(nova_linha)

    output = io.BytesIO()
    book.save(output)
    output.seek(0)
    return output

# --- INTERFACE ---

st.title("⚡ Sistema de Levantamento de Cargas")

menu = st.sidebar.radio("Navegação", ["1. Configuração (Admin)", "2. Preenchimento (Técnico)", "3. Exportar & Finalizar"])

# MÓDULO 1: CONFIGURAÇÃO
if menu == "1. Configuração (Admin)":
    st.header("📂 Configuração do Modelo")
    
    if st.session_state.get('usando_padrao'):
        st.info(f"✅ O arquivo padrão **'{PLANILHA_PADRAO}'** foi carregado automaticamente.")
    
    st.markdown("---")
    st.subheader("Deseja trocar o modelo?")
    arquivo_novo = st.file_uploader("Carregar Nova Planilha Modelo (.xlsx)", type=["xlsx"])
    
    if arquivo_novo:
        st.session_state['planilha_modelo'] = arquivo_novo
        st.session_state['estrutura_modelo'] = analisar_modelo_excel(arquivo_novo)
        st.session_state['usando_padrao'] = False
        st.success("Novo modelo carregado com sucesso!")

# MÓDULO 2: PREENCHIMENTO
elif menu == "2. Preenchimento (Técnico)":
    st.header("📝 Novo Levantamento")
    if not st.session_state['estrutura_modelo']:
        st.warning("Nenhum modelo detectado. Por favor, adicione o arquivo 'Levantamento_Base.xlsx' na pasta ou faça o upload.")
    else:
        col1, col2 = st.columns(2)
        cod_instalacao = col1.text_input("Código de Instalação (UC)")
        
        # LISTA SUSPENSA PARA RESPONSÁVEL TÉCNICO
        responsavel = col2.selectbox("Responsável Técnico", options=LISTA_TECNICOS)
        
        opcoes_abas = list(st.session_state['estrutura_modelo'].keys())
        tipo_equipamento = st.selectbox("Tipo de Equipamento", options=opcoes_abas)

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
            
            if st.form_submit_button("➕ Adicionar Equipamento"):
                if cod_instalacao and responsavel != "Selecione...":
                    novo = {
                        "cod_instalacao": cod_instalacao,
                        "tipo_equipamento": tipo_equipamento,
                        "responsavel": responsavel,
                        "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "dados": respostas
                    }
                    st.session_state['db_formularios'].append(novo)
                    salvar_dados_locais(st.session_state['db_formularios'])
                    st.success("Equipamento registrado!")
                else:
                    st.error("Preencha a UC e selecione um Responsável Técnico.")

        if st.session_state['db_formularios']:
            st.divider()
            st.dataframe(pd.DataFrame(st.session_state['db_formularios'])[['cod_instalacao', 'tipo_equipamento', 'responsavel', 'data_hora']])

# MÓDULO 3: EXPORTAR E FINALIZAR
elif menu == "3. Exportar & Finalizar":
    st.header("💾 Exportar e Enviar Dados")
    
    if not st.session_state['db_formularios']:
        st.info("Nenhum dado pendente para exportação.")
    else:
        excel_final = exportar_para_excel()
        col_down, col_mail = st.columns(2)
        
        with col_down:
            st.subheader("Download Local")
            st.download_button("⬇️ Baixar Planilha (.xlsx)", data=excel_final, file_name=f"levantamento_{datetime.now().strftime('%d_%m_%H%M')}.xlsx")
        
        with col_mail:
            st.subheader("Enviar por E-mail")
            email_dest = st.text_input("E-mail do destinatário")
            if st.button("📧 Enviar Planilha"):
                if email_dest:
                    with st.spinner("Enviando..."):
                        if enviar_email(excel_final, email_dest):
                            st.success("E-mail enviado!")
                else:
                    st.warning("Informe o e-mail.")

        st.divider()
        if st.button("⚠️ FINALIZAR E APAGAR TUDO"):
            limpar_dados_locais()
            st.success("Sistema resetado.")
            st.rerun()
