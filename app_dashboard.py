import streamlit as st
import os
import sys
import io
from datetime import datetime

# Importa as funções de todos os nossos módulos de workflow
from generate_json import gerar_arquivo_carga
from load_database import carregar_base_de_dados
from load_acolhedores import carregar_acolhedores
from send_emails import enviar_notificacoes_personalizadas
from processar_e_gerar_json_respostas import gerar_json_respostas
from carregar_respostas import carregar_respostas_para_base
from upload_drive import upload_arquivo_db
from download_drive import download_arquivo_db


# --- Função Utilitária para Capturar Logs ---
def executar_e_capturar_output(funcao, *args, **kwargs):
    """
    Executa uma função e captura toda a sua saída de 'print' para exibir na tela.
    """
    stdout_original = sys.stdout
    sys.stdout = buffer_saida = io.StringIO()

    try:
        funcao(*args, **kwargs)
        output = buffer_saida.getvalue()
    except Exception as e:
        output = f"Ocorreu uma exceção inesperada:\n{e}"
    finally:
        sys.stdout = stdout_original

    return output


# --- Interface do Streamlit ---

st.set_page_config(page_title="Controle de Adoção ELO", layout="wide")

st.title(" Painel de Controle - ELO")
st.markdown(
    "Use esta interface para executar os diferentes passos do fluxo de trabalho."
)

# --- Colunas para Layout ---
col1, col2 = st.columns(2)

# --- Coluna 1: Carga de Dados ---
with col1:
    st.header("1. Carga de Dados Iniciais")
    st.info("Comece por aqui: gere os arquivos JSON e carregue os dados nas tabelas.")

    # 1.1 Gerar JSON de Acolhimento
    with st.expander(
        "Gerar intermediário de Acolhimento (a partir de um arquivo terminando com .txt no nome)"
    ):
        uploaded_txt = st.file_uploader(
            "Escolha o arquivo .txt com as informações dos visitantes"
        )
        if st.button("Gerar Arquivo JSON de Acolhimento"):
            if uploaded_txt is not None:
                # Salva o arquivo temporariamente para que a função possa lê-lo
                with open("temp_input.txt", "wb") as f:
                    f.write(uploaded_txt.getbuffer())

                with st.spinner("Processando com o Gemini para estruturar os dados..."):
                    logs = executar_e_capturar_output(
                        gerar_arquivo_carga, "temp_input.txt"
                    )
                    st.text_area("Logs da Geração:", logs, height=200)
                os.remove("temp_input.txt")  # Limpa o arquivo temporário
            else:
                st.warning("Por favor, carregue um arquivo .txt primeiro.")

    # 1.2 Carregar Acolhimento
    with st.expander(
        "Carregar arquivo estruturado com os visitantes para o Banco de Dados"
    ):
        data_acolhimento = st.text_input(
            "Digite a data do arquivo de carga (ddmmyy)", key="data_acolhimento"
        )
        if st.button("Carregar Visitantes na Base"):
            if data_acolhimento:
                with st.spinner("Carregando dados..."):
                    logs = executar_e_capturar_output(
                        carregar_base_de_dados, data_acolhimento
                    )
                    st.text_area("Logs da Carga:", logs, height=200)
            else:
                st.warning("Por favor, insira a data do arquivo.")

    # 1.3 Carregar Acolhedores
    with st.expander("Carregar/Atualizar Acolhedores (a partir de .csv)"):
        uploaded_csv = st.file_uploader("Escolha o arquivo acolhedores.csv")
        if st.button("Carregar Acolhedores na Base"):
            if uploaded_csv is not None:
                with open("temp_acolhedores.csv", "wb") as f:
                    f.write(uploaded_csv.getbuffer())

                with st.spinner("Carregando acolhedores..."):
                    logs = executar_e_capturar_output(
                        carregar_acolhedores, "temp_acolhedores.csv"
                    )
                    st.text_area("Logs da Carga de Acolhedores:", logs, height=200)
                os.remove("temp_acolhedores.csv")
            else:
                st.warning("Por favor, carregue um arquivo .csv primeiro.")


# --- Coluna 2: Comunicação e Sincronização ---
with col2:
    st.header("2. Ciclo de Comunicação")
    st.info("Após a carga, use estas funções para gerenciar a comunicação.")

    # 2.1 Disparar E-mails
    with st.expander("Disparar E-mails de Acolhimento"):
        if st.button("Disparar E-mails Agora", key="disparar"):
            with st.spinner("Verificando e enviando e-mails..."):
                logs = executar_e_capturar_output(enviar_notificacoes_personalizadas)
                st.text_area("Logs do Disparo:", logs, height=150)

    # 2.2 Processar Respostas
    with st.expander("Processar Respostas de E-mail e Gerar JSON"):
        if st.button("Processar Respostas Agora", key="processar"):
            with st.spinner("Lendo caixa de entrada e processando com IA..."):
                logs = executar_e_capturar_output(gerar_json_respostas)
                st.text_area("Logs do Processamento:", logs, height=150)

    # 2.3 Carregar Respostas
    with st.expander("Carregar Respostas para o Banco de Dados"):
        data_respostas = st.text_input(
            "Digite a data do arquivo de acompanhamento (ddmmyyyy)",
            key="data_respostas",
        )
        if st.button("Carregar Respostas na Base"):
            if data_respostas:
                with st.spinner("Atualizando banco de dados com as respostas..."):
                    logs = executar_e_capturar_output(
                        carregar_respostas_para_base, data_respostas
                    )
                    st.text_area("Logs da Carga de Respostas:", logs, height=150)
            else:
                st.warning("Por favor, insira a data do arquivo.")

    st.header("3. Sincronização com Google Drive")
    st.warning(
        "A primeira execução de cada uma destas ações abrirá uma janela no seu navegador para autorização."
    )

    # 3.1 Upload
    with st.expander("Enviar Banco de Dados para o Google Drive"):
        if st.button("Upload para o Drive"):
            with st.spinner("Fazendo upload do arquivo do banco de dados..."):
                logs = executar_e_capturar_output(upload_arquivo_db)
                st.text_area("Logs do Upload:", logs, height=100)

    # 3.2 Download
    with st.expander("Baixar Banco de Dados do Google Drive"):
        if st.button("Download do Drive"):
            with st.spinner("Baixando arquivo do banco de dados..."):
                logs = executar_e_capturar_output(download_arquivo_db)
                st.text_area("Logs do Download:", logs, height=100)
