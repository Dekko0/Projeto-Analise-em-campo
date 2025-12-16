import streamlit as st
import pandas as pd
import io
from openpyxl import load_workbook
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Levantamento de Cargas", layout="wide", page_icon="⚡")

# --- ESTADO DA APLICAÇÃO (Simulando Banco de Dados) ---
if 'db_formularios' not in st.session_state:
    st.session_state['db_formularios'] = [] # Lista de dicionários com os dados preenchidos
if 'planilha_modelo' not in st.session_state:
    st.session_state['planilha_modelo'] = None # O arquivo Excel carregado
if 'estrutura_modelo' not in st.session_state:
    st.session_state['estrutura_modelo'] = {} # Cache da estrutura das abas

# --- FUNÇÕES AUXILIARES ---

def analisar_modelo_excel(uploaded_file):
    """
    Lê o Excel e define quais campos são Texto e quais são Dropdown
    baseado nas regras do prompt (conteúdo das colunas).
    """
    xls = pd.ExcelFile(uploaded_file)
    estrutura = {}
    
    for sheet_name in xls.sheet_names:
        # Lê a aba. Assume-se que a linha 1 é cabeçalho.
        df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
        
        campos = []
        for coluna in df.columns:
            # Regra de Negócio: Analisar conteúdo para definir tipo
            # Se a coluna tem valores pré-definidos na planilha modelo (ex: Sim/Não), vira Select
            # Se for vazia ou tiver "Digitável", vira Input
            
            valores_unicos = df[coluna].dropna().unique().tolist()
            tipo = "texto"
            opcoes = []
            
            # Lógica de detecção
            str_valores = [str(v).lower() for v in valores_unicos]
            if "digitável" in str_valores or len(valores_unicos) == 0:
                tipo = "texto"
            elif len(valores_unicos) > 0:
                tipo = "selecao"
                opcoes = valores_unicos
            
            campos.append({
                "nome": coluna,
                "tipo": tipo,
                "opcoes": opcoes
            })
            
        estrutura[sheet_name] = campos
    
    return estrutura

def exportar_para_excel():
    """
    Pega o modelo original e preenche com os dados salvos na memória.
    """
    if not st.session_state['planilha_modelo']:
        return None

    # Carrega o arquivo original na memória para edição
    buffer = io.BytesIO(st.session_state['planilha_modelo'].getvalue())
    book = load_workbook(buffer)

    # Itera sobre os dados salvos
    for registro in st.session_state['db_formularios']:
        tipo_equipamento = registro['tipo_equipamento']
        
        if tipo_equipamento in book.sheetnames:
            sheet = book[tipo_equipamento]
            
            # --- CORREÇÃO DA LÓGICA DE PREENCHIMENTO ---
            # 1. Obter os cabeçalhos do Excel (Linha 1)
            colunas_excel = [cell.value for cell in sheet[1]]
            
            # 2. Preparar a linha de dados, respeitando a ordem do Excel
            nova_linha = []
            
            for col_nome in colunas_excel:
                # Busca o valor no registro salvo (ou vazio se não existir)
                # Adiciona o valor à lista na ordem correta
                valor = registro['dados'].get(col_nome, "")
                nova_linha.append(valor)
            
            # 3. Adiciona a nova linha de dados na próxima linha disponível
            sheet.append(nova_linha)

    # Salva o resultado em um novo buffer
    output = io.BytesIO()
    book.save(output)
    output.seek(0)
    return output

# --- INTERFACE DO USUÁRIO ---

st.title("⚡ Sistema de Levantamento de Cargas")

# Menu Lateral
menu = st.sidebar.radio("Navegação", ["1. Configuração (Admin)", "2. Preenchimento (Técnico)", "3. Exportar Dados"])

