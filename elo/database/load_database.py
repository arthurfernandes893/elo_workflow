import sqlite3
import json
import os
import argparse
from dotenv import load_dotenv

load_dotenv()


def carregar_base_de_dados(data_param: str):
    """
    Carrega dados de um arquivo JSON para o banco de dados SQLite.
    O arquivo é encontrado com base na data fornecida.
    """
    pasta_base = os.getenv("PASTA_BASE")
    pasta_json = os.getenv("PASTA_JSON")
    nome_db = os.getenv("NOME_BANCO_DADOS")

    if not pasta_base:
        print("Erro: Variável de ambiente PASTA_BASE não está configurada.")
        return

    nome_arquivo = f"EloCargaDados_{data_param}.json"
    caminho_arquivo = os.path.join(pasta_json, nome_arquivo)

    if not os.path.exists(caminho_arquivo):
        print(f"Erro: Arquivo '{nome_arquivo}' não encontrado na pasta '{pasta_base}'.")
        return

    print(f"Iniciando carga do arquivo: {caminho_arquivo}")

    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        registros = json.load(f)
        caminho_banco = os.path.join(pasta_base, nome_db)
    conn = sqlite3.connect(caminho_banco)
    cursor = conn.cursor()
    # Habilita o suporte a chaves estrangeiras
    cursor.execute("PRAGMA foreign_keys = ON;")

    logs = {"sucesso": 0, "descartado": 0, "erros_acolhedor": 0}
    data_decisao = registros["data"]

    for reg in registros["lista"]:
        plano = reg.get("plano_de_acao", "")

        if "Descartar" in plano:
            print(
                f"LOG: Registro para '{reg.get('nome', 'N/A')}' descartado conforme plano de ação: {plano}."
            )
            logs["descartado"] += 1
            continue

        nome_acolhedor = reg.get("acolhedor")

        # Busca o ID do acolhedor no banco de dados, verificando nome ou apelido
        cursor.execute(
            "SELECT id_acolhedor FROM acolhedores WHERE acolhedor_nome = ? OR acolhedor_apelido = ?",
            (nome_acolhedor, nome_acolhedor,),
        )
        resultado = cursor.fetchone()

        if resultado is None:
            print(
                f"ERRO DE CARGA: Acolhedor '{nome_acolhedor}' não encontrado no banco de dados para o visitante '{reg.get('nome')}'. Registro ignorado."
            )
            logs["erros_acolhedor"] += 1
            continue

        id_acolhedor_db = resultado[0]

        try:
            cursor.execute(
                """
                INSERT INTO acolhimento (nome, idade, numero, data_decisao, id_acolhedor, HouM, situacao)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reg.get("nome"),
                    reg.get("idade"),
                    reg.get("celular"),
                    data_decisao,
                    id_acolhedor_db,
                    reg.get("HouM"),
                    reg.get("situacao"),
                ),
            )
            logs["sucesso"] += 1
        except sqlite3.IntegrityError:
            print(f"LOG: Registro duplicado para '{reg.get('nome')}' na data '{data_decisao}'. Ignorando.")
            logs["duplicado"] = logs.get("duplicado", 0) + 1
        except sqlite3.Error as e:
            print(f"ERRO SQL ao inserir '{reg.get('nome')}': {e}")

    conn.commit()
    conn.close()

    print("\n--- Relatório de Carga ---")
    print(f"Registros carregados com sucesso: {logs['sucesso']}")
    print(f"Registros descartados (dados essenciais faltando): {logs['descartado']}")
    print(f"Registros com erro (acolhedor não encontrado): {logs['erros_acolhedor']}")
    print("--------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script para carregar dados de visitantes de um arquivo JSON para o banco de dados."
    )
    parser.add_argument(
        "--data", required=True, help="Data do arquivo de carga no formato ddmmyy."
    )
    args = parser.parse_args()

    carregar_base_de_dados(args.data)