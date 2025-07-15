# ELO - Sistema de Automação para Acolhimento de Igreja

##  Propósito Principal

Este projeto é uma solução para automatizar o fluxo de trabalho do Ministério de Acolhimento, inicialmente desenvolvido de forma voluntária por e para os membros da [Primeira Igreja Batista de Iraja](https://www.igrejadeiraja.org.br/). O objetivo é eliminar tarefas manuais, organizar o processo de contato com visitantes e fornecer uma maneira centralizada e eficiente de gerenciar os dados, desde a entrada inicial até o acompanhamento e a sincronização entre múltiplos usuários.

O sistema utiliza uma combinação de scripts Python, uma base de dados local (SQLite), Inteligência Artificial (Google Gemini) para processamento de linguagem natural e uma interface gráfica amigável (Streamlit) para controle. Além de permitir a conexão de visualizadores de dados com a base dados para a construção de dashboards.

##  Recursos Principais

-   **Estruturação de Dados com IA:** Converte listas de visitantes semi-estruturadas (de arquivos de texto) em um formato JSON limpo e validado, usando o Google Gemini.
-   **Carga de Dados em Lote:** Permite carregar listas de novos visitantes e membros da equipe de acolhimento (`acolhedores`) para a base de dados a partir de arquivos JSON e CSV.
-   **Notificações Automatizadas:** Dispara e-mails personalizados para cada membro da equipe de acolhimento, contendo apenas a lista de visitantes pelos quais ele é responsável.
-   **Processamento de Respostas:** Lê a caixa de entrada de e-mail, interpreta as respostas dos acolhedores usando IA para entender o status do contato (ex: "Atendeu e tem interesse", "Não atendeu") e organiza esses dados para atualização.
-   **Painel de Controle Gráfico:** Oferece um dashboard local (via Streamlit) com botões para executar todas as funções do sistema, eliminando a necessidade de usar a linha de comando.
-   **Sincronização via Nuvem:** Permite o upload e download do arquivo do banco de dados para uma pasta no Google Drive, facilitando o compartilhamento e o backup da base de dados entre diferentes usuários e computadores.
-   **Interface de Linha de Comando (CLI):** Oferece uma CLI para executar todas as funções do sistema, ideal para automação e usuários avançados.

## Como Instalar e Configurar

1.  **Pré-requisitos:** Python 3.12 ou superior.
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
    uv sync
    ```
5.  **Configure as Variáveis de Ambiente:** Crie um arquivo chamado `.env` na raiz do projeto e preencha com suas chaves e caminhos:
    ```
    GEMINI_API_KEY="SUA_CHAVE_API_DO_GEMINI"
    EMAIL_USER="seu_email@gmail.com"
    EMAIL_PASS="sua_senha_de_app_de_16_digitos"
    PASTA_BASE="/caminho/absoluto/para/sua/pasta/base_dados"
    ```
    *   **Importante:** Certifique-se de que as pastas especificadas no `.env` existam. Se não existirem, crie-as manualmente.

6.  **Configure a API do Google Drive:** Para que a funcionalidade de upload e download com o Google Drive funcione, você precisa autenticar o sistema com sua conta Google. Siga os passos abaixo:
    *   **Acesse o Google Cloud Console:** Vá para [console.cloud.google.com](https://console.cloud.google.com/) e faça login com sua conta Google. Se você ainda não tiver um projeto, crie um novo.
    *   **Ative a API do Google Drive:** No menu de navegação, vá para **APIs e Serviços > Biblioteca**. Procure por "Google Drive API" e clique em **Ativar**.
    *   **Crie as Credenciais de Acesso:** Vá para **APIs e Serviços > Tela de permissão OAuth**. Selecione o tipo de usuário **Externo** e clique em **Criar**. Preencha as informações solicitadas (nome do aplicativo, e-mail de suporte, etc.) e clique em **Salvar e continuar**. Na tela de **Escopos**, não é necessário adicionar nenhum escopo. Clique em **Salvar e continuar**. Na tela de **Usuários de teste**, adicione seu próprio endereço de e-mail e clique em **Salvar e continuar**. Vá para **APIs e Serviços > Credenciais**. Clique em **Criar Credenciais > ID do cliente OAuth**. Selecione o tipo de aplicativo **App para computador**. Dê um nome para a credencial (ex: "Acolhimento App") e clique em **Criar**.
    *   **Baixe o `credentials.json`:** Após a criação, uma janela pop-up mostrará seu ID e segredo do cliente. Clique em **Fazer o download do JSON**. Renomeie o arquivo baixado para `credentials.json` e coloque-o na raiz do projeto.
    *   **Execute a Aplicação pela Primeira Vez:** Ao executar o `upload_drive.py` ou `download_drive.py` pela primeira vez (ou usando os botões no dashboard), uma janela do navegador será aberta pedindo para você autorizar o acesso à sua conta do Google Drive. Faça login e conceda as permissões necessárias. Após a autorização, um arquivo chamado `token.json` será criado automaticamente na raiz do projeto. Este arquivo armazena suas credenciais de acesso para que você não precise se autenticar novamente.
    *   **Importante:** Nunca compartilhe seus arquivos `credentials.json` ou `token.json`. Se você receber um erro de "Aplicativo não verificado", clique em "Avançado" e depois em "Acessar (nome do seu aplicativo)".

## Como Construir (Build) o Projeto

Para empacotar a aplicação para distribuição ou instalação, siga os passos abaixo:

1.  **Construa o Pacote:**
    ```bash
    uv build
    ```
    Este comando irá criar uma pasta `dist/` com os arquivos de distribuição (`.whl` e `.tar.gz`).

## Como Executar a Aplicação

Existem duas maneiras de executar a aplicação: através do painel de controle gráfico (Streamlit) ou via linha de comando (CLI).

### 1. Executando o Painel de Controle (Streamlit)

O painel de controle é a forma mais fácil e recomendada para a maioria dos usuários.

1.  **Instale o Pacote (se construído):**
    ```bash
    uv pip install dist/eloApp-0.1.0-py3-none-any.whl
    ```
2.  **Execute o Dashboard:**
    ```bash
    eloapp run_dashboard
    ```
    Este comando irá verificar o ambiente e, se tudo estiver correto, abrirá o painel de controle no seu navegador.

### 2. Executando via Linha de Comando (CLI)

A CLI é ideal para automação e para usuários que preferem trabalhar no terminal.

1.  **Instale o Pacote (se construído):**
    ```bash
    uv pip install dist/eloApp-0.1.0-py3-none-any.whl
    ```
2.  **Veja os Comandos Disponíveis:**
    ```bash
    eloapp --help
    ```
3.  **Exemplos de Uso:**
    *   **Gerar JSON de visitantes:**
        ```bash
        eloapp gerar_json entrada_dados/visitantes_exemplo.txt
        ```
    *   **Carregar acolhedores:**
        ```bash
        eloapp carregar_acolhedores entrada_dados/acolhedores.csv
        ```
    *   **Carregar visitantes:**
        ```bash
        eloapp carregar_acolhimento --data 260625
        ```
    *   **Disparar e-mails:**
        ```bash
        eloapp disparar_emails
        ```
    *   **Rodar o dashboard:**
        ```bash
        eloapp run_dashboard
        ```
