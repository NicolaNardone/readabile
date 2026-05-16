# ============================================================
# ReadAbile - Modulo TTS (Sintesi vocale)
# Converte il testo estratto dall'OCR in un file audio MP3
# utilizzando la libreria gratuita gTTS (Google Text-to-Speech)
# ============================================================

from gtts import gTTS  # libreria che converte testo in audio usando Google Translate TTS
import os              # libreria per gestire file e cartelle del sistema operativo


def testo_in_audio(testo, percorso_output="output.mp3"):
    """
    Funzione principale del modulo TTS.
    Riceve una stringa di testo e la converte in un file audio MP3.

    Parametri:
    - testo: la stringa di testo da convertire in audio
    - percorso_output: dove salvare il file MP3 (default: "output.mp3")
    """

    # Creo l'oggetto gTTS passando il testo e la lingua
    # lang="it" = italiano
    # slow=False = velocità normale di lettura (True = lettura lenta, utile per studio)
    audio = gTTS(text=testo, lang="it", slow=False)

    # Salvo il file audio nel percorso indicato
    # Il file viene creato in formato MP3
    audio.save(percorso_output)

    print(f"Audio salvato in: {percorso_output}")


# Questo blocco viene eseguito solo se avviamo direttamente questo file
if __name__ == "__main__":
    testo = input("Inserisci il testo da convertire in audio: ")
    testo_in_audio(testo)

    # Apro automaticamente il file audio con il programma predefinito di Windows
    # os.startfile funziona solo su Windows
    os.startfile("output.mp3")
