"""
jarvis.py — Núcleo do assistente: voz, TTS e processamento de comandos.
Não tem loop próprio; é controlado pelo main.py.
"""

import datetime
import os
import subprocess
import tempfile
import threading
import time
import webbrowser

import numpy as np
import pyttsx3
import scipy.io.wavfile as wav
import sounddevice as sd
import speech_recognition as sr

# ---------------------------------------------------------------------------
# Configuração de áudio
# ---------------------------------------------------------------------------
SAMPLE_RATE = 16000
DURATION    = 5        # segundos de gravação por comando

# ---------------------------------------------------------------------------
# Deteção de aplausos (inspirado em github.com/RafaTatay/jarvis)
# ---------------------------------------------------------------------------
CLAP_SAMPLE_RATE = 44100
CLAP_BLOCK_SIZE  = int(CLAP_SAMPLE_RATE * 0.05)   # blocos de 50ms
CLAP_THRESHOLD   = 0.18    # sensibilidade (sobe se detetar ruído, desce se não detetar)
CLAP_COOLDOWN    = 0.25    # segundos mínimos entre aplausos
CLAP_WINDOW      = 2.0     # janela de tempo para o 2º aplauso

_clap_stream    = None
_clap_times: list = []
_clap_lock      = threading.Lock()
_clap_callback  = None     # chamado quando dois aplausos são detetados


def set_clap_callback(fn):
    """Regista a função a chamar quando dois aplausos são detetados."""
    global _clap_callback
    _clap_callback = fn


def _clap_audio_cb(indata, frames, time_info, status):
    """Callback do stream de áudio — corre numa thread interna do sounddevice."""
    global _clap_times

    rms = float(np.sqrt(np.mean(indata ** 2)))
    now = time.time()

    if rms < CLAP_THRESHOLD:
        return

    with _clap_lock:
        # Ignora se ainda estamos no cooldown do aplauso anterior
        if _clap_times and (now - _clap_times[-1]) < CLAP_COOLDOWN:
            return

        _clap_times.append(now)
        # Remove aplausos fora da janela de tempo
        _clap_times = [t for t in _clap_times if now - t <= CLAP_WINDOW]

        print(f"[CLAP] 👏 {len(_clap_times)}/2  (RMS={rms:.3f})")

        if len(_clap_times) >= 2:
            _clap_times = []
            if _clap_callback:
                threading.Thread(target=_clap_callback, daemon=True).start()


def start_clap_listener():
    """Inicia o stream de deteção de aplausos em background."""
    global _clap_stream
    if _clap_stream is not None:
        return
    _clap_stream = sd.InputStream(
        samplerate=CLAP_SAMPLE_RATE,
        blocksize=CLAP_BLOCK_SIZE,
        channels=1,
        dtype="float32",
        callback=_clap_audio_cb,
    )
    _clap_stream.start()
    print("[CLAP] A ouvir aplausos...")


def stop_clap_listener():
    """Para o stream de deteção de aplausos."""
    global _clap_stream, _clap_times
    if _clap_stream is not None:
        _clap_stream.stop()
        _clap_stream.close()
        _clap_stream = None
    with _clap_lock:
        _clap_times = []

# ---------------------------------------------------------------------------
# Motor de voz (TTS) — inicializado uma vez
# ---------------------------------------------------------------------------
engine = pyttsx3.init()
engine.setProperty("rate", 160)
engine.setProperty("volume", 1.0)

# Callback de resposta — substituído pela interface
_resposta_callback = None

def set_resposta_callback(fn):
    """Regista uma função que é chamada sempre que Jarvis responde."""
    global _resposta_callback
    _resposta_callback = fn

def falar(texto: str) -> None:
    """Fala o texto em voz alta e chama o callback de resposta."""
    print(f"[JARVIS] {texto}")
    if _resposta_callback:
        _resposta_callback(texto)
    engine.say(texto)
    engine.runAndWait()

# ---------------------------------------------------------------------------
# Reconhecimento de voz (STT)
# ---------------------------------------------------------------------------
recognizer = sr.Recognizer()

