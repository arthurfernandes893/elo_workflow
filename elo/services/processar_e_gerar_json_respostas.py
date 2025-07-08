import imaplib
import email
from email.header import decode_header
import google.generativeai as genai
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configurações
IMAP_SERVER = "imap.gmail.com"
EMAIL_CONTA = os.getenv("EMAIL_REMETENTE")  # A conta que recebe as respostas
SENHA_EMAIL = os.getenv("SENHA_EMAIL")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def gerar_json_respostas():
    """
    Lê e-mails não lidos, estrutura as respostas com o Gemini e salva em um arquivo JSON.
    Marca os e-mails como lidos após o processamento para não serem lidos novamente.
    """
    print("Conectando à caixa de e-mail para verificar respostas...")
    respostas_consolidadas = []

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_CONTA, SENHA_EMAIL)
        mail.select("inbox")

        # Procura por e-mails não lidos
        status, messages = mail.search(None, "(UNSEEN)")
        if status != "OK" or not messages[0]:
            print("Nenhuma resposta nova para processar.")
            return

        message_ids = messages[0].split()
        print(f"Encontrados {len(message_ids)} novos e-mails.")

        model = genai.GenerativeModel("gemini-pro")

        for msg_id in message_ids:
            # Busca o e-mail
            _, msg_data = mail.fetch(msg_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            # Extrai o corpo do e-mail
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(
                            "utf-8", errors="ignore"
                        )
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

            if not body.strip():
                continue

            # Prompt para o Gemini
            prompt = f"""
            Analise o corpo do e-mail de resposta abaixo e, para cada visitante mencionado, extraia as informações em um objeto JSON.
            As chaves devem ser "nome_visitante", "status_resposta" e "observacao".

            Os possíveis valores para "status_resposta" são:
            - "Atendeu e tem interesse"
            - "Atendeu e já tem igreja"
            - "Não atendeu"
            - "Número incorreto"

            E-mail:
            ---
            {body}
            ---

            Retorne APENAS uma lista de objetos JSON.
            """

            response = model.generate_content(prompt)
            json_text = response.text.strip().replace("```json", "").replace("```", "")

            try:
                updates = json.loads(json_text)
                respostas_consolidadas.extend(updates)
                print(
                    f"E-mail processado com sucesso. {len(updates)} atualização(ões) extraída(s)."
                )
                # MARCA O E-MAIL COMO LIDO para não processar de novo
                mail.store(msg_id, "+FLAGS", "\\Seen")
            except json.JSONDecodeError:
                print(
                    f"AVISO: Gemini não retornou um JSON válido para um dos e-mails. E-mail será mantido como não lido."
                )
                print("Resposta recebida:", json_text)

    except Exception as e:
        print(f"Ocorreu um erro durante o processamento de e-mails: {e}")
    finally:
        if "mail" in locals() and mail.state == "SELECTED":
            mail.logout()

    # Salva o arquivo JSON se houver respostas consolidadas
    if respostas_consolidadas:
        pasta_base = os.getenv("PASTA_BASE")
        if not pasta_base:
            print("ERRO CRÍTICO: Variável de ambiente PASTA_BASE não definida.")
            return

        data_hoje = datetime.now().strftime("%d%m%Y")
        nome_arquivo = f"acompanhamento_carga_{data_hoje}.json"
        caminho_completo = os.path.join(pasta_base, nome_arquivo)

        with open(caminho_completo, "w", encoding="utf-8") as f:
            json.dump(respostas_consolidadas, f, indent=4, ensure_ascii=False)

        print(f"\nArquivo '{nome_arquivo}' gerado com sucesso em '{pasta_base}'.")
    else:
        print("Nenhuma resposta válida foi extraída para gerar o arquivo.")


if __name__ == "__main__":
    gerar_json_respostas()
