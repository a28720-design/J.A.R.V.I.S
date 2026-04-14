import math
import threading
import tkinter as tk
from tkinter import font as tkfont

import jarvis

# ---------------------------------------------------------------------------
# Paleta de cores
# ---------------------------------------------------------------------------
BG        = "#050d1a"
BG2       = "#0a1628"
ACCENT    = "#00b4d8"
ACCENT2   = "#0077b6"
ACCENT_DIM = "#003d52"
TEXT      = "#e0f7ff"
TEXT_DIM  = "#3a6a7e"
RED       = "#ff4d6d"
GREEN     = "#00f5a0"

# ---------------------------------------------------------------------------
# Classe principal da interface
# ---------------------------------------------------------------------------
class JarvisUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("J.A.R.V.I.S.")
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.overrideredirect(False)

        # Estado
        self.estado = "STANDBY"   # STANDBY | A OUVIR | A PROCESSAR
        self._anim_angle = 0.0
        self._anim_pulse = 0.0
        self._anim_dir   = 1
        self._correndo   = False

        self._build_ui()
        self._animar()

        # Redireciona o falar() do jarvis para a interface
        jarvis.falar = self._falar_ui

    # -----------------------------------------------------------------------
    # Construção da UI
    # -----------------------------------------------------------------------
    def _build_ui(self) -> None:
        # ── Barra de título personalizada ──────────────────────────────────
        barra = tk.Frame(self.root, bg=BG2, height=40)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        tk.Label(
            barra, text="J.A.R.V.I.S.", bg=BG2, fg=ACCENT,
            font=("Courier New", 13, "bold"), padx=16
        ).pack(side="left", pady=8)

        tk.Button(
            barra, text="✕", bg=BG2, fg=TEXT_DIM, bd=0,
            activebackground=RED, activeforeground="white",
            font=("Courier New", 12), padx=10,
            command=self.root.destroy
        ).pack(side="right")

        # Arrastar janela
        barra.bind("<ButtonPress-1>",   self._drag_start)
        barra.bind("<B1-Motion>",       self._drag_move)

        # ── Canvas de animação ──────────────────────────────────────────────
        self.canvas = tk.Canvas(
            self.root, width=700, height=220,
            bg=BG, highlightthickness=0
        )
        self.canvas.pack()

        # ── Status ─────────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="● STANDBY")
        tk.Label(
            self.root, textvariable=self.status_var,
            bg=BG, fg=TEXT_DIM, font=("Courier New", 11, "bold")
        ).pack(pady=(0, 8))

        # ── Separador ──────────────────────────────────────────────────────
        tk.Frame(self.root, bg=ACCENT_DIM, height=1).pack(fill="x", padx=30)

        # ── Histórico de conversa ───────────────────────────────────────────
        frame_log = tk.Frame(self.root, bg=BG2, padx=4, pady=4)
        frame_log.pack(fill="both", expand=True, padx=30, pady=10)

        self.log = tk.Text(
            frame_log, bg=BG2, fg=TEXT, insertbackground=ACCENT,
            font=("Courier New", 10), bd=0, wrap="word",
            state="disabled", padx=10, pady=8
        )
        scroll = tk.Scrollbar(frame_log, command=self.log.yview, bg=BG2)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log.pack(fill="both", expand=True)

        # Tags de cor por emissor
        self.log.tag_config("jarvis", foreground=ACCENT)
        self.log.tag_config("user",   foreground=GREEN)
        self.log.tag_config("erro",   foreground=RED)

        # ── Botão microfone ─────────────────────────────────────────────────
        self.btn = tk.Button(
            self.root, text="🎤  FALAR",
            bg=ACCENT2, fg="white", activebackground=ACCENT,
            activeforeground="white", bd=0,
            font=("Courier New", 12, "bold"),
            padx=24, pady=10, cursor="hand2",
            command=self._iniciar_escuta
        )
        self.btn.pack(pady=(0, 20))

        # Mensagem inicial
        self._log_msg("JARVIS", "Sistema iniciado. Clica em FALAR ou diz «jarvis».")

    # -----------------------------------------------------------------------
    # Arrastar janela
    # -----------------------------------------------------------------------
    def _drag_start(self, e):
        self._drag_x = e.x
        self._drag_y = e.y

    def _drag_move(self, e):
        dx = e.x - self._drag_x
        dy = e.y - self._drag_y
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    # -----------------------------------------------------------------------
    # Log de mensagens
    # -----------------------------------------------------------------------
    def _log_msg(self, emissor: str, texto: str) -> None:
        self.log.configure(state="normal")
        if emissor == "JARVIS":
            self.log.insert("end", f"JARVIS: ", "jarvis")
            self.log.insert("end", f"{texto}\n")
        elif emissor == "TU":
            self.log.insert("end", f"Tu: ", "user")
            self.log.insert("end", f"{texto}\n")
        else:
            self.log.insert("end", f"{texto}\n", "erro")
        self.log.configure(state="disabled")
        self.log.see("end")

    # -----------------------------------------------------------------------
    # falar() substituído — fala E escreve no log
    # -----------------------------------------------------------------------
    def _falar_ui(self, texto: str) -> None:
        self.root.after(0, lambda: self._log_msg("JARVIS", texto))
        # Usa o motor de voz original (acede ao engine diretamente)
        print(f"JARVIS: {texto}")
        jarvis.engine.say(texto)
        jarvis.engine.runAndWait()

    # -----------------------------------------------------------------------
    # Escuta em thread separada
    # -----------------------------------------------------------------------
    def _iniciar_escuta(self) -> None:
        if self._correndo:
            return
        self._correndo = True
        threading.Thread(target=self._escutar_thread, daemon=True).start()

    def _escutar_thread(self) -> None:
        self._set_estado("A OUVIR")
        self.root.after(0, lambda: self.btn.configure(state="disabled"))

        comando = jarvis.ouvir()

        if comando:
            self.root.after(0, lambda: self._log_msg("TU", comando))
            self._set_estado("A PROCESSAR")
            jarvis.processar_comando(comando)
        else:
            self.root.after(0, lambda: self._log_msg("ERRO", "Não percebi. Tenta outra vez."))

        self._set_estado("STANDBY")
        self.root.after(0, lambda: self.btn.configure(state="normal"))
        self._correndo = False

    def _set_estado(self, estado: str) -> None:
        self.estado = estado
        cores = {"STANDBY": TEXT_DIM, "A OUVIR": GREEN, "A PROCESSAR": ACCENT}
        cor = cores.get(estado, TEXT_DIM)
        self.root.after(0, lambda: self.status_var.set(f"● {estado}"))
        self.root.after(0, lambda: self.root.nametowidget(
            self.root.children.get(list(self.root.children)[-2], "")
        ))
        # Atualiza cor do label de estado diretamente
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Label) and "●" in str(widget.cget("textvariable")):
                widget.configure(fg=cor)
                break

    # -----------------------------------------------------------------------
    # Animação do canvas
    # -----------------------------------------------------------------------
    def _animar(self) -> None:
        self.canvas.delete("all")
        cx, cy = 350, 110

        # Anel exterior rotativo (só visível quando A OUVIR / A PROCESSAR)
        if self.estado != "STANDBY":
            for i in range(12):
                ang = math.radians(self._anim_angle + i * 30)
                r1, r2 = 85, 95
                x1 = cx + r1 * math.cos(ang)
                y1 = cy + r1 * math.sin(ang)
                x2 = cx + r2 * math.cos(ang)
                y2 = cy + r2 * math.sin(ang)
                alpha = int(255 * (i / 12))
                cor = f"#{alpha:02x}{min(alpha+100,255):02x}ff" if self.estado == "A OUVIR" \
                      else f"#00{alpha:02x}{min(alpha+100,255):02x}"
                self.canvas.create_line(x1, y1, x2, y2, fill=cor, width=2)
            self._anim_angle = (self._anim_angle + 3) % 360

        # Anéis estáticos de fundo
        for r, op in [(75, "#0a2a3a"), (58, "#0d3347"), (42, "#102e42")]:
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline=ACCENT_DIM, width=1)

        # Círculo central pulsante
        self._anim_pulse += 0.06 * self._anim_dir
        if self._anim_pulse >= 1.0:
            self._anim_dir = -1
        elif self._anim_pulse <= 0.0:
            self._anim_dir = 1

        raio_base = 28
        raio = raio_base + (4 * self._anim_pulse if self.estado != "STANDBY" else 0)

        cor_centro = GREEN if self.estado == "A OUVIR" \
                     else ACCENT if self.estado == "A PROCESSAR" \
                     else ACCENT2

        self.canvas.create_oval(
            cx-raio, cy-raio, cx+raio, cy+raio,
            fill=cor_centro, outline=ACCENT, width=2
        )

        # Ícone microfone simples no centro
        self.canvas.create_rectangle(cx-7, cy-14, cx+7, cy+6,  fill=BG, outline="")
        self.canvas.create_oval(cx-7, cy-2,  cx+7, cy+10, fill=BG, outline="")
        self.canvas.create_line(cx, cy+10, cx, cy+18, fill=TEXT_DIM, width=2)
        self.canvas.create_line(cx-8, cy+18, cx+8, cy+18, fill=TEXT_DIM, width=2)

        # Texto do estado abaixo do círculo (pequeno)
        self.canvas.create_text(
            cx, cy + 50, text=self.estado,
            fill=TEXT_DIM, font=("Courier New", 8)
        )

        self.root.after(40, self._animar)  # ~25 fps


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    root = tk.Tk()
    app  = JarvisUI(root)

    # Mensagem de boas-vindas ao arrancar
    def boas_vindas():
        jarvis.falar("Olá. Sou o Jarvis. Clica em Falar para começar.")
    threading.Thread(target=boas_vindas, daemon=True).start()

    root.mainloop()


if __name__ == "__main__":
    main()