def ouvir() -> str:
    """
    Grava DURATION segundos do microfone e devolve o texto (minúsculas).
    Usa sounddevice + SpeechRecognition (sem PyAudio).
    """
    audio_data = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
    )
    sd.wait()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    wav.write(tmp_path, SAMPLE_RATE, audio_data)

    try:
        with sr.AudioFile(tmp_path) as source:
            audio = recognizer.record(source)
        texto = recognizer.recognize_google(audio, language="pt-PT")
        return texto.lower()
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        falar("Erro de ligação ao serviço de reconhecimento de voz.")
        return ""
    finally:
        os.remove(tmp_path)

# ---------------------------------------------------------------------------
# Processamento de comandos
# ---------------------------------------------------------------------------
def processar_comando(comando: str) -> None:
    """Interpreta e executa um comando de texto."""

    # Horas
    if any(p in comando for p in ["horas", "hora", "que horas"]):
        agora = datetime.datetime.now().strftime("%H:%M")
        falar(f"São {agora}.")

    # Data
    elif any(p in comando for p in ["data", "dia", "que dia"]):
        hoje = datetime.datetime.now().strftime("%d de %B de %Y")
        falar(f"Hoje é {hoje}.")

    # Pesquisa no Google
    elif any(p in comando for p in ["pesquisa", "procura", "pesquisar", "google"]):
        for kw in ["pesquisa", "procura", "pesquisar", "google"]:
            if kw in comando:
                termo = comando.split(kw, 1)[-1].strip()
                break
        if termo:
            falar(f"A pesquisar {termo} no Google.")
            webbrowser.open(f"https://www.google.com/search?q={termo.replace(' ', '+')}")
        else:
            falar("O que devo pesquisar?")

    # Abrir aplicações
    elif any(p in comando for p in ["abre", "abrir", "abre o", "abrir o"]):
        if any(p in comando for p in ["chrome", "browser", "navegador"]):
            falar("A abrir o Chrome.")
            subprocess.Popen("start chrome", shell=True)
        elif any(p in comando for p in ["notepad", "bloco de notas"]):
            falar("A abrir o Bloco de Notas.")
            subprocess.Popen("notepad", shell=True)
        elif any(p in comando for p in ["explorador", "ficheiros", "explorer"]):
            falar("A abrir o Explorador de Ficheiros.")
            subprocess.Popen("explorer", shell=True)
        elif "calculadora" in comando:
            falar("A abrir a Calculadora.")
            subprocess.Popen("calc", shell=True)
        elif "spotify" in comando:
            falar("A abrir o Spotify.")
            subprocess.Popen("start spotify", shell=True)
        elif "discord" in comando:
            falar("A abrir o Discord.")
            subprocess.Popen("start discord", shell=True)
        else:
            falar("Não sei abrir essa aplicação.")

    # Volume
    elif "volume" in comando:
        if any(p in comando for p in ["aumenta", "sobe", "mais"]):
            for _ in range(5):
                subprocess.run(
                    ["powershell", "-c",
                     "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"],
                    capture_output=True
                )
            falar("Volume aumentado.")
        elif any(p in comando for p in ["diminui", "baixa", "menos"]):
            for _ in range(5):
                subprocess.run(
                    ["powershell", "-c",
                     "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"],
                    capture_output=True
                )
            falar("Volume reduzido.")
        elif any(p in comando for p in ["mudo", "silêncio", "silencio", "cala"]):
            subprocess.run(
                ["powershell", "-c",
                 "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"],
                capture_output=True
            )
            falar("Áudio em silêncio.")

    # Cumprimentos
    elif any(p in comando for p in ["olá", "ola", "bom dia", "boa tarde", "boa noite"]):
        hora = datetime.datetime.now().hour
        if hora < 12:
            falar("Bom dia! Como posso ajudar?")
        elif hora < 18:
            falar("Boa tarde! Em que posso ser útil?")
        else:
            falar("Boa noite! Às suas ordens.")

    # Comando não reconhecido
    else:
        falar("Não percebi o comando. Tenta dizer jarvis seguido do que precisas.")
