# ============================================================
# ReadAbile - Server Web (Flask)
# Gestisce l'interfaccia grafica dell'applicazione
# ============================================================

from flask import Flask, render_template, request, jsonify
import os
from ocr import leggi_testo
from tts import testo_in_audio
from mappa import genera_mappa

app = Flask(__name__)

# Cartella dove salviamo le immagini caricate dall'utente
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Cartella per i file statici (audio, mappa)
os.makedirs("static", exist_ok=True)


@app.route("/")
def index():
    """Pagina principale dell'app."""
    return render_template("index.html")


@app.route("/elabora", methods=["POST"])
def elabora():
    """
    Riceve l'immagine caricata dall'utente,
    esegue OCR, TTS e genera la mappa.
    Restituisce i risultati in formato JSON.
    """

    # Controllo se è stato caricato un file
    if "immagine" not in request.files:
        return jsonify({"errore": "Nessuna immagine caricata"}), 400

    file = request.files["immagine"]

    # Salvo l'immagine nella cartella uploads
    percorso = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(percorso)

    # OCR — leggo il testo dall'immagine
    testo = leggi_testo(percorso)
    if testo == "Errore nella lettura del testo" or testo == "":
        return jsonify({"errore": "Impossibile leggere il testo"}), 500

    # TTS — converto il testo in audio
    testo_in_audio(testo, "static/output.mp3")

    # Mappa — genero la mappa concettuale
    genera_mappa(testo, "static/mappa.html")

    return jsonify({
        "testo": testo,
        "audio": "/static/output.mp3",
        "mappa": "/static/mappa.html"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
