"""
interface.py — Desktop app do J.A.R.V.I.S.
Construída com CustomTkinter para um visual moderno e profissional.
"""

import math
import threading
import tkinter as tk
import time

import customtkinter as ctk

import jarvis

# ── Tema global ──────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Paleta de cores ──────────────────────────────────────────────────────────
BG          = "#050d1a"
BG2         = "#0a1628"
BG3         = "#0d1f35"
ACCENT      = "#00b4ff"
ACCENT2     = "#0077b6"
ACCENT_DIM  = "#0a2a3a"
GREEN       = "#00f5a0"
GREEN_DIM   = "#003d2a"
RED         = "#ff4d6d"
TEXT        = "#e0f7ff"
TEXT_DIM    = "#3a6a7e"
GLASS_BG    = "#0c1e33"


# ─────────────────────────────────────────────────────────────────────────────
class OrbCanvas(tk.Canvas):
    """Canvas com animação do orb central (anéis + pulso + ondas)."""

    def __init__(self, master, size=260, **kwargs):
        super().__init__(
            master, width=size, height=size,
            bg=BG, highlightthickness=0, **kwargs
        )
        self.size   = size
        self.cx     = size // 2
        self.cy     = size // 2
        self.estado = "standby"

        # Variáveis de animação
        self._angle     = 0.0
        self._pulse     = 0.0
        self._pulse_dir = 1
        self._wave_t    = 0.0
        self._running   = True

        self._tick()

    def set_estado(self, estado: str):
        self.estado = estado

    def _tick(self):
        if not self._running:
            return
        self.delete("all")
        cx, cy = self.cx, self.cy

        # ── Grelha de fundo (estilo HUD) ─────────────────────────────────
        for i in range(0, self.size, 20):
            self.create_line(i, 0, i, self.size, fill="#0a1e30", width=1)
            self.create_line(0, i, self.size, i,   fill="#0a1e30", width=1)

        # ── Anéis estáticos ───────────────────────────────────────────────
        ring_colors = ["#0a2a3a", "#0d3347", "#102e42"]
        for r, col in zip([105, 85, 68], ring_colors):
            self.create_oval(cx-r, cy-r, cx+r, cy+r, outline=col, width=1)

        # ── Anel rotativo (visível quando ativo) ──────────────────────────
        if self.estado != "standby":
            arc_color = GREEN if self.estado == "ouvir" else ACCENT
            self.create_arc(
                cx-105, cy-105, cx+105, cy+105,
                start=self._angle, extent=240,
                outline=arc_color, width=2, style="arc"
            )
            self.create_arc(
                cx-105, cy-105, cx+105, cy+105,
                start=self._angle + 180, extent=60,
                outline=arc_color, width=1, style="arc"
            )
            self._angle = (self._angle + 2.5) % 360

        # ── Orb central ───────────────────────────────────────────────────
        self._pulse += 0.04 * self._pulse_dir
        if self._pulse >= 1: self._pulse_dir = -1
        if self._pulse <= 0: self._pulse_dir =  1

        base_r = 42
        extra  = 6 * self._pulse if self.estado != "standby" else 2 * self._pulse
        r      = base_r + extra

        if self.estado == "ouvir":
            orb_fill    = "#003d20"
            orb_outline = GREEN
        elif self.estado == "processar":
            orb_fill    = "#001d38"
            orb_outline = ACCENT
        else:
            orb_fill    = "#020a14"
            orb_outline = ACCENT2

        # Brilho exterior
        for glow_r, alpha in [(r+12, "10"), (r+7, "18"), (r+3, "28")]:
            col = f"#00{'f5a0'[:2] if self.estado == 'ouvir' else 'b4ff'[:2]}"
            self.create_oval(
                cx-glow_r, cy-glow_r, cx+glow_r, cy+glow_r,
                outline="", fill=""
            )

        self.create_oval(
            cx-r, cy-r, cx+r, cy+r,
            fill=orb_fill, outline=orb_outline, width=2
        )

        # Ícone microfone
        mic_col = GREEN if self.estado == "ouvir" else ACCENT
        # Corpo
        self.create_rectangle(cx-8, cy-16, cx+8, cy+4,  fill=BG, outline=mic_col, width=1.5)
        self.create_oval(cx-8, cy-2,  cx+8, cy+10, fill=BG, outline=mic_col, width=1.5)
        # Haste
        self.create_line(cx, cy+10, cx, cy+20, fill=mic_col, width=2)
        self.create_line(cx-10, cy+20, cx+10, cy+20, fill=mic_col, width=2)

        # ── Ondas de áudio (só ao ouvir) ──────────────────────────────────
        if self.estado == "ouvir":
            self._wave_t += 0.15
            for i, offset in enumerate(range(-4, 5)):
                h = 18 * abs(math.sin(self._wave_t + i * 0.6))
                x = cx + offset * 9
                y1 = cy + 55 - h
                y2 = cy + 55 + h
                alpha_val = int(180 + 75 * math.sin(self._wave_t + i * 0.4))
                col = f"#{0:02x}{min(alpha_val, 255):02x}{100:02x}"
                self.create_line(x, y1, x, y2, fill=GREEN, width=3, capstyle="round")

        self.after(30, self._tick)   # ~33 fps

    def destroy(self):
        self._running = False
        super().destroy()


