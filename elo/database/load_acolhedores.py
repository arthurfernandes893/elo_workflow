import os
import dotenv
import sqlite3
import csv
import argparse
from elo.services.gerar_acolhedores_csv import gerar_csv_com_llm

dotenv.load_dotenv()

def verificar_variaveis_ambiente():
    """Verifica se todas as variáveis de ambiente necessárias estão configuradas."""
    variaveis_necessarias = [
        "PASTA_BASE",
        "NOME_BANCO_DADOS",
        "GEMINI_API_KEY",
        "MODEL",
        "PASTA_CSV",
    ]
    for var in variaveis_necessarias:
        if not os.getenv(var):
            print(f"ERRO CRÍTICO: Variável de ambiente '{var}' não configurada.")
            return False
    return True

def carregar_acolhedores(caminho_dados_csv, caminho_gps_csv):
    if not verificar_variaveis_ambiente():
        return

    # Processa o CSV e obtém o caminho para o arquivo padronizado
    caminho_csv_padronizado = gerar_csv_com_llm(caminho_dados_csv, caminho_gps_csv)

    if not caminho_csv_padronizado or not os.path.exists(caminho_csv_padronizado):
        print("Erro: Não foi possível gerar ou encontrar o CSV padronizado dos acolhedores.")
        return

    # Tenta ler o conteúdo do CSV gerado para logging em caso de erro posterior
    csv_content_gerado = ""
    try:
        with open(caminho_csv_padronizado, mode="r", encoding="utf-8") as file:
            csv_content_gerado = file.read()
    except Exception as e:
        print(f"Erro ao ler o arquivo CSV gerado para log: {e}")
        # Mesmo com erro de leitura, tenta continuar para o banco de dados

    # Conexão com o banco de dados
    pasta_base = os.getenv("PASTA_BASE")
    nome_db = os.getenv("NOME_BANCO_DADOS")
    caminho_banco = os.path.join(pasta_base, nome_db)
    conn = None  # Inicializa a conexão como None

    try:
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        print(f"Iniciando carga do arquivo padronizado: {caminho_csv_padronizado}")
        logs = {"sucesso": 0, "ja_existe": 0, "erro_gps": 0, "erro_linha": 0}

        # Usa o conteúdo já lido para o DictReader
        leitor_csv = csv.DictReader(csv_content_gerado.splitlines())

        for i, linha in enumerate(leitor_csv, start=2):
            nome = linha.get("Nome")
            apelido = linha.get("Apelido")
            email = linha.get("Email")
            lider_gps_nome = linha.get("GP")

            if not nome or not email or not lider_gps_nome:
                print(f"AVISO (Linha {i}): Linha incompleta. Ignorando.")
                logs["erro_linha"] += 1
                continue

            cursor.execute(
                "SELECT id_gps FROM gps WHERE nome_lider_gps = ?", (lider_gps_nome,)
            )
            resultado_gps = cursor.fetchone()

            if resultado_gps is None:
                print(f"ERRO (Linha {i}): GP com líder '{lider_gps_nome}' não encontrado.")
                logs["erro_gps"] += 1
                continue

            id_gps_db = resultado_gps[0]

            try:
                cursor.execute(
                    "INSERT INTO acolhedores (acolhedor_nome, acolhedor_apelido, acolhedor_email, id_gps) VALUES (?, ?, ?, ?)",
                    (nome, apelido, email, id_gps_db),
                )
                logs["sucesso"] += 1
            except sqlite3.IntegrityError:
                print(f"AVISO (Linha {i}): Acolhedor com e-mail '{email}' já existe.")
                logs["ja_existe"] += 1

        conn.commit()

    except Exception as e:
        print(f"\n--- ERRO INESPERADO DURANTE A CARGA NO BANCO DE DADOS ---")
        print(f"Ocorreu um erro: {e}")
        print("\n--- CONTEÚDO DO CSV GERADO PELO GEMINI ---")
        print(csv_content_gerado)
        print("--------------------------------------------")
        if conn:
            conn.rollback() # Reverte qualquer mudança parcial

    finally:
        if conn:
            conn.close()

    print("\n--- Relatório de Carga de Acolhedores ---")
    print(f"Novos acolhedores inseridos: {logs['sucesso']}")
    print(f"Acolhedores ignorados (já existiam): {logs['ja_existe']}")
    print(f"Erros (GPS não encontrado): {logs['erro_gps']}")
    print(f"Erros (Linhas com dados faltando): {logs['erro_linha']}")
    print("-----------------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script para carregar acolhedores de um arquivo CSV para o banco de dados."
    )
    parser.add_argument("--caminho_dados_csv", help="Caminho para o arquivo de dados de acolhedores.")
    parser.add_argument("--caminho_gps_csv", help="Caminho para o arquivo de dados dos GPs.")
    args = parser.parse_args()

    if not args.caminho_dados_csv or not args.caminho_gps_csv:
        print("ERRO: Forneça os caminhos para os arquivos CSV de dados e de GPs.")
    else:
        carregar_acolhedores(args.caminho_dados_csv, args.caminho_gps_csv)