# ============================================================
# ReadAbile - Server Web (Flask)
# Gestisce autenticazione, registrazione, pannello admin
# e le funzionalità principali dell'app
# ============================================================

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from ocr import leggi_testo
from tts import testo_in_audio
from mappa import genera_mappa
from database import (
    init_db, registra_utente, login_utente, verifica_token,
    verifica_codice_invito, segna_codice_usato,
    get_utenti_in_attesa, get_tutti_utenti,
    approva_utente, blocca_utente,
    crea_codice_invito, get_codici
)

load_dotenv("credenziali.env")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "readabile2026")

# Password pannello amministratore
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin2026")

# Cartelle necessarie
os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)



# Inizializzo il database all'avvio
init_db()

@app.route("/admin/elimina/<int:user_id>")
def admin_elimina(user_id):
    if not admin_autenticato():
        return redirect(url_for("admin_login"))
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM utenti WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/reset-password/<int:user_id>", methods=["POST"])
def admin_reset_password(user_id):
    if not admin_autenticato():
        return redirect(url_for("admin_login"))
    nuova_password = request.form.get("nuova_password")
    if not nuova_password or len(nuova_password) < 6:
        return redirect(url_for("admin_dashboard"))
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE utenti SET password_hash = %s WHERE id = %s",
        (generate_password_hash(nuova_password), user_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("admin_dashboard"))

# ─── HELPERS ─────────────────────────────────────────────

def utente_autenticato():
    """
    Controlla se l'utente è autenticato E se il suo token
    di sessione è ancora valido nel database.
    Se il token non corrisponde (account usato su altro dispositivo)
    disconnette automaticamente.
    """
    if "user_id" not in session or "token" not in session:
        return False
    if not verifica_token(session["user_id"], session["token"]):
        session.clear()
        return False
    return True


def admin_autenticato():
    """Controlla se l'amministratore è autenticato."""
    return session.get("admin") == True


# ─── ROTTE UTENTE ────────────────────────────────────────

@app.route("/")
def index():
    """Pagina principale — richiede autenticazione."""
    if not utente_autenticato():
        return redirect(url_for("login"))
    return render_template("index.html", nome=session.get("nome"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Pagina di login utente."""
    if request.method == "POST":
        email    = request.form.get("email")
        password = request.form.get("password")

        utente, errore = login_utente(email, password)

        if errore:
            return render_template("login.html", errore=errore)

        # Salvo i dati dell'utente nella sessione
        session["user_id"] = utente["id"]
        session["nome"]    = utente["nome"]
        session["token"]   = utente["token_sessione"]

        return redirect(url_for("index"))

    return render_template("login.html", errore=None)


@app.route("/registrati", methods=["GET", "POST"])
def registrati():
    """Pagina di registrazione con codice invito."""
    if request.method == "POST":
        nome           = request.form.get("nome")
        email          = request.form.get("email")
        password       = request.form.get("password")
        codice_invito  = request.form.get("codice_invito").strip().upper()

        # Verifico il codice invito
        if not verifica_codice_invito(codice_invito):
            return render_template("registrati.html", errore="Codice invito non valido o già utilizzato")

        # Registro l'utente
        successo = registra_utente(nome, email, password, codice_invito)

        if not successo:
            return render_template("registrati.html", errore="Email già registrata")

        # Segno il codice come usato
        segna_codice_usato(codice_invito)

        return render_template("registrati.html", successo=True)

    return render_template("registrati.html", errore=None)


@app.route("/logout")
def logout():
    """Disconnette l'utente."""
    session.clear()
    return redirect(url_for("login"))


# ─── ROTTA ELABORAZIONE ──────────────────────────────────

@app.route("/elabora", methods=["POST"])
def elabora():
    """
    Riceve l'immagine, esegue OCR + TTS + Mappa.
    Richiede autenticazione e verifica il token di sessione.
    """
    if not utente_autenticato():
        return jsonify({"errore": "Non autorizzato"}), 401

    if "immagine" not in request.files:
        return jsonify({"errore": "Nessuna immagine caricata"}), 400

    file     = request.files["immagine"]
    percorso = os.path.join("uploads", file.filename)
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


# ─── ROTTE ADMIN ─────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Login pannello amministratore."""
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        return render_template("admin_login.html", errore=True)
    return render_template("admin_login.html", errore=False)


@app.route("/admin")
def admin_dashboard():
    """Pannello di controllo admin — utenti e codici invito."""
    if not admin_autenticato():
        return redirect(url_for("admin_login"))

    utenti        = get_tutti_utenti()
    in_attesa     = get_utenti_in_attesa()
    codici        = get_codici()

    return render_template("admin.html",
        utenti=utenti,
        in_attesa=in_attesa,
        codici=codici
    )


@app.route("/admin/approva/<int:user_id>")
def admin_approva(user_id):
    """Approva un utente in attesa."""
    if not admin_autenticato():
        return redirect(url_for("admin_login"))
    approva_utente(user_id)
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/blocca/<int:user_id>")
def admin_blocca(user_id):
    """Blocca un utente."""
    if not admin_autenticato():
        return redirect(url_for("admin_login"))
    blocca_utente(user_id)
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/crea-codice", methods=["POST"])
def admin_crea_codice():
    """Genera un nuovo codice invito."""
    if not admin_autenticato():
        return redirect(url_for("admin_login"))

    import secrets
    # Genero un codice di 8 caratteri maiuscoli
    codice = secrets.token_hex(4).upper()
    crea_codice_invito(codice)
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/logout")
def admin_logout():
    """Disconnette l'amministratore."""
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


# ─── AVVIO ───────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)