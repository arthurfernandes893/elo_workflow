import os
import sys
from dotenv import load_dotenv

load_dotenv(verbose=True)

def main():
    # Define required environment variables
    required_vars = [
        "GEMINI_API_KEY",
        "MODEL",
        "DRIVE_FOLDER_ID",
        "PASTA_BASE",
        "PASTA_JSON",
        "PASTA_CSV",
        "ACOLHEDORES_CSV_PATH",
        "GPS_CSV_PATH",
        "NOME_BANCO_DADOS",
        "PASTA_BACKUP_LOCAL",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GDRIVE_CREDENTIALS"
    ]

    required_dirs = [
        "PASTA_BASE",
        "PASTA_JSON",
        "PASTA_CSV",
        "ACOLHEDORES_CSV_PATH",
        "GPS_CSV_PATH",
        "NOME_BANCO_DADOS",
        "PASTA_BACKUP_LOCAL",
    ]

    # --- 1. Create Data Directory ---
    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"Creating directory: {data_dir}")
        os.makedirs(data_dir)
        for dir in required_dirs:
            if not os.path.isdir(dir) and os.path.exists(dir):
                print(f"Creating directory: {dir}")
                os.makedirs(dir)
    else:
        print(f"Directory already exists: {data_dir}")

    # --- 2. Validate Environment Variables ---
    print("\nChecking for required environment variables...")
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("\nError: The following required environment variables are not set or are empty:")
        for var in missing_vars:
            print(f"- {var}")
        sys.exit(1) # Exit with an error code
    else:
        print("All required environment variables are set.")

    # --- 3. Check for Credential Files ---
    print("\nChecking for credential files...")
    gdrive_creds_path = os.getenv("GDRIVE_CREDENTIALS")
    google_creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # Check for the existence of the files themselves
    if not os.path.isfile(gdrive_creds_path):
        print(f"Error: Google Drive credentials file not found at path: {gdrive_creds_path}")
        sys.exit(1)

    if not os.path.isfile(google_creds_path):
        print(f"Error: Google Application credentials file not found at path: {google_creds_path}")
        sys.exit(1)

    # Check if token.json exists within the same directory as GDrive credentials
    gdrive_dir = os.path.dirname(gdrive_creds_path)
    token_path = os.path.join(gdrive_dir, "token.json")

    if os.path.exists(token_path):
        print("Found 'token.json'. The application appears to be authenticated.")
    else:
        print("Warning: 'token.json' not found. The application may need to go through the OAuth flow on first run.")

    print("\nEnvironment setup check complete.")

if __name__ == "__main__":
    main()
