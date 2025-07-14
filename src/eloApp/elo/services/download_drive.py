import os
import io
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

# Reutilizando a função de autenticação e configurações
from .auth import autenticar
from .upload_drive import (
    NOME_ARQUIVO_LOCAL,
    NOME_PASTA_DRIVE,
    CAMINHO_ARQUIVO_DB,
)

from dotenv import load_dotenv

load_dotenv()

PASTA_BACKUP_LOCAL = os.getenv("PASTA_BACKUP_LOCAL")

if not PASTA_BACKUP_LOCAL:
    print("Erro: Variável de ambiente PASTA_BACKUP_LOCAL não está configurada.")
    exit(1)


def download_arquivo_db():
    """Encontra o arquivo do DB no Drive e o baixa, fazendo backup da versão antiga."""
    creds = autenticar()

    try:
        service = build("drive", "v3", credentials=creds)

        # 1. Encontrar a pasta e o arquivo no Google Drive
        response_folder = (
            service.files()
            .list(q=f"name='{NOME_PASTA_DRIVE}' and trashed=false", spaces="drive")
            .execute()
        )
        if not response_folder["files"]:
            print(f"ERRO: Pasta '{NOME_PASTA_DRIVE}' não encontrada no Google Drive.")
            return
        folder_id = response_folder["files"][0].get("id")

        response_file = (
            service.files()
            .list(
                q=f"name='{NOME_ARQUIVO_LOCAL}' and '{folder_id}' in parents and trashed=false",
                spaces="drive",
            )
            .execute()
        )
        if not response_file["files"]:
            print(
                f"ERRO: Arquivo '{NOME_ARQUIVO_LOCAL}' não encontrado na pasta do Drive."
            )
            return
        file_id = response_file["files"][0].get("id")
        print(f"Arquivo '{NOME_ARQUIVO_LOCAL}' encontrado no Drive (ID: {file_id}).")

        # 2. Fazer backup do arquivo local antigo, se existir
        if os.path.exists(CAMINHO_ARQUIVO_DB):
            print(f"Arquivo local '{CAMINHO_ARQUIVO_DB}' encontrado. Fazendo backup...")
            # Garante que a pasta de backup exista
            os.makedirs(PASTA_BACKUP_LOCAL, exist_ok=True)
            # Cria um nome de backup com data e hora
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(
                PASTA_BACKUP_LOCAL, f"{NOME_ARQUIVO_LOCAL}.bak_{timestamp}"
            )
            os.rename(CAMINHO_ARQUIVO_DB, backup_path)
            print(f"Backup criado em: {backup_path}")

        # 3. Baixar o novo arquivo
        print("Baixando a versão mais recente do banco de dados...")
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")

        # Salva o conteúdo baixado no arquivo local
        with open(CAMINHO_ARQUIVO_DB, "wb") as f:
            f.write(fh.getvalue())

        print(f"\nSUCESSO: '{CAMINHO_ARQUIVO_DB}' baixado e atualizado.")

    except HttpError as error:
        print(f"Ocorreu um erro: {error}")


if __name__ == "__main__":
    download_arquivo_db()
