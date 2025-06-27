import sqlite3
import json
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

def carregar_respostas_para_base(data_param: str):
    """
    Lê o arquivo JSON de acompanhamento e atualiza a base de dados.
    """
    pasta_base = os.getenv('PASTA_BASE')
    if not pasta_base:
        print("Erro: Variável de ambiente PASTA_BASE não está configurada.")
        return

    nome_arquivo = f'acompanhamento_carga_{data_param}.json'
    caminho_arquivo = os.path.join(pasta_base, nome_arquivo)

    if not os.path.exists(caminho_arquivo):
        print(f"Erro: Arquivo '{nome_arquivo}' não encontrado na pasta '{pasta_base}'.")
        return

    print(f"Iniciando carga de atualizações do arquivo: {caminho_arquivo}")

    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        registros_de_update = json.load(f)

    conn = sqlite3.connect('igreja_dados.db')
    cursor = conn.cursor()

    logs = {'sucesso': 0, 'nao_encontrado': 0, 'erros': 0}

    for update in registros_de_update:
        nome = update.get('nome_visitante')
        status = update.get('status_resposta')
        obs = update.get('observacao')

        if not nome or not status:
            logs['erros'] += 1
            print(f"AVISO: Registro inválido no JSON (nome ou status faltando): {update}")
            continue
        
        try:
            # O ideal é atualizar apenas registros que foram notificados e aguardam resposta
            cursor.execute(
                """
                UPDATE acolhimento 
                SET status_contato = ?, observacoes = ? 
                WHERE nome LIKE ? AND status_contato = 'Notificado'
                """,
                (status, obs, f'%{nome}%')
            )
            
            # Verifica se alguma linha foi realmente alterada
            if cursor.rowcount > 0:
                print(f"SUCESSO: Registro de '{nome}' atualizado para '{status}'.")
                logs['sucesso'] += 1
            else:
                print(f"AVISO: Visitante '{nome}' não encontrado com status 'Notificado'. Pode já ter sido atualizado ou não existe.")
                logs['nao_encontrado'] += 1

        except sqlite3.Error as e:
            logs['erros'] += 1
            print(f"ERRO SQL ao atualizar '{nome}': {e}")
            
    conn.commit()
    conn.close()
    
    print("\n--- Relatório de Carga de Acompanhamento ---")
    print(f"Registros atualizados com sucesso: {logs['sucesso']}")
    print(f"Registros não encontrados ou já atualizados: {logs['nao_encontrado']}")
    print(f"Erros de processamento: {logs['erros']}")
    print("---------------------------------------------")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Script para carregar atualizações de acompanhamento no banco de dados.")
    parser.add_argument('--data', required=True, help="Data do arquivo de acompanhamento no formato ddmmyyyy.")
    args = parser.parse_args()
    
    carregar_respostas_para_base(args.data)