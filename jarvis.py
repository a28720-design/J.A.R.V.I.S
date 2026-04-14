import datetime
import os
import tempfile
import webbrowser

import numpy as np
import pyttsx3
import scipy.io.wavfile as wav
import sounddevice as sd
import speech_recognition as sr

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
SAMPLE_RATE = 16000   # Hz — ideal para reconhecimento de voz
DURATION    = 5       # segundos de gravação por comando
WAKE_WORD   = "jarvis"

# ---------------------------------------------------------------------------
# Motor de voz (text-to-speech)
# ---------------------------------------------------------------------------
engine = pyttsx3.init()
engine.setProperty("rate", 165)          # velocidade da voz
engine.setProperty("volume", 1.0)

def falar(texto: str) -> None:
    """Jarvis responde em voz alta e imprime no ecrã."""
    print(f"JARVIS: {texto}")
    engine.say(texto)
    engine.runAndWait()

# ---------------------------------------------------------------------------
# Captura e reconhecimento de voz
# ---------------------------------------------------------------------------
recognizer = sr.Recognizer()

def ouvir() -> str:
    """Grava áudio do microfone e devolve o texto reconhecido (minúsculas)."""
    print("A ouvir...")
    audio_data = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
    )
    sd.wait()  # aguarda fim da gravação

    # Guarda num ficheiro WAV temporário para o SpeechRecognition processar
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    wav.write(tmp_path, SAMPLE_RATE, audio_data)

    try:
        with sr.AudioFile(tmp_path) as source:
            audio = recognizer.record(source)
        texto = recognizer.recognize_google(audio, language="pt-PT")
        print(f"Reconhecido: {texto}")
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
def processar_comando(comando: str) -> bool:
    """
    Interpreta e executa um comando.
    Devolve False se o utilizador pedir para sair.
    """

    # --- Sair ---
    if any(p in comando for p in ["sair", "desligar", "tchau", "adeus"]):
        falar("Até logo. Desligando.")
        return False

    # --- Horas ---
    if any(p in comando for p in ["horas", "hora", "que horas"]):
        agora = datetime.datetime.now().strftime("%H:%M")
        falar(f"São {agora}.")

    # --- Data ---
    elif any(p in comando for p in ["data", "dia", "que dia"]):
        hoje = datetime.datetime.now().strftime("%d de %B de %Y")
        falar(f"Hoje é {hoje}.")

    # --- Pesquisa no Google ---
    elif "pesquisa" in comando or "procura" in comando or "pesquisar" in comando:
        # Extrai o termo de pesquisa depois da palavra-chave
        for kw in ["pesquisa", "procura", "pesquisar"]:
            if kw in comando:
                termo = comando.split(kw, 1)[-1].strip()
                break
        if termo:
            falar(f"A pesquisar {termo} no Google.")
            webbrowser.open(f"https://www.google.com/search?q={termo.replace(' ', '+')}")
        else:
            falar("O que devo pesquisar?")

    # --- Abrir aplicações ---
    elif "abre" in comando or "abrir" in comando:
        if "chrome" in comando or "browser" in comando or "navegador" in comando:
            falar("A abrir o Chrome.")
            os.startfile("chrome")
        elif "notepad" in comando or "bloco de notas" in comando:
            falar("A abrir o Bloco de Notas.")
            os.startfile("notepad")
        elif "explorador" in comando or "ficheiros" in comando:
            falar("A abrir o Explorador de Ficheiros.")
            os.startfile("explorer")
        elif "calculadora" in comando:
            falar("A abrir a Calculadora.")
            os.startfile("calc")
        else:
            falar("Não sei abrir essa aplicação.")

    # --- Comando não reconhecido ---
    else:
        falar("Não percebi o comando. Tenta outra vez.")

    return True

# ---------------------------------------------------------------------------
# Loop principal
# ---------------------------------------------------------------------------
def main() -> None:
    falar("Olá. Sou o Jarvis, o teu assistente pessoal. Como posso ajudar?")

    ativo = True
    while ativo:
        comando = ouvir()
        if not comando:
            continue

        # Modo wake-word: só reage se ouvir "jarvis"
        if WAKE_WORD in comando:
            # Remove a wake-word e processa o resto
            comando_limpo = comando.replace(WAKE_WORD, "").strip()
            if not comando_limpo:
                falar("Sim? Estou a ouvir.")
                comando_limpo = ouvir()
            ativo = processar_comando(comando_limpo)
        # Modo direto (sem wake-word): aceita tudo enquanto estiver ativo
        # Descomenta a linha abaixo para desativar o modo wake-word:
        # ativo = processar_comando(comando)


if __name__ == "__main__":
    main()
