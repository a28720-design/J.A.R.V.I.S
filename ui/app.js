/* ============================================================
   J.A.R.V.I.S. — Frontend JavaScript
   ============================================================ */

// ── QWebChannel: liga ao Python ─────────────────────────────
let api = null;

new QWebChannel(qt.webChannelTransport, channel => {
  api = channel.objects.api;
  console.log("[JARVIS] Bridge Python ↔ JS ligada.");
});

// ── Canvas: grelha de fundo ──────────────────────────────────
const gridCanvas = document.getElementById("grid-canvas");
const gctx = gridCanvas.getContext("2d");

function drawGrid() {
  gridCanvas.width  = window.innerWidth;
  gridCanvas.height = window.innerHeight;
  gctx.clearRect(0, 0, gridCanvas.width, gridCanvas.height);
  gctx.strokeStyle = "rgba(124, 58, 237, 0.07)";
  gctx.lineWidth   = 1;

  const step = 40;
  for (let x = 0; x < gridCanvas.width; x += step) {
    gctx.beginPath();
    gctx.moveTo(x, 0);
    gctx.lineTo(x, gridCanvas.height);
    gctx.stroke();
  }
  for (let y = 0; y < gridCanvas.height; y += step) {
    gctx.beginPath();
    gctx.moveTo(0, y);
    gctx.lineTo(gridCanvas.width, y);
    gctx.stroke();
  }
}
drawGrid();
window.addEventListener("resize", drawGrid);

// ── Estado da interface ──────────────────────────────────────
const btnSpeak  = document.getElementById("btnSpeak");
const statusTxt = document.getElementById("statusTxt");
const statusLed = document.getElementById("statusLed");

const ESTADOS = {
  standby:   { texto: "STANDBY",         classe: ""          },
  ouvir:     { texto: "A OUVIR...",       classe: "ouvir"     },
  processar: { texto: "A PROCESSAR...",   classe: "processar" },
};

function setEstado(estado) {
  const cfg = ESTADOS[estado] || ESTADOS.standby;

  // Remove classes de estado do body
  document.body.classList.remove("ouvir", "processar");
  if (cfg.classe) document.body.classList.add(cfg.classe);

  statusTxt.textContent = cfg.texto;
  btnSpeak.disabled     = estado !== "standby";
}

// ── Mensagens ────────────────────────────────────────────────
const chatBody = document.getElementById("chatBody");

function addMsg(emissor, texto) {
  const hora = new Date().toLocaleTimeString("pt-PT", {
    hour: "2-digit", minute: "2-digit"
  });

  const div = document.createElement("div");
  div.className = `msg ${emissor}`;

  if (emissor === "sistema") {
    div.innerHTML = `<div class="msg-bubble">${escapeHtml(texto)}</div>`;
  } else {
    const labels = { jarvis: "JARVIS", user: "Tu" };
    div.innerHTML = `
      <div class="msg-meta">
        <span class="msg-label">${labels[emissor] || emissor}</span>
        <span class="msg-time">${hora}</span>
      </div>
      <div class="msg-bubble">${escapeHtml(texto)}</div>
    `;
  }

  chatBody.appendChild(div);
  chatBody.scrollTop = chatBody.scrollHeight;
}

function limparChat() {
  chatBody.innerHTML = "";
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ── Botão FALAR ──────────────────────────────────────────────
function iniciarEscuta() {
  if (!api) return;
  api.iniciar_escuta();
  ripple();
}

function ripple() {
  const btn   = btnSpeak;
  const glow  = btn.querySelector(".btn-glow");
  const clone = glow.cloneNode();
  clone.style.cssText = `
    position:absolute; inset:0; pointer-events:none; border-radius:50px;
    background: rgba(255,255,255,.25);
    animation: ripple-out .5s ease-out forwards;
  `;
  btn.appendChild(clone);
  clone.addEventListener("animationend", () => clone.remove());

  if (!document.getElementById("ripple-kf")) {
    const s = document.createElement("style");
    s.id = "ripple-kf";
    s.textContent = `
      @keyframes ripple-out {
        from { opacity:1; transform: scale(1); }
        to   { opacity:0; transform: scale(1.4); }
      }`;
    document.head.appendChild(s);
  }
}

// ── Atalho de teclado ────────────────────────────────────────
document.addEventListener("keydown", e => {
  if (e.code === "Space" && !btnSpeak.disabled) {
    e.preventDefault();
    iniciarEscuta();
  }
});
