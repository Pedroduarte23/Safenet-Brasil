from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO
import sqlite3
import random
import time
import threading

# =========================
# APP CONFIG
# =========================
app = Flask(__name__)
app.secret_key = "safenet_brasil_2026"

socketio = SocketIO(app, cors_allowed_origins="*")


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
# SIEM STREAM (REAL TIME)
# =========================
def gerar_eventos():

    eventos = ["LOGIN_FAIL", "PIX_FRAUD", "PORT_SCAN", "BRUTE_FORCE", "MALWARE"]

    while True:

        event = {
            "tipo": random.choice(eventos),
            "risco": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "ip": f"10.0.0.{random.randint(1,255)}",
            "user": f"user{random.randint(1,50)}"
        }

        # salva no banco
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO denuncias (tipo, valor, descricao, risco)
        VALUES (?, ?, ?, ?)
        """, (
            event["tipo"],
            event["ip"],
            f"Evento automático {event['tipo']}",
            event["risco"]
        ))

        conn.commit()
        conn.close()

        # envia para dashboard em tempo real
        socketio.emit("new_event", event)

        time.sleep(2)


threading.Thread(target=gerar_eventos, daemon=True).start()


# =========================
# HOME
# =========================
@app.route("/")
def home():
    return redirect("/admin")


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        user = request.form["usuario"]
        password = request.form["senha"]

        if user == "admin" and password == "123456":
            session["admin"] = True
            return redirect("/admin")

        return "Login inválido"

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================
# ADMIN DASHBOARD
# =========================
@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, tipo, valor, descricao, risco
    FROM denuncias
    ORDER BY id DESC
    """)

    denuncias = cursor.fetchall()

    # métricas SOC
    low = medium = high = critical = 0

    for d in denuncias:
        r = d[4]

        if r == "CRITICAL":
            critical += 1
        elif r == "HIGH":
            high += 1
        elif r == "MEDIUM":
            medium += 1
        else:
            low += 1

    conn.close()

    return render_template(
        "admin.html",
        denuncias=denuncias,
        low=low,
        medium=medium,
        high=high,
        critical=critical
    )


# =========================
# SOCKET CONNECT
# =========================
@socketio.on("connect")
def connect():
    print("Cliente conectado ao SOC realtime")


# =========================
# RUN (RENDER READY)
# =========================
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)