import streamlit as st
import os
import sys
import io
import tempfile
from datetime import datetime

from elo.services.generate_json import gerar_arquivo_carga
from elo.database.load_database import carregar_base_de_dados
from elo.database.load_acolhedores import carregar_acolhedores
from elo.services.send_emails import enviar_notificacoes_personalizadas
from elo.services.processar_e_gerar_json_respostas import gerar_json_respostas
from elo.services.carregar_respostas import carregar_respostas_para_base
from elo.services.upload_drive import upload_arquivo_db
from elo.services.download_drive import download_arquivo_db


# --- Função Utilitária para Capturar Logs ---
def executar_e_capturar_output(funcao, *args, **kwargs):
    """
    Executa uma função e captura toda a sua saída de 'print' para exibir na tela.
    Retorna uma tupla (sucesso, logs).
    """
    stdout_original = sys.stdout
    sys.stdout = buffer_saida = io.StringIO()
    sucesso = False
    try:
        funcao(*args, **kwargs)
        output = buffer_saida.getvalue()
        # Consideramos sucesso se não houver exceção e a saída não contiver "ERRO"
        if "erro" not in output.lower() and "exception" not in output.lower():
            sucesso = True
    except Exception as e:
        output = f"Ocorreu uma exceção inesperada:\n{e}"
    finally:
        sys.stdout = stdout_original

    return sucesso, output


# --- Interface do Streamlit ---
st.set_page_config(page_title="Controle de Adoção ELO", layout="wide")

st.title("ELO - Painel de Controle de Adoção")
st.markdown("Use esta interface para executar os diferentes passos do fluxo de trabalho." \
"\n1. Para salvar os acolhimentos, use o passo 1 e cole a lista gerada, no formato:\n" \
"```bash\n" \
"Data: dd/mm/yyyy \n\nNome:\nIdade:\nNumero:\nAcolhedor:\n....\n" \
"```" \
"\n2. Para carregar um acolhimento para o banco de dados, selecione a data do culto informada na lista" \
"\n3. Para atualizar o cadastro de membros, utilize o passo 3 fornecendo um arquivo `.csv` contendo as informações dos membros")

# --- Layout em Abas ---
tab1, tab2, tab3 = st.tabs(["1. Carga de Dados", "2. Comunicação", "3. Sincronização com Drive"])

# --- Aba 1: Carga de Dados ---
with tab1:
    st.header("Carga de Dados Iniciais")
    st.info("Comece por aqui: gere os arquivos JSON e carregue os dados nas tabelas.")

    # 1.1 Gerar JSON de Acolhimento
    with st.expander("Passo 1: Gerar JSON a partir de texto", expanded=True):
        input_text = st.text_area(
            "Cole aqui as informações dos visitantes", height=200, key="input_text"
        )
        if st.button("Gerar Arquivo JSON de Acolhimento"):
            if input_text:
                with st.spinner("Processando com o Gemini para estruturar os dados..."):
                    sucesso, logs = executar_e_capturar_output(
                        gerar_arquivo_carga, dados_entrada_texto=input_text
                    )
                    if sucesso:
                        st.success("Arquivo JSON gerado com sucesso!")
                    else:
                        st.error("Falha ao gerar o arquivo JSON.")
                    with st.expander("Ver Logs da Geração"):
                        st.text_area("", logs, height=200)
            else:
                st.warning("Por favor, insira os dados no campo de texto.")

    # 1.2 Carregar Acolhimento
    with st.expander("Passo 2: Carregar Visitantes para o Banco de Dados", expanded=True):
        date_obj_acolhimento = st.date_input("Selecione a data do arquivo de carga")
        if st.button("Carregar Visitantes na Base"):
            if date_obj_acolhimento:
                data_acolhimento_str = date_obj_acolhimento.strftime("%d%m%Y")
                with st.spinner("Carregando dados..."):
                    sucesso, logs = executar_e_capturar_output(
                        carregar_base_de_dados, data_acolhimento_str
                    )
                    if sucesso:
                        st.success("Visitantes carregados com sucesso no banco de dados!")
                    else:
                        st.error("Falha ao carregar os visitantes.")
                    with st.expander("Ver Logs da Carga"):
                        st.text_area("", logs, height=200)
            else:
                st.warning("Por favor, selecione a data do arquivo.")

    # 1.3 Carregar Acolhedores
    with st.expander("Passo 3: Carregar/Atualizar Acolhedores (Opcional)"):
        uploaded_csv = st.file_uploader("Escolha o arquivo acolhedores.csv")
        if st.button("Carregar Acolhedores na Base"):
            if uploaded_csv is not None:
                # Usa um arquivo temporário para segurança e limpeza automática
                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="wb") as tmp:
                    tmp.write(uploaded_csv.getbuffer())
                    tmp_path = tmp.name
                
                try:
                    with st.spinner("Carregando acolhedores..."):
                        sucesso, logs = executar_e_capturar_output(
                            carregar_acolhedores, tmp_path
                        )
                        if sucesso:
                            st.success("Acolhedores carregados com sucesso!")
                        else:
                            st.error("Falha ao carregar acolhedores.")
                        with st.expander("Ver Logs da Carga de Acolhedores"):
                            st.text_area("", logs, height=200)
                finally:
                    # Garante que o arquivo temporário seja removido
                    os.remove(tmp_path)
            else:
                st.warning("Por favor, carregue um arquivo .csv primeiro.")

