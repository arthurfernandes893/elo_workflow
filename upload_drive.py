import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Permissões necessárias. Se você mudar isso, delete o arquivo token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']

import os
from dotenv import load_dotenv

load_dotenv()

# --- Configurações ---
NOME_ARQUIVO_LOCAL = 'igreja_dados.db'
PASTA_BASE = os.getenv('PASTA_BASE')
if not PASTA_BASE:
    print("Erro: Variável de ambiente PASTA_BASE não está configurada.")
    exit(1)
CAMINHO_ARQUIVO_DB = os.path.join(PASTA_BASE, NOME_ARQUIVO_LOCAL)
NOME_PASTA_DRIVE = 'AutomacaoIgrejaDB' # A pasta que será criada no seu Drive

def autenticar():
    """Realiza a autenticação com a API do Google Drive."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def upload_arquivo_db():
    """Encontra ou cria a pasta no Drive e faz o upload/update do arquivo do DB."""
    if not os.path.exists(CAMINHO_ARQUIVO_DB):
        print(f"ERRO: Arquivo local '{CAMINHO_ARQUIVO_DB}' não encontrado.")
        return

    creds = autenticar()

    try:
        service = build('drive', 'v3', credentials=creds)

        # 1. Encontrar ou criar a pasta no Google Drive
        response = service.files().list(
            q=f"name='{NOME_PASTA_DRIVE}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive'
        ).execute()
        
        if not response['files']:
            print(f"Pasta '{NOME_PASTA_DRIVE}' não encontrada, criando...")
            folder_metadata = {'name': NOME_PASTA_DRIVE, 'mimeType': 'application/vnd.google-apps.folder'}
            folder = service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder.get('id')
            print(f"Pasta criada com ID: {folder_id}")
        else:
            folder_id = response['files'][0].get('id')
            print(f"Pasta '{NOME_PASTA_DRIVE}' encontrada com ID: {folder_id}")

        # 2. Verificar se o arquivo já existe na pasta para decidir entre criar ou atualizar
        response = service.files().list(
            q=f"name='{NOME_ARQUIVO_LOCAL}' and '{folder_id}' in parents and trashed=false",
            spaces='drive'
        ).execute()
        
        media = MediaFileUpload(CAMINHO_ARQUIVO_DB, mimetype='application/x-sqlite3')
        
        if not response['files']:
            # Criar novo arquivo
            print(f"Fazendo upload de '{NOME_ARQUIVO_LOCAL}' pela primeira vez...")
            file_metadata = {'name': NOME_ARQUIVO_LOCAL, 'parents': [folder_id]}
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        else:
            # Atualizar arquivo existente
            print(f"Atualizando o arquivo '{NOME_ARQUIVO_LOCAL}' no Drive...")
            file_id = response['files'][0].get('id')
            service.files().update(fileId=file_id, media_body=media).execute()
        
        print("\nSUCESSO: Upload/atualização do banco de dados concluído.")

    except HttpError as error:
        print(f'Ocorreu um erro: {error}')

if __name__ == '__main__':
    upload_arquivo_db()