# ---------------------------------------------------------
# MÓDULO 1: CONFIGURAÇÃO (ADMIN)
# ---------------------------------------------------------
if menu == "1. Configuração (Admin)":
    st.header("📂 Configuração do Modelo")
    st.markdown("Faça o upload da planilha Excel modelo. O sistema criará os formulários automaticamente baseados nas abas e colunas.")

    arquivo = st.file_uploader("Carregar Planilha Modelo (.xlsx)", type=["xlsx"])

    if arquivo:
        st.session_state['planilha_modelo'] = arquivo
        # Processar estrutura
        st.session_state['estrutura_modelo'] = analisar_modelo_excel(arquivo)
        st.success("Modelo carregado e processado com sucesso!")
        
        with st.expander("Ver Estrutura Identificada"):
            st.json(st.session_state['estrutura_modelo'])
            
    # Botão para gerar um modelo de teste caso o usuário não tenha um
    if st.button("Não tem planilha? Gerar Modelo de Teste"):
        # Cria um Excel simples em memória para teste
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        # Aba Ar Condicionado
        df_ar = pd.DataFrame({
            'Local': ['Sala', 'Quarto'], # Exemplo para virar dropdown
            'BTUs': ['Digitável', 'Digitável'],
            'Tecnologia': ['Inverter', 'Convencional'],
            'Marca': ['Digitável', 'Digitável']
        })
        df_ar.to_excel(writer, sheet_name='Ar Condicionado', index=False)
        
        # Aba Iluminação
        df_luz = pd.DataFrame({
            'Ambiente': ['Cozinha', 'Sala'],
            'Tipo Lâmpada': ['LED', 'Incandescente', 'Fluorescente'],
            'Potência (W)': ['Digitável', 'Digitável'],
            'Qtd': ['Digitável', 'Digitável']
        })
        df_luz.to_excel(writer, sheet_name='Iluminação', index=False)
        
        writer.close()
        output.seek(0)
        
        st.download_button(
            label="⬇️ Baixar Modelo Exemplo",
            data=output,
            file_name="modelo_padrao.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ---------------------------------------------------------
# MÓDULO 2: PREENCHIMENTO (TÉCNICO)
# ---------------------------------------------------------
elif menu == "2. Preenchimento (Técnico)":
    st.header("📝 Novo Levantamento")

    if not st.session_state['estrutura_modelo']:
        st.warning("⚠️ Por favor, carregue a planilha modelo na aba 'Configuração' primeiro.")
    else:
        # Dados da Unidade
        col1, col2 = st.columns(2)
        cod_instalacao = col1.text_input("Código de Instalação (UC)", placeholder="Ex: 123456789")
        responsavel = col2.text_input("Responsável Técnico", placeholder="Nome do técnico")

        st.divider()

        # Seleção do Tipo de Equipamento (Baseado nas Abas do Excel)
        opcoes_abas = list(st.session_state['estrutura_modelo'].keys())
        tipo_equipamento = st.selectbox("Selecione o Tipo de Equipamento", options=opcoes_abas)

        st.subheader(f"Detalhes: {tipo_equipamento}")
        
        # GERAÇÃO DINÂMICA DO FORMULÁRIO
        campos = st.session_state['estrutura_modelo'][tipo_equipamento]
        respostas = {}
        
        with st.form("form_tecnico"):
            # Cria colunas dinâmicas para layout (2 campos por linha)
            cols = st.columns(2)
            
            for i, campo in enumerate(campos):
                col_atual = cols[i % 2]
                
                label = campo['nome']
                
                if campo['tipo'] == 'selecao':
                    val = col_atual.selectbox(label, options=campo['opcoes'])
                else:
                    # Input de texto (Digitável)
                    val = col_atual.text_input(label)
                
                respostas[label] = val
            
            # Botão de Salvar
            submitted = st.form_submit_button("➕ Adicionar Equipamento")
            
            if submitted:
                if not cod_instalacao:
                    st.error("O Código de Instalação é obrigatório!")
                else:
                    # Cria o objeto de registro
                    novo_registro = {
                        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                        "cod_instalacao": cod_instalacao,
                        "responsavel": responsavel,
                        "tipo_equipamento": tipo_equipamento,
                        "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "dados": respostas
                    }
                    
                    st.session_state['db_formularios'].append(novo_registro)
                    st.success(f"{tipo_equipamento} adicionado com sucesso à UC {cod_instalacao}!")

        # Visualizar itens já adicionados nesta sessão
        if len(st.session_state['db_formularios']) > 0:
            st.divider()
            st.markdown("### 📋 Itens adicionados nesta sessão")
            df_view = pd.DataFrame(st.session_state['db_formularios'])
            # Mostra apenas colunas resumo
            st.dataframe(df_view[['cod_instalacao', 'tipo_equipamento', 'responsavel', 'data_hora']], use_container_width=True)

# ---------------------------------------------------------
# MÓDULO 3: EXPORTAÇÃO
# ---------------------------------------------------------
elif menu == "3. Exportar Dados":
    st.header("💾 Exportar Planilha Final")
    
    qtd_registros = len(st.session_state['db_formularios'])
    st.metric("Total de Equipamentos Registrados", qtd_registros)
    
    if qtd_registros > 0 and st.session_state['planilha_modelo']:
        excel_processado = exportar_para_excel()
        
        if excel_processado:
            st.download_button(
                label="⬇️ Baixar Planilha Preenchida (.xlsx)",
                data=excel_processado,
                file_name=f"levantamento_cargas_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.success("Planilha gerada com a mesma estrutura do modelo original!")
    
    elif qtd_registros == 0:
        st.info("Nenhum formulário foi preenchido ainda.")
    elif not st.session_state['planilha_modelo']:
        st.error("Modelo de planilha não encontrado. Volte para Configuração.")