# --- Aba 2: Comunicação ---
with tab2:
    st.header("Ciclo de Comunicação")
    st.info("Após a carga, use estas funções para gerenciar a comunicação.")

    # 2.1 Disparar E-mails
    with st.expander("Disparar E-mails de Acolhimento", expanded=True):
        if st.button("Disparar E-mails Agora"):
            with st.spinner("Verificando e enviando e-mails..."):
                sucesso, logs = executar_e_capturar_output(enviar_notificacoes_personalizadas)
                if sucesso:
                    st.success("E-mails enviados com sucesso!")
                else:
                    st.error("Falha no envio dos e-mails.")
                with st.expander("Ver Logs do Disparo"):
                    st.text_area("", logs, height=150)

    # 2.2 Processar Respostas
    with st.expander("Processar Respostas de E-mail e Gerar JSON", expanded=True):
        if st.button("Processar Respostas Agora"):
            with st.spinner("Lendo caixa de entrada e processando com IA..."):
                sucesso, logs = executar_e_capturar_output(gerar_json_respostas)
                if sucesso:
                    st.success("Respostas processadas e JSON gerado!")
                else:
                    st.error("Falha ao processar as respostas.")
                with st.expander("Ver Logs do Processamento"):
                    st.text_area("", logs, height=150)

    # 2.3 Carregar Respostas
    with st.expander("Carregar Respostas para o Banco de Dados", expanded=True):
        date_obj_respostas = st.date_input("Selecione a data do arquivo de acompanhamento")
        if st.button("Carregar Respostas na Base"):
            if date_obj_respostas:
                data_respostas_str = date_obj_respostas.strftime("%d%m%Y")
                with st.spinner("Atualizando banco de dados com as respostas..."):
                    sucesso, logs = executar_e_capturar_output(
                        carregar_respostas_para_base, data_respostas_str
                    )
                    if sucesso:
                        st.success("Respostas carregadas com sucesso!")
                    else:
                        st.error("Falha ao carregar as respostas.")
                    with st.expander("Ver Logs da Carga de Respostas"):
                        st.text_area("", logs, height=150)
            else:
                st.warning("Por favor, selecione a data do arquivo.")

# --- Aba 3: Sincronização com Google Drive ---
with tab3:
    st.header("Sincronização com Google Drive")
    st.warning(
        "A primeira execução de cada uma destas ações pode abrir uma janela no seu navegador para autorização."
    )

    col1, col2 = st.columns(2)
    with col1:
        with st.expander("Enviar para o Drive", expanded=True):
            if st.button("Upload para o Google Drive"):
                with st.spinner("Fazendo upload do arquivo do banco de dados..."):
                    sucesso, logs = executar_e_capturar_output(upload_arquivo_db)
                    if sucesso:
                        st.success("Upload para o Drive concluído com sucesso!")
                    else:
                        st.error("Falha no upload para o Drive.")
                    with st.expander("Ver Logs do Upload"):
                        st.text_area("", logs, height=100)
    
    with col2:
        with st.expander("Baixar do Drive", expanded=True):
            if st.button("Download do Google Drive"):
                with st.spinner("Baixando arquivo do banco dedados..."):
                    sucesso, logs = executar_e_capturar_output(download_arquivo_db)
                    if sucesso:
                        st.success("Download do Drive concluído com sucesso!")
                    else:
                        st.error("Falha no download do Drive.")
                    with st.expander("Ver Logs do Download"):
                        st.text_area("", logs, height=100)