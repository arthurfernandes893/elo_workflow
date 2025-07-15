import os
import dotenv
import sqlite3
import datetime
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import matplotlib.pyplot as plt
import tempfile
import ast

def verificar_variaveis_ambiente():
    """Verifica se todas as variáveis de ambiente necessárias estão configuradas."""
    variaveis_necessarias = ["PASTA_BASE", "NOME_BANCO_DADOS", "EMAIL_USER", "EMAIL_PASS", "MAIL_LIST"]
    for var in variaveis_necessarias:
        if not os.getenv(var):
            print(f"ERRO CRÍTICO: Variável de ambiente '{var}' não configurada.")
            return False
    return True


dotenv.load_dotenv(verbose=True)

def getPendingAllocations(start_date, end_date) -> pd.DataFrame:
    if not verificar_variaveis_ambiente():
        return

    pasta_base = os.getenv("PASTA_BASE")
    nome_db = os.getenv("NOME_BANCO_DADOS")
    caminho_banco = os.path.join(pasta_base, nome_db)
    conn = None

    if not os.path.exists(caminho_banco):
        print(f"Erro: Arquivo do banco de dados nao encontrado")
        return
    
    try:
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        print(f"Iniciando Query dos Acolhimentos Pendentes entre {start_date} e {end_date}")
        
        query = (f"SELECT acc.data_decisao, acc.evento, acc.HouM, acc.status_contato, "
         "a.acolhedor_nome, g.nome_lider_gps "
         "FROM acolhimento AS acc "
         "LEFT JOIN acolhedores a ON a.id_acolhedor = acc.id_acolhedor "
         "LEFT JOIN gps AS g ON g.id_gps = a.id_gps "
         "WHERE acc.status_contato = 'Pendente' "
         f"AND acc.data_decisao >= '{start_date}' OR acc.data_decisao <='{end_date}';")

        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        print(f"\n--- ERRO INESPERADO DURANTE A LEITURA DO BANCO DE DADOS ---")
        print(f"Ocorreu um erro: {e}")
        if conn:
            conn.rollback()

    finally:
        if conn:
            conn.close()


def getCountPendingAllocations(start_date, end_date):
    df = getPendingAllocations(start_date, end_date)
    if df is None:
        return None

    pending_counts = df.groupby('acolhedor_nome').size().reset_index(name='acolhimentos_pendentes')
    return pending_counts

def plot_pending_allocations_as_jpeg(start_date, end_date):
    """
    Generates a JPEG image of a table with conditional formatting for pending allocations
    and saves it to a temporary file.
    """
    df = getCountPendingAllocations(start_date, end_date)
    if df is None or df.empty:
        print("Não há dados de alocações pendentes para gerar o relatório.")
        return None

    def get_color(val):
        if val <= 2:
            return 'green'
        elif val == 3:
            return 'yellow'
        else:
            return 'red'

    fig, ax = plt.subplots(figsize=(8, len(df) * 0.5))  # Adjust size based on number of rows
    ax.axis('tight')
    ax.axis('off')

    the_table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center')
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(10)
    the_table.scale(1.2, 1.2)

    for i, val in enumerate(df['acolhimentos_pendentes']):
        color = get_color(val)
        the_table[(i + 1, 1)].set_facecolor(color)

    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmpfile:
            output_path = tmpfile.name
            plt.savefig(output_path, bbox_inches='tight', dpi=150)
            print(f"Relatório temporário de alocações pendentes salvo em: {output_path}")
            return output_path
    except Exception as e:
        print(f"Erro ao salvar o arquivo JPEG temporário: {e}")
        return None

def send_allocation_email(start_date, end_date):
    """
    Sends an email with the pending allocations report (as a JPEG image) to a list of recipients.
    """
    if not verificar_variaveis_ambiente():
        return

    attachment_path = plot_pending_allocations_as_jpeg(start_date, end_date)
    if not attachment_path:
        print("Não foi possível gerar o anexo. E-mail não enviado.")
        return

    try:
        from_email = os.getenv("EMAIL_USER")
        password = os.getenv("EMAIL_PASS")
        mail_list_str = os.getenv("MAIL_LIST")
        
        if not mail_list_str:
            print("ERRO: A variável de ambiente MAIL_LIST não está definida.")
            return
            
        to_emails = ast.literal_eval(mail_list_str)

        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = ", ".join(to_emails)
        msg['Subject'] = f"Alocação dos Acolhedores - {datetime.date.today().strftime("%d/%m/%Y")}"

        body = "Segue em anexo a alocação dos acolhedores nos dias de congresso.\n Atenção para não alocar acolhedores no vermelho\n\nAtenciosamente, Ministerio ELO"
        msg.attach(MIMEText(body, 'plain'))

        with open(attachment_path, 'rb') as fp:
            img = MIMEImage(fp.read())
        img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
        msg.attach(img)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_emails, text)
        server.quit()
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar o e-mail: {e}")
    finally:
        if attachment_path and os.path.exists(attachment_path):
            os.remove(attachment_path)
            print(f"Arquivo temporário removido: {attachment_path}")

'''
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process pending allocations.")
    parser.add_argument('--plot', action='store_true', help='Generate a JPEG plot of pending allocations.')
    parser.add_argument('--send-email', action='store_true', help='Send the report to the list of email addresses defined in the .env file.')
    
    args = parser.parse_args()

    if args.plot:
        # Note: when using --plot directly, the temp file is not automatically cleaned up.
        # This is intended for debugging or viewing the plot locally.
        plot_pending_allocations_as_jpeg()
    elif args.send_email:
        send_allocation_email()
    else:
        print(getCountPendingAllocations())
'''