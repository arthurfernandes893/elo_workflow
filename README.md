# Sistema de Automação para Acolhimento de Igreja

##  Propósito Principal

Este projeto é uma solução para automatizar o fluxo de trabalho do ministério de acolhimento, inicialmente desenvolvido de forma voluntária por e para os membros da [Primeira Igreja Batista de Iraja](https://www.igrejadeiraja.org.br/). O objetivo é eliminar tarefas manuais, organizar o processo de contato com visitantes e fornecer uma maneira centralizada e eficiente de gerenciar os dados, desde a entrada inicial até o acompanhamento e a sincronização entre múltiplos usuários.

O sistema utiliza uma combinação de scripts Python, uma base de dados local (SQLite), Inteligência Artificial (Google Gemini) para processamento de linguagem natural e uma interface gráfica amigável (Streamlit) para controle.

##  Recursos Principais

-   **Estruturação de Dados com IA:** Converte listas de visitantes semi-estruturadas (de arquivos de texto) em um formato JSON limpo e validado, usando o Google Gemini.
-   **Carga de Dados em Lote:** Permite carregar listas de novos visitantes e membros da equipe de acolhimento (`acolhedores`) para a base de dados a partir de arquivos JSON e CSV.
-   **Notificações Automatizadas:** Dispara e-mails personalizados para cada membro da equipe de acolhimento, contendo apenas a lista de visitantes pelos quais ele é responsável.
-   **Processamento de Respostas:** Lê a caixa de entrada de e-mail, interpreta as respostas dos acolhedores usando IA para entender o status do contato (ex: "Atendeu e tem interesse", "Não atendeu") e organiza esses dados para atualização.
-   **Painel de Controle Gráfico:** Oferece um dashboard local (via Streamlit) com botões para executar todas as funções do sistema, eliminando a necessidade de usar a linha de comando.
-   **Sincronização via Nuvem:** Permite o upload e download do arquivo do banco de dados para uma pasta no Google Drive, facilitando o compartilhamento e o backup da base de dados entre diferentes usuários e computadores.

##  Visão Geral do Fluxo de Trabalho

O sistema foi projetado para ser operado através do painel de controle (`app_dashboard.py`). O fluxo de trabalho típico é o seguinte:

1.  **Configuração Inicial (Feita uma única vez):**
    * Executa-se o script `setup_database.py` para criar o banco de dados.
    * Prepara-se um arquivo `acolhedores.csv` com os dados da equipe e usa-se o dashboard para carregá-los na base.

2.  **Ciclo Semanal de Visitantes:**
    * Um usuário cria um arquivo `.txt` simples com as informações dos novos visitantes.
    * No dashboard, ele usa o botão **"Gerar JSON de Acolhimento"**. O sistema lê o `.txt`, usa o Gemini para estruturar e validar os dados, e cria um arquivo `elo-carga_<data>.json`.
    * Em seguida, o usuário usa o botão **"Carregar Visitantes na Base"**, que lê o JSON recém-criado e insere os visitantes no banco de dados, distribuindo-os automaticamente entre os acolhedores.

3.  **Ciclo de Comunicação e Acompanhamento:**
    * O usuário clica em **"Disparar E-mails Agora"**. O sistema envia as notificações para a equipe.
    * Periodicamente (ex: diariamente), o usuário clica em **"Processar Respostas Agora"**. O sistema lê a caixa de entrada, interpreta as respostas dos acolhedores e gera um arquivo `acompanhamento_carga_<data>.json`.
    * Para finalizar, o usuário clica em **"Carregar Respostas na Base"** para atualizar o status de cada visitante no banco de dados.

4.  **Sincronização e Backup:**
    * Ao final de uma sessão de trabalho, o usuário clica em **"Upload para o Drive"** para salvar a versão mais recente e segura do banco de dados na nuvem.
    * Outro usuário, em outro computador, pode clicar em **"Download do Drive"** para baixar a versão mais recente, garantindo que todos trabalhem com os mesmos dados.

##  Descrição dos Scripts

O projeto é composto por vários módulos, cada um com uma responsabilidade específica:

-   `app_dashboard.py`: **(Ponto de Entrada Principal)** O front-end visual construído com Streamlit. Unifica todas as funcionalidades em uma interface gráfica com botões, tornando o sistema acessível a usuários não-técnicos.

-   `setup_database.py`: Script de configuração que cria o arquivo de banco de dados (`igreja_dados.db`) e define a estrutura das tabelas (`gps`, `acolhedores`, `acolhimento`).

-   `generate_json.py`: Recebe um arquivo `.txt` com dados de visitantes, envia para a API do Google Gemini e recebe de volta um arquivo JSON estruturado e validado.

-   `load_database.py`: Lê o arquivo `elo-carga_<data>.json` e insere os registros de novos visitantes na tabela `acolhimento`.

-   `load_acolhedores.py`: Lê um arquivo `acolhedores.csv` e carrega/atualiza os dados dos membros da equipe na tabela `acolhedores`.

-   `send_emails.py`: Conecta-se a um servidor SMTP para enviar e-mails de notificação personalizados para os acolhedores.

-   `processar_e_gerar_json_respostas.py`: Conecta-se a um servidor IMAP para ler e-mails de resposta, usa o Gemini para interpretar o conteúdo e gera um arquivo JSON com o status do acompanhamento.

-   `carregar_respostas.py`: Lê o JSON de acompanhamento e atualiza os registros correspondentes na tabela `acolhimento`.

-   `upload_drive.py`: Autentica-se na API do Google Drive e faz o upload (ou atualização) do arquivo `igreja_dados.db`.

-   `download_drive.py`: Autentica-se na API do Google Drive e baixa a versão mais recente do `igreja_dados.db`, fazendo um backup da versão local anterior.

-   `gerenciador.py`: Uma alternativa ao dashboard, oferece uma interface de linha de comando para executar todas as mesmas funções.

##  Como Instalar e Configurar

1.  **Pré-requisitos:** Python 3.8 ou superior.
2.  **Instale o `uv`:** Siga as instruções em [astral.sh/uv](https://astral.sh/uv) para instalar o gerenciador de pacotes.
3.  **Ambiente Virtual:**
    ```bash
    # Crie o ambiente
    uv venv
    # Ative o ambiente (Windows)
    .\.venv\Scripts\activate
    # Ative o ambiente (macOS/Linux)
    source .venv/bin/activate
    ```
4.  **Instale as Dependências:**
    ```bash
    uv pip install streamlit pandas google-generativeai python-dotenv google-api-python-client google-auth-httplib2 google-auth-oauthlib
    ```
5.  **Configure as Variáveis de Ambiente:** Crie um arquivo chamado `.env` na raiz do projeto e preencha com suas chaves e caminhos:
    ```
    GEMINI_API_KEY="SUA_CHAVE_API_DO_GEMINI"
    EMAIL_REMETENTE="seu_email@gmail.com"
    SENHA_EMAIL="sua_senha_de_app_de_16_digitos"
    PASTA_BASE="Caminho/Para/Sua/Pasta/base_dados"
    ```
6.  **Configure a API do Google Drive:** Siga as instruções do **Passo 0** da documentação do workflow para gerar o arquivo `credentials.json` e coloque-o na raiz do projeto.

##  Como Executar a Aplicação

Para iniciar o painel de controle principal, certifique-se de que seu ambiente virtual esteja ativado e execute o seguinte comando no terminal:

```bash
streamlit run app_dashboard.py
```

Uma janela no seu navegador será aberta com a aplicação pronta para uso.