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

##  Visão Geral do Fluxo de Trabalho

O sistema foi projetado para ser operado através do painel de controle (`app_dashboard.py`). O fluxo de trabalho típico é o seguinte:

1.  **Configuração Inicial (Feita uma única vez):**
    * Executa-se o script `setup_database.py` para criar o banco de dados.
    * Prepara-se os arquivos `acolhedores_dados.csv` (com os dados da equipe) e `gps.csv` (com os dados dos líderes de GP) e usa-se o dashboard para carregá-los na base.

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

-   `load_acolhedores.py`: Lê os arquivos `acolhedores_dados.csv` e `gps.csv` e carrega/atualiza os dados dos membros da equipe na tabela `acolhedores`.

-   `send_emails.py`: Conecta-se a um servidor SMTP para enviar e-mails de notificação personalizados para os acolhedores.

-   `processar_e_gerar_json_respostas.py`: Conecta-se a um servidor IMAP para ler e-mails de resposta, usa o Gemini para interpretar o conteúdo e gera um arquivo JSON com o status do acompanhamento.

-   `carregar_respostas.py`: Lê o JSON de acompanhamento e atualiza os registros correspondentes na tabela `acolhimento`.

-   `upload_drive.py`: Autentica-se na API do Google Drive e faz o upload (ou atualização) do arquivo `igreja_dados.db` da pasta `base_dados`.

