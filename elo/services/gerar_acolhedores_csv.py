import pandas as pd
import argparse
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure o Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def standardize_leader_name(leader_name, model):
    """Usa o Gemini para padronizar o nome do líder."""
    prompt = f"""
    Padronize o seguinte nome para que ele seja consistente (remova apelidos, títulos e formate como 'Nome Sobrenome'):
    Nome original: {leader_name}
    Nome padronizado:
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Erro ao padronizar o nome '{leader_name}': {e}")
        return leader_name

def processar_acolhedores_csv(caminho_dados: str, caminho_gps: str):
    """
    Processa os arquivos CSV de acolhedores e GPs para gerar um arquivo CSV estruturado.
    """
    try:
        df_dados = pd.read_csv(caminho_dados)
        df_gps = pd.read_csv(caminho_gps)
    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado. {e}")
        return

    # Renomear colunas para facilitar o acesso
    df_dados.columns = [
        "nome_apelido",
        "nascimento",
        "email",
        "celular",
        "lider_gp",
    ]
    df_gps.columns = ["nome_gp", "lider_gp_padronizado"]

    # Inicializa o modelo Gemini
    model = genai.GenerativeModel(os.getenv("MODEL"))

    # Padroniza os nomes dos líderes em ambos os DataFrames
    print("Padronizando nomes dos líderes com o Gemini...")
    df_dados["lider_gp_padronizado"] = df_dados["lider_gp"].apply(
        lambda x: standardize_leader_name(x, model)
    )
    df_gps["lider_gp_padronizado_gemini"] = df_gps["lider_gp_padronizado"].apply(
        lambda x: standardize_leader_name(x, model)
    )

    # Merge dos DataFrames
    df_merged = pd.merge(
        df_dados,
        df_gps,
        left_on="lider_gp_padronizado",
        right_on="lider_gp_padronizado_gemini",
        how="left",
    )

    # Estrutura final do CSV
    df_final = df_merged[
        ["nome_apelido", "nascimento", "email", "celular", "nome_gp"]
    ]
    df_final = df_final.rename(
        columns={
            "nome_apelido": "NomeCompleto",
            "nascimento": "Nascimento",
            "email": "Email",
            "celular": "Celular",
            "nome_gp": "GP",
        }
    )

    # Salva o arquivo CSV final
    caminho_saida = "acolhedores_carga.csv"
    df_final.to_csv(caminho_saida, index=False)
    print(f"Arquivo '{caminho_saida}' gerado com sucesso!")


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

    processar_acolhedores_csv(args.data, args.gps)
