import argparse
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure o Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def gerar_csv_com_llm(caminho_dados: str, caminho_gps: str):
    """
    Usa o Gemini para processar os arquivos CSV e gerar um arquivo CSV estruturado.
    """
    try:
        with open(caminho_dados, 'r', encoding='utf-8') as f:
            dados_csv = f.read()
        with open(caminho_gps, 'r', encoding='utf-8') as f:
            gps_csv = f.read()
    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado. {e}")
        return

    model = genai.GenerativeModel(os.getenv("MODEL"))

    prompt = f"""
    Você é um especialista em processamento de dados. Sua única função é receber dois arquivos CSV e retorná-los como um único CSV formatado.

    **Arquivo 1 (Dados dos Acolhedores):**
    (Colunas: `Carimbo_de_data/hora`, `Nome`, `apelido`, `Nascimento`, `email`, `numero`, `Nome_do_lider_de_gp`)
    ```csv
    {dados_csv}
    ```

    **Arquivo 2 (Dados dos GPs):**
    (Colunas: `GPS_name`, `LÍDER_name`)
    ```csv
    {gps_csv}
    ```

    **Tarefa:**

    1.  **Padronize** os nomes em `Nome_do_lider_de_gp` e `LÍDER_name` para o que estiver em LÍDER_name.
    3.  **Gere** um novo CSV com as seguintes colunas e mapeamento:
        *   `Nome` (de `Nome`)
        *   `Apelido` (de `apelido`)
        *   `Nascimento` (de `Nascimento`)
        *   `Email` (de `email`)
        *   `Celular` (de `numero`)
        *   `GP` (de `LÍDER_name`)

    **REGRAS DE SAÍDA:**
    *   **NÃO** inclua o cabeçalho CSV na sua resposta.
    *   **NÃO** inclua explicações, planos de ação ou qualquer texto extra.
    *   Sua resposta deve conter **APENAS** os dados CSV brutos, prontos para serem salvos em um arquivo.
    * NAO inclua cabeçalhos como ```csv ou ```no fim. Retorne raw text para receber o header do csv e ser salvo em arquivo.
    **Exemplo de Saída:**
    ```
"John Doe","Johnny","1990-01-01","john.doe@example.com","(11) 99999-9999","Rafael Ricardo"
"Jane Smith","Jane","1985-05-20","jane.smith@email.com","(21) 88888-8888","Aline figueiredo"
    ```
    """

    print("Enviando dados para o Gemini...")
    try:
        response = model.generate_content(prompt)
        csv_output = response.text.strip()

        # Limpa a saída para remover marcadores de código
        if csv_output.startswith("```csv"):
            csv_output = csv_output[6:]
        if csv_output.endswith("```"):
            csv_output = csv_output[:-3]
        csv_output = csv_output.strip()

        # Salva o arquivo CSV final
        pasta_csv = os.getenv("PASTA_CSV")
        if not pasta_csv:
            print("Erro: Variável de ambiente PASTA_CSV não configurada.")
            return

        caminho_saida = os.path.join(pasta_csv, "acolhedores_carga.csv")
        
        # Adiciona o cabeçalho ao arquivo
        header = "Nome,Apelido,Nascimento,Email,Celular,GP\n"
        with open(caminho_saida, 'w', encoding='utf-8') as f:
            f.write(header)
            f.write(csv_output)

        print(f"Arquivo '{caminho_saida}' gerado com sucesso!")
        return caminho_saida

    except Exception as e:
        print(f"Erro ao gerar o CSV com o Gemini: {e}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script para estruturar dados de acolhedores a partir de arquivos CSV."
    )
    parser.add_argument(
        "--data", required=True, help="Caminho para o arquivo data.csv."
    )
    parser.add_argument(
        "--gps", required=True, help="Caminho para o arquivo gps.csv."
    )
    args = parser.parse_args()

    gerar_csv_com_llm(args.data, args.gps)