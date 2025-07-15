import streamlit as st
import os
import sys
import io
import csv
import tempfile
from datetime import datetime, timedelta
import sqlite3
from elo.services.generate_json import gerar_arquivo_carga
from elo.database.load_database import carregar_base_de_dados
from elo.database.load_acolhedores import carregar_acolhedores
from elo.database.load_gps import carregar_gps
from elo.services.send_emails import enviar_notificacoes_personalizadas
from elo.services.processar_e_gerar_json_respostas import gerar_json_respostas
from elo.services.carregar_respostas import carregar_respostas_para_base
from elo.services.upload_drive import upload_arquivo_db
from elo.services.download_drive import download_arquivo_db
from elo.services.send_allocation import send_allocation_email


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


def run():
    # --- Interface do Streamlit ---
    st.set_page_config(page_title="Controle de Adoção ELO", layout="wide")

    st.title("ELO - Painel de Controle de Adoção")
    st.markdown("Use esta interface para executar os diferentes passos do fluxo de trabalho." \
    "\n1. Para salvar os acolhimentos, use o passo 1 e cole a lista gerada, no formato:\n" \
    "```bash\n" \
    "Data: dd/mm/yyyy \n\nEvento: conectados\n\n*Meninos*\nNome:\nIdade:\nNumero:\nAcolhedor:\n....\n" \
    "*Meninas*\nNome:\nIdade:\nNumero:\nAcolhedor:\n....\n" \
    "```" \
    "\n2. Para carregar um acolhimento para o banco de dados, selecione a data do culto informada na lista" \
    "\n3. Para atualizar o cadastro de membros, utilize o passo 4 fornecendo um arquivo `.csv` contendo as informações dos membros")

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
            date_obj_acolhimento = st.date_input("Selecione a data do arquivo de carga", format="DD/MM/YYYY")
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

        # 1.3 Gerar CSV de Acolhedores
        with st.expander("Passo 3: Gerar CSV de Acolhedores (com Gemini)", expanded=True):
            uploaded_raw_acolhedores_csv = st.file_uploader("Escolha o arquivo CSV bruto dos acolhedores (ex: acolhedores_dados.csv)", type=["csv"], key="raw_acolhedores_csv")
            
            if st.button("Gerar acolhedores_carga.csv"):
                if uploaded_raw_acolhedores_csv is not None:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="wb") as tmp_raw_data:
                        tmp_raw_data.write(uploaded_raw_acolhedores_csv.getbuffer())
                        tmp_raw_data_path = tmp_raw_data.name
                    
                    try:
                        # Query GPS data from DB
                        conn = sqlite3.connect(os.path.join(os.getenv("PASTA_BASE"), os.getenv("NOME_BANCO_DADOS")))
                        cursor = conn.cursor()
                        cursor.execute("SELECT id_gps, nome_lider_gps FROM gps")
                        gps_data = cursor.fetchall()
                        conn.close()

                        if not gps_data:
                            st.error("Erro: A tabela de GPs está vazia. Carregue os GPs primeiro.")
                        else:
                            output = io.StringIO()
                            writer = csv.writer(output)
                            writer.writerow(["id_gps", "nome_lider_gps"])
                            writer.writerows(gps_data)
                            gps_data_string = output.getvalue()

                            with st.spinner("Gerando acolhedores_carga.csv com Gemini..."):
                                # Call gerar_csv_com_llm
                                from elo.services.gerar_acolhedores_csv import gerar_csv_com_llm
                                caminho_saida_csv = gerar_csv_com_llm(tmp_raw_data_path, gps_data_string)
                                
                                if caminho_saida_csv:
                                    st.success(f"Arquivo '{os.path.basename(caminho_saida_csv)}' gerado com sucesso em {os.path.dirname(caminho_saida_csv)}!")
                                else:
                                    st.error("Falha ao gerar acolhedores_carga.csv.")
                    except Exception as e:
                        st.error(f"Ocorreu um erro inesperado durante a geração do CSV: {e}")
                    finally:
                        os.remove(tmp_raw_data_path)
                else:
                    st.warning("Por favor, carregue o arquivo CSV bruto dos acolhedores.")

        # 1.4 Carregar Acolhedores no Banco de Dados
        with st.expander("Passo 4: Carregar Acolhedores no Banco de Dados", expanded=True):
            st.info("Certifique-se de que 'acolhedores_carga.csv' foi gerado no passo anterior.")
            
            # Assuming acolhedores_carga.csv is saved in PASTA_CSV
            pasta_csv = os.getenv("PASTA_CSV")
            caminho_acolhedores_carga_csv = os.path.join(pasta_csv, "acolhedores_carga.csv")

            if st.button("Carregar acolhedores_carga.csv na Base"):
                if os.path.exists(caminho_acolhedores_carga_csv):
                    with st.spinner("Carregando acolhedores no banco de dados..."):
                        sucesso, logs = executar_e_capturar_output(
                            carregar_acolhedores, caminho_acolhedores_carga_csv
                        )
                        if sucesso:
                            st.success("Acolhedores carregados com sucesso no banco de dados!")
                        else:
                            st.error("Falha ao carregar acolhedores no banco de dados.")
                        with st.expander("Ver Logs da Carga de Acolhedores"):
                            st.text_area("", logs, height=200)
                else:
                    st.warning(f"Arquivo '{os.path.basename(caminho_acolhedores_carga_csv)}' não encontrado. Por favor, gere-o no Passo 3 primeiro.")

        # 1.4 Carregar GPs
        with st.expander("Passo 4: Carregar/Atualizar GPs (Opcional)"):
            uploaded_gps_data_csv = st.file_uploader("Escolha o arquivo de dados dos GPs (ex: gps_data.csv)", type=["csv"], key="gps_data_csv")
            
            if st.button("Carregar GPs na Base"):
                if uploaded_gps_data_csv is not None:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="wb") as tmp_gps_data:
                        tmp_gps_data.write(uploaded_gps_data_csv.getbuffer())
                        tmp_gps_data_path = tmp_gps_data.name
                    
                    try:
                        with st.spinner("Carregando GPs..."):
                            sucesso, logs = executar_e_capturar_output(
                                carregar_gps, tmp_gps_data_path
                            )
                            if sucesso:
                                st.success("GPs carregados com sucesso!")
                            else:
                                st.error("Falha ao carregar GPs.")
                            with st.expander("Ver Logs da Carga de GPs"):
                                st.text_area("", logs, height=200)
                    finally:
                        os.remove(tmp_gps_data_path)
                else:
                    st.warning("Por favor, carregue o arquivo .csv de dados dos GPs.")

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

        # 2.4 Enviar Alocação
        with st.expander("Enviar Relatório de Alocação de Acolhedores", expanded=True):
            st.info("Selecione o período para o relatório de alocações pendentes.")
            col1, col2 = st.columns(2)
            with col1:
                start_date_alloc = st.date_input("Data de Início", value=datetime.now() - timedelta(days=30))
            with col2:
                end_date_alloc = st.date_input("Data de Fim", value=datetime.now())

            if st.button("Enviar Relatório de Alocação"):
                if start_date_alloc and end_date_alloc:
                    with st.spinner("Gerando e enviando relatório de alocação..."):
                        sucesso, logs = executar_e_capturar_output(
                            send_allocation_email, 
                            start_date=start_date_alloc.strftime('%Y-%m-%d'), 
                            end_date=end_date_alloc.strftime('%Y-%m-%d')
                        )
                        if sucesso:
                            st.success("Relatório de alocação enviado com sucesso!")
                        else:
                            st.error("Falha no envio do relatório de alocação.")
                        with st.expander("Ver Logs do Envio"):
                            st.text_area("", logs, height=150)
                else:
                    st.warning("Por favor, selecione as datas de início e fim.")

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

run()