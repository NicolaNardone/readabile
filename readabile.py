# ============================================================
# ReadAbile - Script principale
# Collega il modulo OCR e il modulo TTS:
# 1. Legge il testo da un'immagine (OCR)
# 2. Converte il testo in audio (TTS)
# ============================================================

import os
from ocr import leggi_testo        # importo la funzione OCR dal file ocr.py
from tts import testo_in_audio     # importo la funzione TTS dal file tts.py


def elabora_immagine(percorso_immagine):
    """
    Funzione principale di ReadAbile.
    Riceve il percorso di un'immagine, estrae il testo
    e lo converte in audio.
    """

    print("\nLettura testo dall'immagine...")

    # Chiamo la funzione OCR passando il percorso dell'immagine
    testo = leggi_testo(percorso_immagine)

    # Controllo se il testo è stato letto correttamente
    if testo == "Errore nella lettura del testo" or testo == "":
        print("Impossibile leggere il testo dall'immagine.")
        return

    print("\n--- TESTO RILEVATO ---")
    print(testo)

    print("\nConversione in audio...")

    # Chiamo la funzione TTS passando il testo e il nome del file di output
    testo_in_audio(testo, "output.mp3")

    print("\nFatto! Riproduco l'audio...")

    # Apro automaticamente il file audio con il programma predefinito di Windows
    os.startfile("output.mp3")


# Questo blocco viene eseguito solo se avviamo direttamente questo file
if __name__ == "__main__":
    percorso = input("Inserisci il percorso dell'immagine: ")
    elabora_immagine(percorso)
