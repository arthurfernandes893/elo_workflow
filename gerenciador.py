import argparse

# Importa as funções principais dos outros scripts.
# Cada script deve ter sua lógica principal dentro de uma função para que possa ser importada.
from elo.services.generate_json import gerar_arquivo_carga
from elo.database.load_database import carregar_base_de_dados
from elo.database.load_acolhedores import carregar_acolhedores
from elo.services.send_emails import enviar_notificacoes_personalizadas


def main():
    """
    Função principal que configura e processa os argumentos da linha de comando.
    """
    # Cria o parser principal
    parser = argparse.ArgumentParser(
        description="Gerenciador da Automação de Acolhimento da Igreja.",
        formatter_class=argparse.RawTextHelpFormatter,  # Melhora a formatação da ajuda
    )

    # Cria um container para os sub-comandos
    subparsers = parser.add_subparsers(
        dest="comando", required=True, help="Comandos disponíveis"
    )

    # --- Comando 1: Gerar JSON ---
    parser_gerar = subparsers.add_parser(
        "gerar_json", help="Gera o arquivo JSON a partir de um arquivo .txt de entrada."
    )
    parser_gerar.add_argument(
        "arquivo_txt",
        help="Caminho para o arquivo .txt de entrada (ex: entrada_de_dados/entrada.txt)",
    )

    # --- Comando 2: Carregar Acolhedores ---
    parser_acolhedores = subparsers.add_parser(
        "carregar_acolhedores",
        help="Carrega a lista de acolhedores a partir de um arquivo .csv.",
    )
    parser_acolhedores.add_argument(
        "arquivo_csv", help="Caminho para o arquivo acolhedores.csv"
    )

    # --- Comando 3: Carregar Acolhimento ---
    parser_acolhimento = subparsers.add_parser(
        "carregar_acolhimento",
        help="Carrega visitantes (acolhimento) a partir de um JSON gerado.",
    )
    parser_acolhimento.add_argument(
        "--data",
        required=True,
        help="Data do arquivo de carga no formato ddmmyy (ex: 260625)",
    )

    # --- Comando 4: Disparar E-mails ---
    parser_emails = subparsers.add_parser(
        "disparar_emails",
        help="Verifica por visitantes pendentes e dispara os e-mails para os acolhedores.",
    )

    # Processa os argumentos fornecidos pelo usuário
    args = parser.parse_args()

    # Chama a função correspondente ao comando escolhido
    print("--- Executando Comando ---")
    if args.comando == "gerar_json":
        gerar_arquivo_carga(args.arquivo_txt)

    elif args.comando == "carregar_acolhedores":
        carregar_acolhedores(args.arquivo_csv)

    elif args.comando == "carregar_acolhimento":
        carregar_base_de_dados(args.data)

    elif args.comando == "disparar_emails":
        print("Iniciando o disparo de e-mails...")
        enviar_notificacoes_personalizadas()

    print("--- Comando Concluído ---")


if __name__ == "__main__":
    main()