# ─────────────────────────────────────────────────────────────────────────────
class JarvisApp(ctk.CTk):
    """Janela principal do J.A.R.V.I.S."""

    def __init__(self):
        super().__init__()

        self.title("J.A.R.V.I.S.")
        self.geometry("900x620")
        self.minsize(820, 560)
        self.configure(fg_color=BG)
        self._a_correr = False

        self._build_ui()
        self._setup_jarvis()

    # ── Construção da UI ─────────────────────────────────────────────────────
    def _build_ui(self):

        # ── Barra de título personalizada ────────────────────────────────
        barra = ctk.CTkFrame(self, fg_color=BG2, height=48, corner_radius=0)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        ctk.CTkLabel(
            barra, text="J.A.R.V.I.S.",
            font=ctk.CTkFont("Courier New", 16, "bold"),
            text_color=ACCENT
        ).pack(side="left", padx=20)

        ctk.CTkLabel(
            barra, text="Assistente Virtual Inteligente",
            font=ctk.CTkFont("Courier New", 10),
            text_color=TEXT_DIM
        ).pack(side="left", padx=0)

        ctk.CTkButton(
            barra, text="✕", width=40, height=40,
            corner_radius=0, fg_color="transparent",
            hover_color=RED, text_color=TEXT_DIM,
            font=ctk.CTkFont("Courier New", 14),
            command=self.destroy
        ).pack(side="right")

        # Arrastar janela
        barra.bind("<ButtonPress-1>",   self._drag_start)
        barra.bind("<B1-Motion>",       self._drag_move)

        # ── Linha separadora ─────────────────────────────────────────────
        ctk.CTkFrame(self, fg_color=ACCENT_DIM, height=1, corner_radius=0).pack(fill="x")

        # ── Conteúdo principal ───────────────────────────────────────────
        corpo = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        corpo.pack(fill="both", expand=True, padx=0, pady=0)
        corpo.grid_columnconfigure(0, weight=1)
        corpo.grid_columnconfigure(1, weight=1)
        corpo.grid_rowconfigure(0, weight=1)

        # ── Painel esquerdo: orb + status + botão ────────────────────────
        esquerdo = ctk.CTkFrame(corpo, fg_color=BG, corner_radius=0)
        esquerdo.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        # Orb
        self.orb = OrbCanvas(esquerdo, size=260)
        self.orb.pack(pady=(30, 16))

        # Badge de estado
        self.status_var = tk.StringVar(value="● STANDBY")
        badge = tk.Frame(esquerdo, bg=BG2, bd=0, highlightthickness=1,
                         highlightbackground=ACCENT_DIM)
        badge.pack(pady=(0, 24))
        self.status_label = tk.Label(
            badge, textvariable=self.status_var,
            bg=BG2, fg=TEXT_DIM,
            font=("Courier New", 10, "bold"),
            padx=18, pady=6
        )
        self.status_label.pack()

        # Botão FALAR
        self.btn = ctk.CTkButton(
            esquerdo,
            text="🎤   FALAR",
            font=ctk.CTkFont("Courier New", 13, "bold"),
            fg_color=ACCENT2, hover_color=ACCENT,
            text_color="white",
            width=180, height=46,
            corner_radius=30,
            command=self._iniciar_escuta
        )
        self.btn.pack(pady=(0, 10))

        ctk.CTkLabel(
            esquerdo,
            text="ou pressiona  [Espaço]",
            font=ctk.CTkFont("Courier New", 9),
            text_color=TEXT_DIM
        ).pack()

        # ── Separador vertical ────────────────────────────────────────────
        ctk.CTkFrame(corpo, fg_color=ACCENT_DIM, width=1,
                     corner_radius=0).grid(row=0, column=0,
                     sticky="nse", padx=(0, 0))

        # ── Painel direito: chat ──────────────────────────────────────────
        direito = ctk.CTkFrame(corpo, fg_color=GLASS_BG, corner_radius=0)
        direito.grid(row=0, column=1, sticky="nsew")
        direito.grid_rowconfigure(1, weight=1)
        direito.grid_columnconfigure(0, weight=1)

        # Cabeçalho do chat
        chat_header = ctk.CTkFrame(direito, fg_color=BG2, corner_radius=0, height=38)
        chat_header.grid(row=0, column=0, sticky="ew")
        chat_header.grid_propagate(False)

        ctk.CTkLabel(
            chat_header, text="▸  REGISTO DE ATIVIDADE",
            font=ctk.CTkFont("Courier New", 10),
            text_color=TEXT_DIM
        ).pack(side="left", padx=14, pady=8)

        ctk.CTkButton(
            chat_header, text="limpar",
            font=ctk.CTkFont("Courier New", 9),
            fg_color="transparent", hover_color=BG3,
            text_color=TEXT_DIM, border_color=ACCENT_DIM,
            border_width=1, width=60, height=24, corner_radius=4,
            command=self._limpar_chat
        ).pack(side="right", padx=10, pady=7)

        # Área de mensagens
        self.chat = tk.Text(
            direito, bg=GLASS_BG, fg=TEXT,
            font=("Courier New", 10),
            bd=0, highlightthickness=0,
            wrap="word", state="disabled",
            padx=14, pady=10,
            insertbackground=ACCENT,
            selectbackground=ACCENT_DIM
        )
        self.chat.grid(row=1, column=0, sticky="nsew")

        scroll = ctk.CTkScrollbar(direito, command=self.chat.yview,
                                  fg_color=GLASS_BG, button_color=ACCENT_DIM,
                                  button_hover_color=ACCENT2)
        scroll.grid(row=1, column=1, sticky="ns")
        self.chat.configure(yscrollcommand=scroll.set)

        # Tags de cor
        self.chat.tag_config("jarvis_tag",  foreground=ACCENT)
        self.chat.tag_config("user_tag",    foreground=GREEN)
        self.chat.tag_config("sistema_tag", foreground=RED)
        self.chat.tag_config("hora_tag",    foreground=TEXT_DIM)

        # Atalho teclado
        self.bind("<space>", lambda e: self._iniciar_escuta()
                  if not self._a_correr else None)

    # ── Arrastar janela ──────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._dx = e.x
        self._dy = e.y

    def _drag_move(self, e):
        self.geometry(f"+{self.winfo_x()+e.x-self._dx}+{self.winfo_y()+e.y-self._dy}")

    # ── Integração com jarvis.py ─────────────────────────────────────────────
    def _setup_jarvis(self):
        jarvis.set_resposta_callback(self._msg_jarvis)

        def boas_vindas():
            time.sleep(0.5)
            jarvis.falar("Olá. Sou o Jarvis. Clica em Falar para começar.")

        threading.Thread(target=boas_vindas, daemon=True).start()

    # ── Mensagens no chat ────────────────────────────────────────────────────
    def _adicionar_msg(self, emissor: str, texto: str):
        """Adiciona uma mensagem ao chat (thread-safe via after)."""
        def _inserir():
            hora = time.strftime("%H:%M")
            self.chat.configure(state="normal")

            if emissor == "jarvis":
                self.chat.insert("end", f"[{hora}] ", "hora_tag")
                self.chat.insert("end", "JARVIS: ", "jarvis_tag")
                self.chat.insert("end", f"{texto}\n\n")
            elif emissor == "user":
                self.chat.insert("end", f"[{hora}] ", "hora_tag")
                self.chat.insert("end", "TU: ", "user_tag")
                self.chat.insert("end", f"{texto}\n\n")
            else:
                self.chat.insert("end", f"⚠ {texto}\n\n", "sistema_tag")

            self.chat.configure(state="disabled")
            self.chat.see("end")

        self.after(0, _inserir)

    def _msg_jarvis(self, texto: str):
        self._adicionar_msg("jarvis", texto)

    def _limpar_chat(self):
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.configure(state="disabled")

    # ── Estado visual ────────────────────────────────────────────────────────
    def _set_estado(self, estado: str):
        configs = {
            "standby":   ("● STANDBY",        TEXT_DIM, TEXT_DIM),
            "ouvir":     ("● A OUVIR...",      GREEN,    GREEN),
            "processar": ("● A PROCESSAR...",  ACCENT,   ACCENT),
        }
        texto, cor_label, _ = configs.get(estado, configs["standby"])

        def _atualizar():
            self.status_var.set(texto)
            self.status_label.configure(fg=cor_label)
            self.orb.set_estado(estado)
            self.btn.configure(state="disabled" if estado != "standby" else "normal")

        self.after(0, _atualizar)

    # ── Escuta ───────────────────────────────────────────────────────────────
    def _iniciar_escuta(self):
        if self._a_correr:
            return
        self._a_correr = True
        threading.Thread(target=self._escutar_thread, daemon=True).start()

    def _escutar_thread(self):
        self._set_estado("ouvir")
        comando = jarvis.ouvir()

        if not comando:
            self._set_estado("standby")
            self.after(0, lambda: self._adicionar_msg(
                "sistema", "Não percebi. Tenta outra vez."))
            self._a_correr = False
            return

        self.after(0, lambda: self._adicionar_msg("user", comando))
        self._set_estado("processar")
        jarvis.processar_comando(comando)
        self._set_estado("standby")
        self._a_correr = False


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = JarvisApp()
    app.mainloop()
