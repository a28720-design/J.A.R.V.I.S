"""
app.py — Servidor Flask + SocketIO.
Faz a ponte entre o frontend web e o núcleo do assistente (jarvis.py).
"""

import threading

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

import jarvis

# ---------------------------------------------------------------------------
# Configuração Flask
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = "jarvis-pap-2025"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ---------------------------------------------------------------------------
# Callback: quando Jarvis fala, envia para o frontend
# ---------------------------------------------------------------------------
def resposta_callback(texto: str) -> None:
    socketio.emit("mensagem", {"emissor": "jarvis", "texto": texto})

jarvis.set_resposta_callback(resposta_callback)

# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------------------------------------------------------------------
# Eventos SocketIO
# ---------------------------------------------------------------------------
@socketio.on("connect")
def on_connect():
    emit("estado", {"estado": "standby"})
    emit("mensagem", {
        "emissor": "jarvis",
        "texto": "Sistema iniciado. Clica em FALAR ou diz «Jarvis» para começar."
    })

@socketio.on("iniciar_escuta")
def on_iniciar_escuta():
    """Cliente pediu para começar a ouvir."""
    def escutar():
        socketio.emit("estado", {"estado": "ouvir"})
        comando = jarvis.ouvir()

        if not comando:
            socketio.emit("estado", {"estado": "standby"})
            socketio.emit("mensagem", {
                "emissor": "sistema",
                "texto": "Não percebi. Tenta outra vez."
            })
            return

        socketio.emit("mensagem", {"emissor": "user", "texto": comando})
        socketio.emit("estado", {"estado": "processar"})
        jarvis.processar_comando(comando)
        socketio.emit("estado", {"estado": "standby"})

    threading.Thread(target=escutar, daemon=True).start()

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import webbrowser, threading

    def abrir_browser():
        import time; time.sleep(1)
        webbrowser.open("http://127.0.0.1:5000")

    threading.Thread(target=abrir_browser, daemon=True).start()
    socketio.run(app, host="127.0.0.1", port=5000, debug=False)
