import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

def carregar_gps(caminho_arquivo_csv: str):
    """
    Carrega dados de um arquivo CSV para a tabela 'gps' no banco de dados SQLite.
    O CSV deve ter uma coluna chamada 'LÍDER_name'.
    """
    pasta_base = os.getenv("PASTA_BASE")
    nome_db = os.getenv("NOME_BANCO_DADOS")
    caminho_banco = os.path.join(pasta_base, nome_db)

    if not caminho_arquivo_csv or not os.path.exists(caminho_arquivo_csv):
        print(f"Erro: Caminho para o arquivo CSV de GPs é inválido ou o arquivo não foi encontrado: '{caminho_arquivo_csv}'")
        return

    try:
        df = pd.read_csv(caminho_arquivo_csv)
        if 'LÍDER_name' not in df.columns:
            print(f"Erro: O arquivo CSV deve conter a coluna 'LÍDER_name'. Colunas encontradas: {df.columns.tolist()}")
            return

    except Exception as e:
        print(f"Erro ao ler ou processar o arquivo CSV: {e}")
        return

    conn = sqlite3.connect(caminho_banco)
    cursor = conn.cursor()

    logs = {"sucesso": 0, "falha": 0, "ja_existe": 0}

    for index, row in df.iterrows():
        nome_lider = row.get("LÍDER_name")

        if not nome_lider:
            print(f"AVISO (Linha {index + 2}): Linha com nome do líder em branco. Ignorando.")
            continue

        try:
            # A vírgula após nome_lider é crucial, pois cria uma tupla de um elemento.
            cursor.execute(
                """
                INSERT INTO gps (nome_lider_gps)
                VALUES (?)
                """,
                (nome_lider,),
            )
            logs["sucesso"] += 1
        except sqlite3.IntegrityError:
            print(f"LOG: Líder '{nome_lider}' já existe no banco de dados. Ignorando.")
            logs["ja_existe"] += 1
        except sqlite3.Error as e:
            print(f"ERRO SQL ao inserir líder '{nome_lider}': {e}")
            logs["falha"] += 1

    conn.commit()
    conn.close()

    print("\n--- Relatório de Carga de GPs ---")
    print(f"GPs carregados com sucesso: {logs['sucesso']}")
    print(f"GPs ignorados (já existiam): {logs['ja_existe']}")
    print(f"Falhas na carga: {logs['falha']}")
    print("---------------------------------")