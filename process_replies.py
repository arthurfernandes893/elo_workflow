import imaplib
import email
from email.header import decode_header
import google.generativeai as genai
import os
import json
import sqlite3
from dotenv import load_dotenv

load_dotenv()

# Configurações
IMAP_SERVER = "imap.gmail.com"
EMAIL_CONTA = os.getenv("EMAIL_REMETENTE") # A conta que recebe as respostas
SENHA_EMAIL = os.getenv("SENHA_EMAIL")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def processar_respostas():
        pasta_base = os.getenv('PASTA_BASE')
    if not pasta_base:
        print("Erro: Variável de ambiente PASTA_BASE não está configurada.")
        return
    caminho_banco = os.path.join(pasta_base, 'igreja_dados.db')
    conn = sqlite3.connect(caminho_banco)
    cursor = conn.cursor()

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_CONTA, SENHA_EMAIL)
        mail.select("inbox")

        status, messages = mail.search(None, '(UNSEEN)')
        if status != 'OK' or not messages[0]:
            print("Nenhuma resposta nova.")
            return

        for msg_id in messages[0].split():
            _, msg_data = mail.fetch(msg_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            # Pega o e-mail do remetente
            remetente_email, _ = email.utils.parseaddr(msg["From"])

            # Verifica se o remetente é um acolhedor conhecido
            cursor.execute("SELECT id_acolhedor FROM acolhedores WHERE acolhedor_email = ?", (remetente_email,))
            result = cursor.fetchone()
            if not result:
                print(f"Ignorando e-mail de remetente desconhecido: {remetente_email}")
                continue
            
            id_acolhedor_remetente = result[0]
            
            # Extrai o corpo do e-mail
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain": body = part.get_payload(decode=True).decode()
            else:
                body = msg.get_payload(decode=True).decode()

            if not body: continue

            # Usa Gemini para extrair informações
            model = genai.GenerativeModel('gemini-pro')
            prompt = f"""
            Analise o corpo do e-mail abaixo. Para cada visitante mencionado, retorne um objeto JSON com "nome_visitante", "status_resposta" e "observacao".
            Valores possíveis para "status_resposta": "Atendeu e tem interesse", "Atendeu e já tem igreja", "Não atendeu", "Número incorreto", "Ignorado".

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
                for update in updates:
                    nome = update.get("nome_visitante")
                    status = update.get("status_resposta")
                    obs = update.get("observacao")
                    
                    if nome and status:
                        # Atualiza o visitante pelo nome E pelo ID do acolhedor que respondeu
                        cursor.execute(
                            "UPDATE acolhimento SET status_contato = ?, observacoes = ? WHERE nome LIKE ? AND id_acolhedor = ?",
                            (status, obs, f'%{nome}%', id_acolhedor_remetente)
                        )
                        print(f"Atualizado: Visitante '{nome}' por {remetente_email} -> Status: {status}")
                conn.commit()
            except Exception as e:
                print(f"Erro ao processar resposta do Gemini ou atualizar BD: {e}")

    except Exception as e:
        print(f"Erro geral: {e}")
    finally:
        conn.close()
        if 'mail' in locals() and mail.state == 'SELECTED':
            mail.logout()

if __name__ == '__main__':
    processar_respostas()