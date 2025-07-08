import smtplib
import sqlite3
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()

def enviar_notificacoes_personalizadas():
    pasta_base = os.getenv('PASTA_BASE')
    if not pasta_base:
        print("Erro: Variável de ambiente PASTA_BASE não está configurada.")
        return
    caminho_banco = os.path.join(pasta_base, 'igreja_dados.db')
    conn = sqlite3.connect(caminho_banco)
    cursor = conn.cursor()

    # Encontra acolhedores que têm visitantes pendentes
    query = """
    SELECT DISTINCT a.id_acolhedor, ac.acolhedor_nome, ac.acolhedor_email
    FROM acolhimento a
    JOIN acolhedores ac ON a.id_acolhedor = ac.id_acolhedor
    WHERE a.status_contato = 'Pendente'
    """
    acolhedores_a_notificar = pd.read_sql_query(query, conn)

    if acolhedores_a_notificar.empty:
        print("Nenhum acolhedor com visitantes pendentes.")
        conn.close()
        return

    remetente = os.getenv("EMAIL_REMETENTE")
    senha = os.getenv("SENHA_EMAIL")

    for _, acolhedor in acolhedores_a_notificar.iterrows():
        id_acolhedor = acolhedor['id_acolhedor']
        nome_acolhedor = acolhedor['acolhedor_nome']
        email_acolhedor = acolhedor['acolhedor_email']

        # Pega a lista de visitantes para este acolhedor específico
        df_visitantes = pd.read_sql_query(
            f"SELECT nome, idade, numero, decisao FROM acolhimento WHERE id_acolhedor = {id_acolhedor} AND status_contato = 'Pendente'",
            conn
        )

        if df_visitantes.empty:
            continue

        # Monta e-mail personalizado
        message = MIMEMultipart("alternative")
        message["Subject"] = "Você tem novos visitantes para acolher!"
        message["From"] = remetente
        message["To"] = email_acolhedor

        html_body = f"""
        <html><body>
            <p>Olá {nome_acolhedor},</p>
            <p>Estes são os novos visitantes atribuídos a você para contato:</p>
            {df_visitantes.to_html(index=False, justify='left')}
            <p>Por favor, responda a este e-mail informando o resultado do contato.</p>
        </body></html>
        """
        message.attach(MIMEText(html_body, "html"))

        try:
            # Envia o email
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(remetente, senha)
                server.sendmail(remetente, email_acolhedor, message.as_string())

            print(f"E-mail enviado com sucesso para {nome_acolhedor} ({email_acolhedor}).")

            # Atualiza o status para 'Notificado' para evitar reenvio
            ids_para_atualizar = pd.read_sql_query(f"SELECT id FROM acolhimento WHERE id_acolhedor = {id_acolhedor} AND status_contato = 'Pendente'", conn)['id'].tolist()
            cursor.execute(f"UPDATE acolhimento SET status_contato = 'Notificado' WHERE id IN ({','.join('?' for _ in ids_para_atualizar)})", ids_para_atualizar)
            conn.commit()

        except Exception as e:
            print(f"Falha ao enviar e-mail para {nome_acolhedor}: {e}")

    conn.close()

if __name__ == '__main__':
    enviar_notificacoes_personalizadas()