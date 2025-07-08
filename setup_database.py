import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

NOME_BANCO_DADOS = "igreja_dados.db"
PASTA_BASE = os.getenv("PASTA_BASE")

if not PASTA_BASE:
    print("Erro: Variável de ambiente PASTA_BASE não está configurada.")
    exit(1)

caminho_banco = os.path.join(PASTA_BASE, NOME_BANCO_DADOS)

conn = sqlite3.connect(caminho_banco)
cursor = conn.cursor()

# Habilita o suporte a chaves estrangeiras no SQLite
cursor.execute("PRAGMA foreign_keys = ON;")

# 1. Tabela 'gps'
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS gps (
    id_gps INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_lider_gps VARCHAR(45) NOT NULL UNIQUE
);
"""
)

# 2. Tabela 'acolhedores'
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS acolhedores (
    id_acolhedor INTEGER PRIMARY KEY AUTOINCREMENT,
    acolhedor_nome VARCHAR(45) NOT NULL,
    acolhedor_email VARCHAR(45) NOT NULL UNIQUE,
    id_gps INTEGER,
    FOREIGN KEY (id_gps) REFERENCES gps(id_gps)
);
"""
)

# 3. Tabela 'acolhimento'
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS acolhimento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(70) NOT NULL,
    idade INTEGER,
    numero VARCHAR(45),
    decisao VARCHAR(45),
    data_decisao DATETIME NOT NULL,
    data_carga DATETIME DEFAULT CURRENT_TIMESTAMP,
    status_contato VARCHAR(45) DEFAULT 'Pendente',
    observacoes VARCHAR(255),
    id_acolhedor INTEGER,
    HouM VARCHAR(1),
    FOREIGN KEY (id_acolhedor) REFERENCES acolhedores(id_acolhedor),
    UNIQUE(nome, data_decisao)
);
"""
)

print("Banco de dados e tabelas verificados/criados com sucesso.")

# --- Povoamento Inicial (Exemplo) ---
# Você precisa ter pelo menos um grupo e um acolhedor para o sistema funcionar.
# Execute esta parte apenas uma vez ou quando precisar adicionar mais membros.
try:
    cursor.execute(
        "INSERT INTO gps (nome_lider_gps) VALUES ('Líder Exemplo 1'), ('Líder Exemplo 2');"
    )
    print("Grupos de exemplo inseridos.")
except sqlite3.IntegrityError:
    print("Grupos de exemplo já existem.")

try:
    cursor.execute(
        """
    INSERT INTO acolhedores (acolhedor_nome, acolhedor_email, id_gps) VALUES 
        ('João Acolhedor', 'joao.acolhedor@seuemail.com', 1),
        ('Maria Acolhedora', 'maria.acolhedora@seuemail.com', 1),
        ('Pedro Acolhedor', 'pedro.acolhedor@seuemail.com', 2);
    """
    )
    print("Acolhedores de exemplo inseridos.")
except sqlite3.IntegrityError:
    print("Acolhedores de exemplo já existem.")


conn.commit()
conn.close()