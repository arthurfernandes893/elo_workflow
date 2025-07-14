import sqlite3
import pandas as pd
import os
import unicodedata
import re
from dotenv import load_dotenv

load_dotenv()

def normalizar_string(s):
    """Normaliza uma string: minúsculas, sem acentos, sem espaços extras e com underscores."""
    if not isinstance(s, str):
        return ""
    # Remove acentos
    nfkd_form = unicodedata.normalize('NFKD', s)
    sem_acentos = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Remove caracteres especiais, substitui espaços por underscore e converte para minúsculas
    sem_acentos = re.sub(r'[^a-zA-Z0-9_]', '', sem_acentos)
    sem_espacos_extra = re.sub(r'\s+', ' ', sem_acentos).strip()
    com_underscore = sem_espacos_extra.replace(' ', '_')
    return com_underscore.lower()

def carregar_gps(caminho_arquivo_csv: str):
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
        nome_lider_original = row.get("LÍDER_name")

        if not nome_lider_original:
            print(f"AVISO (Linha {index + 2}): Linha com nome do líder em branco. Ignorando.")
            continue

        nome_lider_normalizado = normalizar_string(nome_lider_original)

        try:
            cursor.execute(
                """
                INSERT INTO gps (nome_lider_gps)
                VALUES (?)
                """,
                (nome_lider_normalizado,),
            )
            logs["sucesso"] += 1
        except sqlite3.IntegrityError:
            print(f"LOG: Líder '{nome_lider_normalizado}' (original: '{nome_lider_original}') já existe no banco de dados. Ignorando.")
            logs["ja_existe"] += 1
        except sqlite3.Error as e:
            print(f"ERRO SQL ao inserir líder '{nome_lider_normalizado}' (original: '{nome_lider_original}'): {e}")
            logs["falha"] += 1

    conn.commit()
    conn.close()

    print("\n--- Relatório de Carga de GPs ---")
    print(f"GPs carregados com sucesso: {logs['sucesso']}")
    print(f"GPs ignorados (já existiam): {logs['ja_existe']}")
    print(f"Falhas na carga: {logs['falha']}")
    print("---------------------------------")