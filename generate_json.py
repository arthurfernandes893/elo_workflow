import google.generativeai as genai
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def gerar_arquivo_carga(caminho_arquivo_txt: Optional[str] = None, dados_entrada_texto: Optional[str] = None):
    """
    Lê dados de um arquivo de texto ou de uma string, envia para o Gemini para estruturação
    e salva o resultado em um arquivo JSON nomeado.
    """
    dados_entrada = None
    if dados_entrada_texto:
        dados_entrada = dados_entrada_texto
    elif caminho_arquivo_txt:
        try:
            with open(caminho_arquivo_txt, "r", encoding="utf-8") as f:
                dados_entrada = f.read()
        except FileNotFoundError:
            print(f"Erro: Arquivo de entrada não encontrado em '{caminho_arquivo_txt}'")
            return
    else:
        print("Erro: Nenhum dado de entrada fornecido (nem arquivo, nem texto).")
        return

    if not dados_entrada:
        print("Erro: Dados de entrada estão vazios.")
        return

    model = genai.GenerativeModel("gemini-2.5-flash")

    # Prompt para atender aos requisitos
    prompt = f"""
    Analise a lista semi-estruturada de pessoas abaixo e converta-a em uma lista de objetos JSON.

    No começo da lista deve estar a data daquela lista. No json gerado deve ser o primeiro campo, de nome "data", a conter essa informação.
    Se não houver uma informação, retorne esse campo definido para uma string vazia: ""
    Em seguida estruture um campo de nome "lista" a partir dos dados fornecidos seguindo as regras abaixo:
    
    Regras para cada objeto:
    1. As chaves devem ser "nome", "idade", "celular", "acolhedor", "plano_de_acao" e "HouM".
    2. Se as informações de "nome" ou "acolhedor" estiverem faltando, o "plano_de_acao" deve ser "Descartar registro por falta de dados essenciais".
    3. Se as informações de "idade" ou "celular" estiverem faltando (mas "nome" e "acolhedor" estiverem presentes), o "plano_de_acao" deve ser "Carregar registro e solicitar dados faltantes ao acolhedor".
    4. Se todos os dados estiverem presentes, o "plano_de_acao" deve ser "Carregar registro normalmente".
    5. O campo "idade" deve ser um número inteiro. Se estiver vazio, use o valor null no JSON.
    6. O campo "HouM" deve ser preenchido com 'H' para homem e 'M' para mulher, com base no nome da pessoa. Se não for possível determinar, deixe em branco.

    Retorne APENAS um objeto json contendo a data e a lista de objetos JSON, nada mais.

    Dados de Entrada:
    ---
    {dados_entrada}
    ---
    """

    print("Enviando dados para o Gemini para estruturação...")
    try:
        response = model.generate_content(prompt)
        if not response or not hasattr(response, "text"):
            raise ValueError("Resposta inválida ou vazia recebida do Gemini.")
    except Exception as e:
        print(f"Erro ao enviar dados para o Gemini ou ao receber a resposta: {e}")
        return

    print("Análise do Gemini completa.")

    try:
        # Limpa a resposta do Gemini para garantir que é um JSON válido
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        dados_estruturados = json.loads(json_text)

        # Extrai a data do JSON estruturado
        try:
            data_arquivo = datetime.strptime(dados_estruturados["data"], "%d/%m/%Y")  # Valida o formato da data
        except (IndexError, ValueError):
            raise ValueError("a data informada no arquivo não esta no formato dd/mm/yyyy.")

        # Define o nome do arquivo de saída usando a data extraída
        nome_arquivo_saida = f"EloCargaDados_{data_arquivo.strftime('%d%m%Y')}.json"

        # Pega o caminho da pasta base a partir da variável de ambiente
        pasta_base = os.getenv("PASTA_BASE")
        if not pasta_base:
            raise ValueError("Variável de ambiente PASTA_BASE não definida. Impossível completar o processamento")

        caminho_completo_saida = os.path.join(pasta_base, nome_arquivo_saida)

        # Salva o arquivo JSON
        with open(caminho_completo_saida, "w", encoding="utf-8") as f:
            json.dump(dados_estruturados, f, indent=4, ensure_ascii=False)


        print(f"Arquivo '{nome_arquivo_saida}' gerado com sucesso em '{pasta_base}'.")

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Erro ao processar a resposta do Gemini ou salvar o arquivo: {e}")
        print("Resposta recebida do Gemini:")
        print(response.text)


if __name__ == "__main__":
    # Exemplo de como chamar o script.
    # Pode ser melhorado com argparse para receber o caminho do arquivo como argumento.
    arquivo_de_entrada = "./entrada_dados/adocao-270625.txt"
    gerar_arquivo_carga(caminho_arquivo_txt=arquivo_de_entrada)
