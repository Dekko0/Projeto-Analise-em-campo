import streamlit as st

def apply_custom_style():
    # Injeta o CSS do Google Material Symbols
    st.markdown("""
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />
        <style>
            /* Classe para alinhar ícones com texto */
            .icon-text {
                font-family: 'Material Symbols Outlined';
                font-weight: normal;
                font-style: normal;
                font-size: 24px;  /* Tamanho padrão */
                line-height: 1;
                letter-spacing: normal;
                text-transform: none;
                display: inline-block;
                white-space: nowrap;
                word-wrap: normal;
                direction: ltr;
                vertical-align: middle;
                margin-right: 8px;
            }
            /* Ajuste para títulos maiores */
            h1 .icon-text, h2 .icon-text {
                font-size: 32px;
            }
            /* Ajuste para botões (se suportado pelo navegador/tema) */
            div.stButton > button {
                font-weight: 500;
            }
        </style>
    """, unsafe_allow_html=True)