-   `download_drive.py`: Autentica-se na API do Google Drive e baixa a versão mais recente do `igreja_dados.db` para a pasta `base_dados`, fazendo um backup da versão local anterior.

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
    uv sync
    ```
5.  **Configure as Variáveis de Ambiente:** Crie um arquivo chamado `.env` na raiz do projeto e preencha com suas chaves e caminhos:
    ```
    GEMINI_API_KEY="SUA_CHAVE_API_DO_GEMINI"
    EMAIL_REMETENTE="seu_email@gmail.com"
    SENHA_EMAIL="sua_senha_de_app_de_16_digitos"
    PASTA_BASE="/caminho/absoluto/para/sua/pasta/base_dados"
    ```
    *   **Importante:** Certifique-se de que a pasta especificada em `PASTA_BASE` exista. Se não existir, crie-a manualmente.

6.  **Configure a API do Google Drive:** Para que a funcionalidade de upload e download com o Google Drive funcione, você precisa autenticar o sistema com sua conta Google. Siga os passos abaixo:
    *   **Acesse o Google Cloud Console:** Vá para [console.cloud.google.com](https://console.cloud.google.com/) e faça login com sua conta Google. Se você ainda não tiver um projeto, crie um novo.
    *   **Ative a API do Google Drive:** No menu de navegação, vá para **APIs e Serviços > Biblioteca**. Procure por "Google Drive API" e clique em **Ativar**.
    *   **Crie as Credenciais de Acesso:** Vá para **APIs e Serviços > Tela de permissão OAuth**. Selecione o tipo de usuário **Externo** e clique em **Criar**. Preencha as informações solicitadas (nome do aplicativo, e-mail de suporte, etc.) e clique em **Salvar e continuar**. Na tela de **Escopos**, não é necessário adicionar nenhum escopo. Clique em **Salvar e continuar**. Na tela de **Usuários de teste**, adicione seu próprio endereço de e-mail e clique em **Salvar e continuar**. Vá para **APIs e Serviços > Credenciais**. Clique em **Criar Credenciais > ID do cliente OAuth**. Selecione o tipo de aplicativo **App para computador**. Dê um nome para a credencial (ex: "Acolhimento App") e clique em **Criar**.
    *   **Baixe o `credentials.json`:** Após a criação, uma janela pop-up mostrará seu ID e segredo do cliente. Clique em **Fazer o download do JSON**. Renomeie o arquivo baixado para `credentials.json`.
    *   **Mova o `credentials.json` para o Projeto:** Coloque o arquivo `credentials.json` na raiz do seu projeto.
    *   **Execute a Aplicação pela Primeira Vez:** Ao executar o `upload_drive.py` ou `download_drive.py` pela primeira vez (ou usando os botões no dashboard), uma janela do navegador será aberta pedindo para você autorizar o acesso à sua conta do Google Drive. Faça login e conceda as permissões necessárias. Após a autorização, um arquivo chamado `token.json` será criado automaticamente na raiz do projeto. Este arquivo armazena suas credenciais de acesso para que você não precise se autenticar novamente.
    *   **Importante:** Nunca compartilhe seus arquivos `credentials.json` ou `token.json`. Se você receber um erro de "Aplicativo não verificado", clique em "Avançado" e depois em "Acessar (nome do seu aplicativo)".

##  Estrutura de Pastas Essenciais

Para o correto funcionamento do sistema, as seguintes pastas são esperadas na raiz do projeto:

-   `base_dados/`: Esta é a pasta referenciada pela variável `PASTA_BASE` no seu arquivo `.env`. É onde os arquivos JSON intermediários (`elo-carga_*.json`, `acompanhamento_carga_*.json`) e o arquivo do banco de dados (`igreja_dados.db`) serão armazenados ou lidos.
-   `entrada_dados/`: (Opcional, mas recomendado para organização) Sugere-se usar esta pasta para armazenar os arquivos `.txt` de entrada com os dados dos visitantes e o `acolhedores.csv`.

### Exemplo de Arquivos de Entrada:

**`entrada_dados/visitantes_exemplo.txt` (para `generate_json.py`):**
```
Nome: João Silva, Idade: 30, Celular: 99999-8888, Acolhedor: Maria Acolhedora
Nome: Ana Souza, Celular: 98765-4321, Acolhedor: João Acolhedor
Nome: Pedro Santos, Idade: 25, Acolhedor: Maria Acolhedora
Nome: Carla Lima, Idade: 40, Celular: 91234-5678, Acolhedor: Pedro Acolhedor
```

**`entrada_dados/acolhedores.csv` (para `load_acolhedores.py`):**
```csv
acolhedor_nome,acolhedor_email,nome_lider_gps
João Acolhedor,joao.acolhedor@seuemail.com,Líder Exemplo 1
Maria Acolhedora,maria.acolhedora@seuemail.com,Líder Exemplo 1
Pedro Acolhedor,pedro.acolhedor@seuemail.com,L��der Exemplo 2
```

##  Como Executar a Aplicação

Para iniciar o painel de controle principal, certifique-se de que seu ambiente virtual esteja ativado e execute o seguinte comando no terminal:

```bash
streamlit run app_dashboard.py
```

Uma janela no seu navegador será aberta com a aplicação pronta para uso.

## Como Executar os Scripts Individualmente

Além do painel de controle, você pode executar cada script Python diretamente via terminal. Certifique-se de que seu ambiente virtual esteja ativado (`source .venv/bin/activate` ou `.\.venv\Scripts\activate`).

**Configuração Inicial:**

-   **`setup_database.py`**: Cria o banco de dados e as tabelas.
    ```bash
    python setup_database.py
    ```

**Carga de Dados:**

-   **`generate_json.py`**: Gera um arquivo JSON estruturado a partir de um TXT de visitantes.
    ```bash
    python generate_json.py <caminho_para_o_arquivo_txt>
    # Exemplo: python generate_json.py entrada_dados/visitantes_exemplo.txt
    ```

-   **`load_database.py`**: Carrega visitantes de um arquivo JSON para o banco de dados.
    ```bash
    python load_database.py <caminho_para_o_arquivo_json>
    # Exemplo: python load_database.py base_dados/elo-carga_2023-10-27.json
    ```

-   **`load_acolhedores.py`**: Carrega dados de acolhedores de CSVs para o banco de dados.
    ```bash
    # Opção 1: Usando variáveis de ambiente (recomendado para automação)
    export ACOLHEDORES_DADOS_CSV_PATH="entrada_dados/acolhedores_dados.csv" # macOS/Linux
    export GPS_CSV_PATH="entrada_dados/gps.csv" # macOS/Linux
    # set ACOLHEDORES_DADOS_CSV_PATH="entrada_dados/acolhedores_dados.csv" # Windows
    # set GPS_CSV_PATH="entrada_dados/gps.csv" # Windows
    python load_acolhedores.py

    # Opção 2: Passando os caminhos como argumentos
    python load_acolhedores.py --caminho_dados_csv entrada_dados/acolhedores_dados.csv --caminho_gps_csv entrada_dados/gps.csv
    ```

**Comunicação e Acompanhamento:**

-   **`send_emails.py`**: Envia e-mails de notificação para os acolhedores.
    ```bash
    python send_emails.py
    ```

-   **`processar_e_gerar_json_respostas.py`**: Processa respostas de e-mails e gera um JSON de acompanhamento.
    ```bash
    python processar_e_gerar_json_respostas.py
    ```

-   **`carregar_respostas.py`**: Atualiza o status dos visitantes no banco de dados com base no JSON de acompanhamento.
    ```bash
    python carregar_respostas.py <caminho_para_o_arquivo_json_respostas>
    # Exemplo: python carregar_respostas.py base_dados/acompanhamento_carga_2023-10-27.json
    ```

**Sincronização com Google Drive:**

-   **`upload_drive.py`**: Faz upload do banco de dados para o Google Drive.
    ```bash
    python upload_drive.py
    ```

-   **`download_drive.py`**: Faz download do banco de dados do Google Drive.
    ```bash
    python download_drive.py
    ```

**Interface de Linha de Comando Alternativa:**

-   **`gerenciador.py`**: Oferece uma interface de linha de comando interativa para todas as funções.
    ```bash
    python gerenciador.py
    ```
