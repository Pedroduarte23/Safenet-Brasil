import sqlite3

conexao = sqlite3.connect("database.db")

cursor = conexao.cursor()

cursor.execute("""
CREATE TABLE denuncias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    valor TEXT NOT NULL,
    descricao TEXT NOT NULL,
    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conexao.commit()
conexao.close()

print("Banco criado com sucesso!")