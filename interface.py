"""
interface.py — Desktop app do J.A.R.V.I.S.
Design inspirado em dexterai.org:
  - Tema escuro com acentos roxo/violeta
  - Animações de pulse suaves
  - Layout minimalista e tipografia hierárquica
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

# ── Paleta (inspirada em dexterai.org) ───────────────────────────────────────
BG          = "#07070f"       # fundo principal
BG2         = "#0e0e1a"       # fundo secundário
BG3         = "#13131f"       # fundo cards
BORDER      = "#1e1e30"       # bordas subtis
ACCENT      = "#7c3aed"       # roxo principal
ACCENT_L    = "#a78bfa"       # roxo claro
ACCENT_DIM  = "#2d1b69"       # roxo escuro
GLOW        = "#7c3aed"       # cor do glow
GREEN       = "#10b981"       # verde para "a ouvir"
GREEN_DIM   = "#064e3b"
RED         = "#ef4444"
TEXT        = "#f9fafb"       # texto principal
TEXT_MUTED  = "rgba(229, 231, 235, 0.72)"
TEXT_DIM    = "#6b7280"       # texto desativado


# ─────────────────────────────────────────────────────────────────────────────
class OrbCanvas(tk.Canvas):
    """
    Canvas central com animação estilo Dexter AI:
    - Pulse lento (8s) quando standby
    - Anel rotativo e ondas quando ativo
    """

    def __init__(self, master, size=280, **kwargs):
        super().__init__(
            master, width=size, height=size,
            bg=BG, highlightthickness=0, **kwargs
        )
        self.size   = size
        self.cx     = size // 2
        self.cy     = size // 2
        self.estado = "standby"

        self._angle     = 0.0
        self._pulse_t   = 0.0          # tempo do pulse (0→2π)
        self._wave_t    = 0.0
        self._running   = True

        self._tick()

    def set_estado(self, estado: str):
        self.estado = estado

    def _hex_to_rgb(self, hex_color):
        h = hex_color.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def _tick(self):
        if not self._running:
            return
        self.delete("all")
        cx, cy = self.cx, self.cy

        # ── Pulse lento (estilo animate-pulse-slow do Dexter) ─────────────
        # Opacidade oscila entre 0.1 e 0.4 ao longo de 8s
        self._pulse_t += 0.008   # ~8s por ciclo a 33fps
        pulse_alpha = 0.1 + 0.3 * abs(math.sin(self._pulse_t * math.pi))

        # ── Halos de glow ─────────────────────────────────────────────────
        glow_col = ACCENT if self.estado != "ouvir" else GREEN
        r, g, b = self._hex_to_rgb(glow_col)

        for glow_r, base_alpha in [(110, 0.04), (90, 0.07), (72, 0.12)]:
            alpha = int(min(255, (base_alpha + pulse_alpha * 0.1) * 255))
            fill_col = f"#{r:02x}{g:02x}{b:02x}"
            # Simula transparência com stipple
            self.create_oval(
                cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r,
                fill=fill_col, outline="",
                stipple="gray12" if alpha < 40 else "gray25"
            )

        # ── Anéis ─────────────────────────────────────────────────────────
        ring_styles = [
            (105, BORDER, 1),
            (85,  "#1a1a2e", 1),
            (68,  ACCENT_DIM, 1),
        ]
        for r_val, col, w in ring_styles:
            self.create_oval(
                cx - r_val, cy - r_val, cx + r_val, cy + r_val,
                outline=col, width=w
            )

        # ── Anel rotativo (apenas quando ativo) ───────────────────────────
        if self.estado != "standby":
            arc_col = GREEN if self.estado == "ouvir" else ACCENT_L
            speed   = 3 if self.estado == "ouvir" else 5

            self.create_arc(
                cx - 105, cy - 105, cx + 105, cy + 105,
                start=self._angle, extent=200,
                outline=arc_col, width=2, style="arc"
            )
            self.create_arc(
                cx - 105, cy - 105, cx + 105, cy + 105,
                start=self._angle + 220, extent=80,
                outline=arc_col, width=1, style="arc"
            )
            self._angle = (self._angle + speed) % 360

        # ── Orb central ───────────────────────────────────────────────────
        orb_r = 52

        if self.estado == "ouvir":
            fill    = "#052e1f"
            outline = GREEN
            ow      = 2
        elif self.estado == "processar":
            fill    = "#1a0a3a"
            outline = ACCENT_L
            ow      = 2
        else:
            fill    = "#0e0e1a"
            outline = ACCENT_DIM
            ow      = 1

        self.create_oval(
            cx - orb_r, cy - orb_r, cx + orb_r, cy + orb_r,
            fill=fill, outline=outline, width=ow
        )

        # Reflexo interno
        self.create_oval(
            cx - 20, cy - 34, cx + 8, cy - 16,
            fill="#ffffff", outline="", stipple="gray12"
        )

        # ── Ícone central ─────────────────────────────────────────────────
        ic = GREEN if self.estado == "ouvir" else ACCENT_L
        # Corpo microfone
        self.create_rectangle(cx - 9, cy - 18, cx + 9, cy + 4,
                               fill=BG3, outline=ic, width=1)
        self.create_oval(cx - 9, cy - 2, cx + 9, cy + 12,
                         fill=BG3, outline=ic, width=1)
        # Haste
        self.create_line(cx, cy + 12, cx, cy + 22, fill=ic, width=2)
        self.create_line(cx - 11, cy + 22, cx + 11, cy + 22, fill=ic, width=2)

        # ── Ondas de áudio (só ao ouvir) ──────────────────────────────────
        if self.estado == "ouvir":
            self._wave_t += 0.18
            offsets = range(-4, 5)
            for i, offset in enumerate(offsets):
                h = 20 * abs(math.sin(self._wave_t + i * 0.7))
                x  = cx + offset * 10
                y1 = cy + 66 - h
                y2 = cy + 66 + max(h, 2)
                self.create_line(x, y1, x, y2,
                                 fill=GREEN, width=3, capstyle="round")

        self.after(30, self._tick)

    def destroy(self):
        self._running = False
        super().destroy()


# ─────────────────────────────────────────────────────────────────────────────
class JarvisApp(ctk.CTk):
    """Janela principal — estética Dexter AI."""

    WIDTH  = 940
    HEIGHT = 640

    def __init__(self):
        super().__init__()

        self.title("J.A.R.V.I.S.")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(860, 580)
        self.configure(fg_color=BG)
        self._a_correr = False

        self._build_ui()
        self._setup_jarvis()

    # ── UI ───────────────────────────────────────────────────────────────────
    def _build_ui(self):

        # ── Barra de título ──────────────────────────────────────────────
        barra = ctk.CTkFrame(self, fg_color=BG2, height=52, corner_radius=0)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        # Ponto decorativo roxo
        tk.Canvas(barra, width=8, height=8, bg=BG2,
                  highlightthickness=0).pack(side="left", padx=(18, 6), pady=22)
        self.after(100, lambda: self._draw_dot(barra))

        ctk.CTkLabel(
            barra, text="J.A.R.V.I.S.",
            font=ctk.CTkFont("Segoe UI", 15, "bold"),
            text_color=TEXT
        ).pack(side="left", padx=0)

        ctk.CTkLabel(
            barra, text="  —  Assistente Virtual Inteligente",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=TEXT_DIM
        ).pack(side="left")

        # Botões de janela
        for txt, cmd, hover in [
            ("  ✕  ", self.destroy,   RED),
            ("  —  ", self.iconify,   BORDER),
        ]:
            ctk.CTkButton(
                barra, text=txt, width=42, height=52,
                corner_radius=0, fg_color="transparent",
                hover_color=hover, text_color=TEXT_DIM,
                font=ctk.CTkFont("Segoe UI", 13),
                command=cmd
            ).pack(side="right")

        barra.bind("<ButtonPress-1>", self._drag_start)
        barra.bind("<B1-Motion>",     self._drag_move)

        # Linha separadora com glow
        sep = tk.Canvas(self, height=1, bg=BG, highlightthickness=0)
        sep.pack(fill="x")
        sep.create_line(0, 0, 2000, 0, fill=ACCENT_DIM, width=1)

        # ── Layout principal ──────────────────────────────────────────────
        corpo = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        corpo.pack(fill="both", expand=True)
        corpo.grid_columnconfigure(0, weight=5)
        corpo.grid_columnconfigure(1, weight=1, minsize=1)
        corpo.grid_columnconfigure(2, weight=6)
        corpo.grid_rowconfigure(0, weight=1)

        self._build_painel_esquerdo(corpo)
        # Separador vertical
        tk.Frame(corpo, bg=BORDER, width=1).grid(
            row=0, column=1, sticky="ns", pady=20)
        self._build_painel_chat(corpo)

    def _draw_dot(self, parent):
        """Ponto roxo animado na barra de título."""
        c = tk.Canvas(parent, width=10, height=10, bg=BG2, highlightthickness=0)
        c.place(x=18, y=21)
        c.create_oval(0, 0, 10, 10, fill=ACCENT, outline="")

    # ── Painel esquerdo ──────────────────────────────────────────────────────
    def _build_painel_esquerdo(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        frame.grid(row=0, column=0, sticky="nsew")

        # Orb
        self.orb = OrbCanvas(frame, size=280)
        self.orb.pack(pady=(28, 16))

        # Badge de estado
        badge_frame = tk.Frame(frame, bg=BG3,
                               highlightthickness=1,
                               highlightbackground=BORDER)
        badge_frame.pack(pady=(0, 22))

        self.status_dot = tk.Canvas(badge_frame, width=8, height=8,
                                    bg=BG3, highlightthickness=0)
        self.status_dot.pack(side="left", padx=(14, 6), pady=10)
        self._update_dot_color(TEXT_DIM)

        self.status_var = tk.StringVar(value="STANDBY")
        self.status_lbl = tk.Label(
            badge_frame, textvariable=self.status_var,
            bg=BG3, fg=TEXT_DIM,
            font=("Segoe UI", 10, "bold"),
            padx=0, pady=9
        )
        self.status_lbl.pack(side="left", padx=(0, 14))

        # Botão principal
        self.btn = ctk.CTkButton(
            frame,
            text="🎤   FALAR",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_L,
            text_color=TEXT,
            width=190, height=48,
            corner_radius=24,
            command=self._iniciar_escuta
        )
        self.btn.pack(pady=(0, 10))

        ctk.CTkLabel(
            frame,
            text="pressiona  [Espaço]  para falar",
            font=ctk.CTkFont("Segoe UI", 9),
            text_color=TEXT_DIM
        ).pack()

        self.bind("<space>", lambda e: self._iniciar_escuta()
                  if not self._a_correr else None)

    # ── Painel de chat ───────────────────────────────────────────────────────
    def _build_painel_chat(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=BG2, corner_radius=0)
        frame.grid(row=0, column=2, sticky="nsew")
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Cabeçalho
        header = ctk.CTkFrame(frame, fg_color=BG3, corner_radius=0, height=42)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)

        ctk.CTkLabel(
            header, text="  ▸  Registo de Atividade",
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            text_color=TEXT_DIM
        ).pack(side="left", padx=8, pady=10)

        ctk.CTkButton(
            header, text="limpar",
            font=ctk.CTkFont("Segoe UI", 9),
            fg_color="transparent", hover_color=BORDER,
            text_color=TEXT_DIM, border_color=BORDER,
            border_width=1, width=56, height=26, corner_radius=6,
            command=self._limpar_chat
        ).pack(side="right", padx=10, pady=8)

        # Área de texto
        self.chat = tk.Text(
            frame,
            bg=BG2, fg=TEXT,
            font=("Segoe UI", 10),
            bd=0, highlightthickness=0,
            wrap="word", state="disabled",
            padx=16, pady=12,
            insertbackground=ACCENT,
            selectbackground=ACCENT_DIM,
            spacing3=4
        )
        self.chat.grid(row=1, column=0, sticky="nsew")

        scroll = ctk.CTkScrollbar(
            frame, command=self.chat.yview,
            fg_color=BG2,
            button_color=BORDER,
            button_hover_color=ACCENT_DIM
        )
        scroll.grid(row=1, column=1, sticky="ns")
        self.chat.configure(yscrollcommand=scroll.set)

        # Tags
        self.chat.tag_config("label_jarvis", foreground=ACCENT_L,
                             font=("Segoe UI", 9, "bold"))
        self.chat.tag_config("label_user",   foreground=GREEN,
                             font=("Segoe UI", 9, "bold"))
        self.chat.tag_config("hora",         foreground=TEXT_DIM,
                             font=("Segoe UI", 8))
        self.chat.tag_config("erro",         foreground=RED,
                             font=("Segoe UI", 9))
        self.chat.tag_config("body",         foreground=TEXT,
                             font=("Segoe UI", 10))

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._dx = e.x
        self._dy = e.y

    def _drag_move(self, e):
        self.geometry(
            f"+{self.winfo_x()+e.x-self._dx}+{self.winfo_y()+e.y-self._dy}")

    def _update_dot_color(self, cor):
        self.status_dot.delete("all")
        self.status_dot.create_oval(0, 0, 8, 8, fill=cor, outline="")

    def _set_estado(self, estado: str):
        cfg = {
            "standby":   ("STANDBY",        TEXT_DIM, TEXT_DIM, True),
            "ouvir":     ("A OUVIR...",      GREEN,    GREEN,    False),
            "processar": ("A PROCESSAR...",  ACCENT_L, ACCENT_L, False),
        }
        texto, cor_dot, cor_txt, btn_on = cfg.get(estado, cfg["standby"])

        def _atualizar():
            self.status_var.set(texto)
            self.status_lbl.configure(fg=cor_txt)
            self._update_dot_color(cor_dot)
            self.orb.set_estado(estado)
            self.btn.configure(
                state="normal" if btn_on else "disabled",
                fg_color=ACCENT if btn_on else BORDER
            )
        self.after(0, _atualizar)

    # ── Chat ─────────────────────────────────────────────────────────────────
    def _adicionar_msg(self, emissor: str, texto: str):
        def _inserir():
            hora = time.strftime("%H:%M")
            self.chat.configure(state="normal")

            if emissor == "jarvis":
                self.chat.insert("end", f"{hora}  ", "hora")
                self.chat.insert("end", "JARVIS\n", "label_jarvis")
                self.chat.insert("end", f"{texto}\n\n", "body")
            elif emissor == "user":
                self.chat.insert("end", f"{hora}  ", "hora")
                self.chat.insert("end", "TU\n", "label_user")
                self.chat.insert("end", f"{texto}\n\n", "body")
            else:
                self.chat.insert("end", f"⚠  {texto}\n\n", "erro")

            self.chat.configure(state="disabled")
            self.chat.see("end")

        self.after(0, _inserir)

    def _msg_jarvis(self, texto: str):
        self._adicionar_msg("jarvis", texto)

    def _limpar_chat(self):
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.configure(state="disabled")

    # ── Jarvis ───────────────────────────────────────────────────────────────
    def _setup_jarvis(self):
        jarvis.set_resposta_callback(self._msg_jarvis)

        def boas_vindas():
            time.sleep(0.6)
            jarvis.falar("Olá. Sou o Jarvis. Clica em Falar para começar.")

        threading.Thread(target=boas_vindas, daemon=True).start()

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
