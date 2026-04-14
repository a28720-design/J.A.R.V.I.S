"""
main.py — Entrada principal do J.A.R.V.I.S.
PyQt6 + QWebEngineView: janela desktop que renderiza HTML/CSS/JS real.
Comunicação bidirecional via QWebChannel.
"""

import json
import os
import sys
import threading
import time

from PyQt6.QtCore    import QObject, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtGui     import QIcon
from PyQt6.QtWebChannel   import QWebChannel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QMainWindow

import jarvis

# ── Caminho absoluto para a pasta ui/ ────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_PATH  = os.path.join(BASE_DIR, "ui", "index.html")


# ─────────────────────────────────────────────────────────────────────────────
class Bridge(QObject):
    """
    Objeto exposto ao JavaScript via QWebChannel.
    JS chama métodos Python → Python responde via runJavaScript().
    """

    # Sinais para thread-safety (emitidos de threads, recebidos na main thread)
    _js_signal = pyqtSignal(str)

    def __init__(self, view: QWebEngineView):
        super().__init__()
        self._view      = view
        self._a_correr  = False
        self._js_signal.connect(self._run_js_main_thread)

    # ── Chamado pelo JS: botão FALAR ──────────────────────────────────────────
    @pyqtSlot()
    def iniciar_escuta(self):
        if self._a_correr:
            return
        self._a_correr = True
        threading.Thread(target=self._escutar_thread, daemon=True).start()

    # ── Chamado pelo JS: fechar app ───────────────────────────────────────────
    @pyqtSlot()
    def fechar(self):
        QApplication.quit()

    # ── Chamado pelo JS: minimizar ────────────────────────────────────────────
    @pyqtSlot()
    def minimizar(self):
        self._view.window().showMinimized()

    # ── Thread de voz ─────────────────────────────────────────────────────────
    def _escutar_thread(self):
        self._js("setEstado('ouvir')")
        comando = jarvis.ouvir()

        if not comando:
            self._js("setEstado('standby')")
            self._js_msg("sistema", "Não percebi. Tenta outra vez.")
            self._a_correr = False
            return

        self._js_msg("user", comando)
        self._js("setEstado('processar')")
        jarvis.processar_comando(comando)
        self._js("setEstado('standby')")
        self._a_correr = False

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _js(self, code: str):
        """Executa JavaScript na main thread (thread-safe via sinal)."""
        self._js_signal.emit(code)

    def _js_msg(self, emissor: str, texto: str):
        e = json.dumps(emissor)
        t = json.dumps(texto)
        self._js(f"addMsg({e}, {t})")

    def _run_js_main_thread(self, code: str):
        self._view.page().runJavaScript(code)

    # ── Callback do jarvis.falar() ────────────────────────────────────────────
    def on_jarvis_fala(self, texto: str):
        self._js_msg("jarvis", texto)


# ─────────────────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S.")
        self.resize(980, 660)
        self.setMinimumSize(820, 560)

        # Remove barra de título nativa (a UI tem a sua própria)
        from PyQt6.QtCore import Qt
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # WebView
        self.view = QWebEngineView(self)
        self.setCentralWidget(self.view)

        # Bridge Python ↔ JS
        self.bridge  = Bridge(self.view)
        self.channel = QWebChannel()
        self.channel.registerObject("api", self.bridge)
        self.view.page().setWebChannel(self.channel)

        # Regista callback do Jarvis
        jarvis.set_resposta_callback(self.bridge.on_jarvis_fala)

        # Carrega a interface HTML
        self.view.load(QUrl.fromLocalFile(UI_PATH))
        self.view.loadFinished.connect(self._on_loaded)

        # Drag da janela (clique na titlebar custom)
        self._drag_pos = None

    def _on_loaded(self):
        """Quando a página carrega, inicia a boas-vindas."""
        def bv():
            time.sleep(0.5)
            jarvis.falar("Olá. Sou o Jarvis. Clica em Falar para começar.")
        threading.Thread(target=bv, daemon=True).start()

    # Drag da janela frameless
    def mousePressEvent(self, e):
        from PyQt6.QtCore import Qt
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint()

    def mouseMoveEvent(self, e):
        from PyQt6.QtCore import Qt
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            delta = e.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = e.globalPosition().toPoint()

    def mouseReleaseEvent(self, e):
        self._drag_pos = None


# ─────────────────────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("J.A.R.V.I.S.")

    win = MainWindow()
    win.show()

    # Centra a janela no ecrã
    screen = app.primaryScreen().geometry()
    win.move(
        (screen.width()  - win.width())  // 2,
        (screen.height() - win.height()) // 2,
    )

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
