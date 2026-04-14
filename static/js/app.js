/* =========================================================
   J.A.R.V.I.S. — Frontend JavaScript
   Gere SocketIO, animações e interações da interface
   ========================================================= */

// ── Elementos do DOM ──────────────────────────────────────
const btnMic     = document.getElementById("btnMic");
const statusText = document.getElementById("statusText");
const chatBody   = document.getElementById("chatBody");

// ── SocketIO ──────────────────────────────────────────────
const socket = io();

socket.on("connect",    () => console.log("[JARVIS] Ligado ao servidor."));
socket.on("disconnect", () => definirEstado("offline"));

// Recebe mudanças de estado
socket.on("estado", ({ estado }) => definirEstado(estado));

// Recebe mensagens
socket.on("mensagem", ({ emissor, texto }) => adicionarMensagem(emissor, texto));

// ── Partículas de fundo ──────────────────────────────────
const canvas = document.getElementById("particles");
const ctx    = canvas.getContext("2d");
let particulas = [];

function initParticulas() {
  canvas.width  = window.innerWidth;
  canvas.height = window.innerHeight;

  particulas = Array.from({ length: 80 }, () => ({
    x:  Math.random() * canvas.width,
    y:  Math.random() * canvas.height,
    r:  Math.random() * 1.5 + 0.3,
    vx: (Math.random() - 0.5) * 0.25,
    vy: (Math.random() - 0.5) * 0.25,
    o:  Math.random() * 0.5 + 0.1,
  }));
}

function animarParticulas() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  particulas.forEach(p => {
    p.x += p.vx;
    p.y += p.vy;
    if (p.x < 0) p.x = canvas.width;
    if (p.x > canvas.width)  p.x = 0;
    if (p.y < 0) p.y = canvas.height;
    if (p.y > canvas.height) p.y = 0;

    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(0, 180, 255, ${p.o})`;
    ctx.fill();
  });

  // Linhas entre partículas próximas
  for (let i = 0; i < particulas.length; i++) {
    for (let j = i + 1; j < particulas.length; j++) {
      const dx = particulas[i].x - particulas[j].x;
      const dy = particulas[i].y - particulas[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 100) {
        ctx.beginPath();
        ctx.strokeStyle = `rgba(0, 180, 255, ${0.08 * (1 - dist / 100)})`;
        ctx.lineWidth = 0.5;
        ctx.moveTo(particulas[i].x, particulas[i].y);
        ctx.lineTo(particulas[j].x, particulas[j].y);
        ctx.stroke();
      }
    }
  }

  requestAnimationFrame(animarParticulas);
}

window.addEventListener("resize", initParticulas);
initParticulas();
animarParticulas();

// ── Estado da interface ───────────────────────────────────
const ESTADOS = {
  standby:   { texto: "STANDBY",       classe: "",          btn: true  },
  ouvir:     { texto: "A OUVIR...",    classe: "ouvir",     btn: false },
  processar: { texto: "A PROCESSAR...", classe: "processar", btn: false },
  offline:   { texto: "OFFLINE",       classe: "",          btn: false },
};

function definirEstado(estado) {
  const cfg = ESTADOS[estado] || ESTADOS.standby;

  // Remove todas as classes de estado
  document.body.classList.remove("ouvir", "processar");
  if (cfg.classe) document.body.classList.add(cfg.classe);

  statusText.textContent = cfg.texto;
  btnMic.disabled = !cfg.btn;
}

// ── Mensagens no chat ─────────────────────────────────────
function adicionarMensagem(emissor, texto) {
  const wrapper = document.createElement("div");
  wrapper.className = `msg ${emissor}`;

  const labels = { jarvis: "JARVIS", user: "TU", sistema: "SISTEMA" };
  const label = document.createElement("div");
  label.className = "msg-label";
  label.textContent = labels[emissor] || emissor.toUpperCase();

  const balao = document.createElement("div");
  balao.className = "msg-text";
  balao.textContent = texto;

  if (emissor !== "sistema") wrapper.appendChild(label);
  wrapper.appendChild(balao);
  chatBody.appendChild(wrapper);

  // Scroll automático para a última mensagem
  chatBody.scrollTop = chatBody.scrollHeight;
}

function limparChat() {
  chatBody.innerHTML = "";
}

// ── Botão FALAR ───────────────────────────────────────────
function iniciarEscuta() {
  socket.emit("iniciar_escuta");
  rippleEffect();
}

function rippleEffect() {
  const ripple = btnMic.querySelector(".btn-ripple");
  ripple.style.cssText = `
    width: 200px; height: 200px;
    top: 50%; left: 50%;
    margin-top: -100px; margin-left: -100px;
    animation: ripple-anim 0.6s ease-out forwards;
  `;

  // Injeta a keyframe se ainda não existir
  if (!document.getElementById("ripple-style")) {
    const s = document.createElement("style");
    s.id = "ripple-style";
    s.textContent = `
      @keyframes ripple-anim {
        from { transform: scale(0); opacity: 1; }
        to   { transform: scale(2); opacity: 0; }
      }`;
    document.head.appendChild(s);
  }

  setTimeout(() => { ripple.style.cssText = ""; }, 700);
}

// ── Atalho de teclado: Espaço para falar ─────────────────
document.addEventListener("keydown", e => {
  if (e.code === "Space" && !btnMic.disabled && document.activeElement.tagName !== "INPUT") {
    e.preventDefault();
    iniciarEscuta();
  }
});
