# ============================================================
# ReadAbile - Modulo OCR (Riconoscimento testo da immagine)
# Utilizza l'API gratuita di OCR.space per estrarre il testo
# da foto scattate con il telefono o caricate dal PC
# ============================================================

import requests      # libreria per fare richieste a internet (chiamate API)
import os            # libreria per gestire file e cartelle del sistema operativo
from dotenv import load_dotenv  # libreria per leggere variabili da file .env

# Carico le variabili dal file credenziali.env
# In questo file è salvata la chiave API in modo sicuro,
# così non è scritta direttamente nel codice
load_dotenv("credenziali.env")

# Leggo la chiave API dalla variabile d'ambiente appena caricata
# La chiave API è come una password che identifica il nostro progetto
# presso il servizio OCR.space
API_KEY = os.getenv("OCR_API_KEY")


def leggi_testo(percorso_immagine):
    """
    Funzione principale del modulo OCR.
    Riceve il percorso di un'immagine sul disco,
    la invia all'API di OCR.space e restituisce
    il testo riconosciuto come stringa.
    """

    # Apro il file immagine in modalità binaria ("rb" = read binary)
    # La modalità binaria è necessaria perché le immagini non sono
    # file di testo ma sequenze di byte
    with open(percorso_immagine, "rb") as f:
        immagine = f.read()  # leggo tutto il contenuto del file

    # Ricavo solo il nome del file dal percorso completo
    # Esempio: "./foto/prova.jpeg" → "prova.jpeg"
    # Serve per indicare all'API il nome del file che stiamo inviando
    nome_file = os.path.basename(percorso_immagine)

    # Invio l'immagine all'API di OCR.space tramite una richiesta HTTP POST
    # È come compilare un modulo online e cliccare "Invia"
    risposta = requests.post(
        "https://api.ocr.space/parse/image",  # indirizzo dell'API

        # "files" contiene il file immagine da analizzare
        # il formato è: (nome_file, contenuto, tipo_di_file)
        files={"file": (nome_file, immagine, "image/jpeg")},

        # "data" contiene i parametri della richiesta
        data={
            "apikey": API_KEY,          # la nostra chiave di accesso al servizio
            "language": "auto",         # rileva automaticamente la lingua del testo
            "isOverlayRequired": False, # non serve la posizione delle parole nell'immagine
            "filetype": "JPG",          # formato del file immagine
            "OCREngine": "3",           # motore OCR più preciso (Engine 3 = qualità massima)
            "detectOrientation": True,  # raddrizza automaticamente le foto storte
            "scale": True,              # migliora la qualità delle foto a bassa risoluzione
        }
    )

    # Converto la risposta dal formato JSON a un dizionario Python
    # JSON è il formato standard usato dalle API per scambiare dati
    risultato = risposta.json()

    # Controllo se l'API ha restituito un errore durante l'elaborazione
    # .get() è usato per evitare errori se la chiave non esiste nella risposta
    if risultato.get("IsErroredOnProcessing", True):
        return "Errore nella lettura del testo"

    # Estraggo il testo riconosciuto dalla risposta
    # "ParsedResults" è una lista (potrebbero esserci più pagine)
    # prendiamo solo il primo elemento [0] perché mandiamo una sola immagine
    testo = risultato["ParsedResults"][0]["ParsedText"]

    # .strip() rimuove spazi e righe vuote all'inizio e alla fine del testo
    return testo.strip()


# Questo blocco viene eseguito solo se avviamo direttamente questo file
if __name__ == "__main__":
    percorso = input("Inserisci il percorso dell'immagine: ")
    testo = leggi_testo(percorso)
    print("\n--- TESTO RILEVATO ---")
    print(testo)
