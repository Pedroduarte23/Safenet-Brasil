import sqlite3

conexao = sqlite3.connect("database.db")
cursor = conexao.cursor()

# adiciona a coluna risco
cursor.execute("ALTER TABLE denuncias ADD COLUMN risco TEXT")

conexao.commit()
conexao.close()

print("Coluna 'risco' adicionada com sucesso!")