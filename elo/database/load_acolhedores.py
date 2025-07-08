import os
import dotenv
import sqlite3
import csv
import argparse

dotenv.load_dotenv()  # Load environment variables from .env file


def carregar_acolhedores(caminho_csv):
    pasta_base = os.getenv("PASTA_BASE")
    NOME_BANCO_DADOS = os.getenv("NOME_BANCO_DADOS")
    
    if not pasta_base or not NOME_BANCO_DADOS:
        print("Erro: Variáveis de ambiente não estão configuradas.")
        return

    caminho_banco = os.path.join(pasta_base, NOME_BANCO_DADOS)
    
    try:
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        # Habilita o suporte a chaves estrangeiras para garantir a integridade
        cursor.execute("PRAGMA foreign_keys = ON;")
    except sqlite3.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return

    print(f"Iniciando carga do arquivo: {caminho_csv}")
    logs = {"sucesso": 0, "ja_existe": 0, "erro_gps": 0, "erro_linha": 0}

    try:
        with open(caminho_csv, mode="r", encoding="utf-8") as file:
            # DictReader usa a primeira linha do CSV como chaves do dicionário
            leitor_csv = csv.DictReader(file)

            for i, linha in enumerate(
                leitor_csv, start=2
            ):  # start=2 para contar a linha do cabeçalho
                nome = linha.get("acolhedor_nome")
                email = linha.get("acolhedor_email")
                lider_gps_nome = linha.get("nome_lider_gps")

                if not nome or not email or not lider_gps_nome:
                    print(
                        f"AVISO (Linha {i}): Linha incompleta. Todos os campos são obrigatórios. Ignorando."
                    )
                    logs["erro_linha"] += 1
                    continue

                # Passo 1: Encontrar o id_gps correspondente ao nome do líder
                cursor.execute(
                    "SELECT id_gps FROM gps WHERE nome_lider_gps = ?", (lider_gps_nome,)
                )
                resultado_gps = cursor.fetchone()

                if resultado_gps is None:
                    print(
                        f"ERRO (Linha {i}): Grupo com líder '{lider_gps_nome}' não encontrado no banco de dados. Ignorando acolhedor '{nome}'."
                    )
                    logs["erro_gps"] += 1
                    continue

                id_gps_db = resultado_gps[0]

                # Passo 2: Tentar inserir o novo acolhedor
                try:
                    cursor.execute(
                        "INSERT INTO acolhedores (acolhedor_nome, acolhedor_email, id_gps) VALUES (?, ?, ?)",
                        (nome, email, id_gps_db),
                    )
                    logs["sucesso"] += 1
                except sqlite3.IntegrityError:
                    # Este erro ocorre se o e-mail já existir (devido à restrição UNIQUE)
                    print(
                        f"AVISO (Linha {i}): Acolhedor com e-mail '{email}' já existe no banco. Ignorando."
                    )
                    logs["ja_existe"] += 1

    except FileNotFoundError:
        print(f"ERRO CRÍTICO: O arquivo '{caminho_csv}' não foi encontrado.")
        conn.close()
        return
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao ler o arquivo CSV: {e}")
        conn.close()
        return

    conn.commit()
    conn.close()

    print("\n--- Relatório de Carga de Acolhedores ---")
    print(f"Novos acolhedores inseridos com sucesso: {logs['sucesso']}")
    print(f"Acolhedores ignorados (já existiam): {logs['ja_existe']}")
    print(f"Erros (GPS não encontrado): {logs['erro_gps']}")
    print(f"Erros (Linhas com dados faltando): {logs['erro_linha']}")
    print("-----------------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script para carregar acolhedores de um arquivo CSV para o banco de dados."
    )
    parser.add_argument(
        "--caminho_csv",
        help="Caminho para o arquivo acolhedores.csv a ser carregado. Se não fornecido, tentará usar a variável de ambiente ACOLHEDORES_CSV_PATH.",
    )
    args = parser.parse_args()

    # Load CSV path from argument or environment variable
    csv_path = args.caminho_csv or os.getenv("ACOLHEDORES_CSV_PATH")

    if not csv_path:
        print(
            "ERRO: O caminho para o arquivo CSV não foi fornecido. Use --caminho_csv ou defina a variável de ambiente ACOLHEDORES_CSV_PATH."
        )
    else:
        carregar_acolhedores(csv_path)
