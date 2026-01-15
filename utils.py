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
from datetime import datetime, timedelta, timezone

# Constantes
PLANILHA_PADRAO_ADMIN = "Levantamento_Base.xlsx"

# DATAS E CAMINHOS
def get_data_hora_br():
    fuso_br = timezone(timedelta(hours=-3))
    return datetime.now(fuso_br)

def get_user_data_path(nome_usuario=None):
    user = nome_usuario if nome_usuario else st.session_state.get('usuario_ativo')
    if user:
        nome_limpo = "".join(filter(str.isalnum, user))
        return f"dados_{nome_limpo}.json"
    return None

def get_user_template_path(nome_usuario=None):
    user = nome_usuario if nome_usuario else st.session_state.get('usuario_ativo')
    if user:
        nome_limpo = "".join(filter(str.isalnum, user))
        return f"template_{nome_limpo}.xlsx"
    return None

# PERSISTÊNCIA JSON
def salvar_dados_locais(dados):
    path = get_user_data_path()
    if path:
        with open(path, "w") as f: json.dump(dados, f)

def carregar_dados_locais(path_especifico=None):
    path = path_especifico if path_especifico else get_user_data_path()
    if path and os.path.exists(path):
        with open(path, "r") as f: return json.load(f)
    return []

# LÓGICA EXCEL 
def analisar_modelo_excel(file_content):
    try:
        buffer = io.BytesIO(file_content) if isinstance(file_content, bytes) else io.BytesIO(file_content.getvalue())
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
                                if formula and formula.startswith('"'):
                                    h["opcoes"] = formula.strip('"').split(',')
            estrutura[sheet_name] = [{"nome": h["nome"], "tipo": h["tipo"], "opcoes": h["opcoes"]} for h in headers]
        return estrutura
    except Exception as e:
        st.error(f"Erro ao analisar o Excel: {e}")
        return {}

def carregar_modelo_atual():
    path_pessoal = get_user_template_path()
    if path_pessoal and os.path.exists(path_pessoal):
        with open(path_pessoal, "rb") as f:
            content = f.read()
            st.session_state['planilha_modelo'] = io.BytesIO(content)
            st.session_state['estrutura_modelo'] = analisar_modelo_excel(content)
            st.session_state['origem_modelo'] = "Pessoal"
    elif os.path.exists(PLANILHA_PADRAO_ADMIN):
        with open(PLANILHA_PADRAO_ADMIN, "rb") as f:
            content = f.read()
            st.session_state['planilha_modelo'] = io.BytesIO(content)
            st.session_state['estrutura_modelo'] = analisar_modelo_excel(content)
            st.session_state['origem_modelo'] = "Padrão do Sistema"

def exportar_para_excel(dados_lista):
    if 'planilha_modelo' not in st.session_state: return None
    st.session_state['planilha_modelo'].seek(0)
    book = load_workbook(st.session_state['planilha_modelo'])
    for registro in dados_lista:
        if registro['tipo_equipamento'] in book.sheetnames:
            sheet = book[registro['tipo_equipamento']]
            colunas_excel = [cell.value for cell in sheet[1]]
            nova_linha = [registro['dados'].get(col, "") for col in colunas_excel]
            sheet.append(nova_linha)
    output = io.BytesIO()
    book.save(output)
    output.seek(0)
    return output

# EMAIL
def enviar_email(arquivo_buffer, destinatario):
    try:
        msg = MIMEMultipart()
        msg['From'] = "levantamento.poupenergia@gmail.com"
        msg['To'] = destinatario
        msg['Subject'] = f"Levantamento {st.session_state['usuario_ativo']} - {get_data_hora_br().strftime('%d/%m/%Y')}"
        msg.attach(MIMEText("Relatório gerado pelo sistema de cargas.", 'plain'))
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(arquivo_buffer.getvalue())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename=levantamento.xlsx')
        msg.attach(part)
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login("levantamento.poupenergia@gmail.com", "kiqplowxqprcugjc")
        server.send_message(msg)
        server.quit()
        return True
    except: return False
