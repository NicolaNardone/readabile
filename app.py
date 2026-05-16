# ============================================================
# ReadAbile - Server Web (Flask)
# Gestisce l'interfaccia grafica dell'applicazione
# Protetto da password per evitare accessi non autorizzati
# ============================================================

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
from ocr import leggi_testo
from tts import testo_in_audio
from mappa import genera_mappa

app = Flask(__name__)

# Chiave segreta per gestire le sessioni utente
app.secret_key = "readabile2026"

# Password di accesso all'applicazione
PASSWORD = "maker2026"

# Cartella dove salviamo le immagini caricate dall'utente
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Cartella per i file statici (audio, mappa)
os.makedirs("static", exist_ok=True)


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Pagina di login.
    GET = mostra il form di accesso
    POST = verifica la password inserita
    """
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            session["autenticato"] = True
            return redirect(url_for("index"))
        return render_template("login.html", errore=True)
    return render_template("login.html", errore=False)


@app.route("/logout")
def logout():
    """Cancella la sessione e reindirizza al login."""
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    """
    Pagina principale dell'app.
    Se l'utente non e' autenticato, lo mando al login.
    """
    if not session.get("autenticato"):
        return redirect(url_for("login"))
    return render_template("index.html")


@app.route("/elabora", methods=["POST"])
def elabora():
    """
    Riceve l'immagine caricata dall'utente,
    esegue OCR, TTS e genera la mappa.
    Restituisce i risultati in formato JSON.
    """
    if not session.get("autenticato"):
        return jsonify({"errore": "Non autorizzato"}), 401

    if "immagine" not in request.files:
        return jsonify({"errore": "Nessuna immagine caricata"}), 400

    file = request.files["immagine"]
    percorso = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(percorso)

    testo = leggi_testo(percorso)
    if testo == "Errore nella lettura del testo" or testo == "":
        return jsonify({"errore": "Impossibile leggere il testo"}), 500

    testo_in_audio(testo, "static/output.mp3")
    genera_mappa(testo, "static/mappa.html")

    return jsonify({
        "testo": testo,
        "audio": "/static/output.mp3",
        "mappa": "/static/mappa.html"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
