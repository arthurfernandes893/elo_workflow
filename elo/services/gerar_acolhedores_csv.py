import argparse
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def gerar_csv_com_llm(caminho_dados: str, gps_data_string: str):
    """
    Usa o Gemini para processar o CSV de acolhedores e a lista de GPs do banco de dados.
    """
    try:
        with open(caminho_dados, 'r', encoding='utf-8') as f:
            dados_csv = f.read()
    except FileNotFoundError as e:
        print(f"Erro: Arquivo de dados não encontrado. {e}")
        return

    model = genai.GenerativeModel(os.getenv("MODEL"))

    prompt = f"""
    Você é um especialista em processamento de dados. Sua única função é receber um arquivo CSV de acolhida e uma lista de líderes de GP e retorná-los como um único CSV formatado.

    **Arquivo 1 (Dados da Acolhida):**
    (Colunas: `Carimbo_de_data/hora`, `Nome`, `apelido`, `Nascimento`, `email`, `numero`, `Nome_do_lider_de_gp`)
    ```csv
    {dados_csv}
    ```

    **Arquivo 2 (Líderes de GP do Banco de Dados):**
    (Colunas: `id_gps`, `nome_lider_gps`)
    **IMPORTANTE: A coluna `nome_lider_gps` já está normalizada (minúsculas, sem acentos, com underscores).**
    ```csv
    {gps_data_string}
    ```

    **Tarefa:**

    1.  Encontre a correspondência exata entre o nome do líder em `Nome_do_lider_de_gp` do Arquivo 1 e a coluna `nome_lider_gps` do Arquivo 2.
    2.  **Gere** um novo CSV com as seguintes colunas e mapeamento:
        *   `Nome` (de `Nome`)
        *   `Apelido` (de `apelido`)
        *   `Nascimento` (de `Nascimento`)
        *   `Email` (de `email`)
        *   `Celular` (de `numero`)
        *   `GP` (use o valor EXATO de `nome_lider_gps` correspondente do Arquivo 2, SEM NENHUMA ALTERAÇÃO OU NORMALIZAÇÃO ADICIONAL)

    **REGRAS DE SAÍDA:**
    *   **NÃO** inclua o cabeçalho CSV na sua resposta.
    *   **NÃO** inclua explicações, planos de ação ou qualquer texto extra.
    *   Sua resposta deve conter **APENAS** os dados CSV brutos.

    **Exemplo de Saída:**
    ```
"John Doe","Johnny","1990-01-01","john.doe@example.com","(11) 99999-9999","rafael_ricardo"
"Jane Smith","Jane","1985-05-20","jane.smith@email.com","(21) 88888-8888","aline_figueiredo"
    ```
    """

    print("Enviando dados para o Gemini...")
    try:
        response = model.generate_content(prompt)
        csv_output = response.text.strip()

        if csv_output.startswith("```csv"):
            csv_output = csv_output[6:]
        if csv_output.endswith("```"):
            csv_output = csv_output[:-3]
        csv_output = csv_output.strip()

        pasta_csv = os.getenv("PASTA_CSV")
        if not pasta_csv:
            print("Erro: Variável de ambiente PASTA_CSV não configurada.")
            return

        caminho_saida = os.path.join(pasta_csv, "acolhedores_carga.csv")
        
        header = "Nome,Apelido,Nascimento,Email,Celular,GP\n"
        with open(caminho_saida, 'w', encoding='utf-8') as f:
            f.write(header)
            f.write(csv_output)

        print(f"Arquivo '{caminho_saida}' gerado com sucesso!")
        return caminho_saida

    except Exception as e:
        print(f"Erro ao gerar o CSV com o Gemini: {e}")
        return None

