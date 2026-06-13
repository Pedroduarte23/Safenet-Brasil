from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO
import sqlite3
import random
import threading
import time

app = Flask(__name__)
app.secret_key = "safenet_brasil_2026"

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)


# =========================
# BANCO
# =========================
def init_db():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS denuncias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        valor TEXT,
        descricao TEXT,
        risco TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================
# EVENTOS SIEM
# =========================
def gerar_eventos():

    eventos = [
        "LOGIN_FAIL",
        "PIX_FRAUD",
        "PORT_SCAN",
        "BRUTE_FORCE",
        "MALWARE"
    ]

    while True:

        evento = {
            "tipo": random.choice(eventos),
            "risco": random.choice(
                ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
            ),
            "ip": f"10.0.0.{random.randint(1,255)}",
            "user": f"user{random.randint(1,50)}"
        }

        socketio.emit("new_event", evento)

        time.sleep(2)


threading.Thread(
    target=gerar_eventos,
    daemon=True
).start()


# =========================
# HOME
# =========================
@app.route("/", methods=["GET", "POST"])
def home():

    print("ENTROU NA HOME")

    denuncias = []

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM denuncias")
    total = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM denuncias WHERE tipo='Telefone'"
    )
    telefones = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM denuncias WHERE tipo='PIX'"
    )
    pix = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM denuncias WHERE tipo='Site'"
    )
    sites = cursor.fetchone()[0]

    if request.method == "POST":

        pesquisa = request.form["pesquisa"]

        cursor.execute("""
        SELECT tipo, valor, descricao, risco
        FROM denuncias
        WHERE valor LIKE ?
        ORDER BY id DESC
        """, (f"%{pesquisa}%",))

        denuncias = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        denuncias=denuncias,
        total=total,
        telefones=telefones,
        pix=pix,
        sites=sites
    )


# =========================
# DENUNCIA
# =========================
@app.route("/denuncia", methods=["GET", "POST"])
def denuncia():

    if request.method == "POST":

        tipo = request.form["tipo"]
        valor = request.form["valor"]
        descricao = request.form["descricao"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO denuncias
        (tipo, valor, descricao, risco)
        VALUES (?, ?, ?, ?)
        """, (
            tipo,
            valor,
            descricao,
            "MEDIUM"
        ))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("denuncia.html")


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    print("ENTROU NO LOGIN")

    if request.method == "POST":

        usuario = request.form["usuario"]
        senha = request.form["senha"]

        if usuario == "admin" and senha == "123456":

            session["admin"] = True

            return redirect("/admin")

        return "Usuário ou senha inválidos."

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================
# ADMIN
# =========================
@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/login")

    return render_template("admin.html")


# =========================
# SOCKET
# =========================
@socketio.on("connect")
def connect():
    print("Cliente conectado")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True
    )