import os
import dotenv
import sqlite3
import csv
import argparse
from .utils import normalizar_string

dotenv.load_dotenv()

def verificar_variaveis_ambiente():
    """Verifica se todas as variáveis de ambiente necessárias estão configuradas."""
    variaveis_necessarias = ["PASTA_BASE", "NOME_BANCO_DADOS"]
    for var in variaveis_necessarias:
        if not os.getenv(var):
            print(f"ERRO CRÍTICO: Variável de ambiente '{var}' não configurada.")
            return False
    return True

def carregar_acolhedores(caminho_acolhedores_carga_csv):
    if not verificar_variaveis_ambiente():
        return

    pasta_base = os.getenv("PASTA_BASE")
    nome_db = os.getenv("NOME_BANCO_DADOS")
    caminho_banco = os.path.join(pasta_base, nome_db)
    conn = None

    if not os.path.exists(caminho_acolhedores_carga_csv):
        print(f"Erro: Arquivo de carga de acolhedores não encontrado: {caminho_acolhedores_carga_csv}")
        return

    try:
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        print(f"Iniciando carga do arquivo: {caminho_acolhedores_carga_csv}")
        logs = {"sucesso": 0, "ja_existe": 0, "erro_gps": 0, "erro_linha": 0}

        with open(caminho_acolhedores_carga_csv, mode="r", encoding="utf-8") as file:
            leitor_csv = csv.DictReader(file)

            for i, linha in enumerate(leitor_csv, start=2):
                nome = linha.get("Nome")
                apelido = linha.get("Apelido")
                email = linha.get("Email")
                lider_gps_nome_do_csv = linha.get("GP") # Este já vem normalizado do Gemini

                if not nome or not email or not lider_gps_nome_do_csv:
                    print(f"AVISO (Linha {i}): Linha incompleta. Ignorando.")
                    logs["erro_linha"] += 1
                    continue

                nome = normalizar_string(nome)

                # Usar o valor do CSV diretamente para a busca, pois Gemini já o normalizou
                cursor.execute(
                    "SELECT id_gps FROM gps WHERE nome_lider_gps = ?", (lider_gps_nome_do_csv,)
                )
                resultado_gps = cursor.fetchone()

                if resultado_gps is None:
                    print(f"ERRO (Linha {i}): GP com líder '{lider_gps_nome_do_csv}' não encontrado no banco de dados.")
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
        if conn:
            conn.rollback()

    finally:
        if conn:
            conn.close()

    print("\n--- Relatório de Carga de Acolhedores ---")
    if 'logs' in locals():
        print(f"Novos acolhedores inseridos: {logs['sucesso']}")
        print(f"Acolhedores ignorados (já existiam): {logs['ja_existe']}")
        print(f"Erros (GPS não encontrado): {logs['erro_gps']}")
        print(f"Erros (Linhas com dados faltando): {logs['erro_linha']}")
    print("-----------------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script para carregar acolhedores de um arquivo CSV para o banco de dados."
    )
    parser.add_argument("--caminho_acolhedores_carga_csv", required=True, help="Caminho para o arquivo acolhedores_carga.csv gerado.")
    args = parser.parse_args()

    carregar_acolhedores(args.caminho_acolhedores_carga_csv)
