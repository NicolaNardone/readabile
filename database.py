# ============================================================
# ReadAbile - Modulo Database
# Gestisce la connessione a PostgreSQL e tutte le operazioni
# sugli utenti: creazione tabelle, registrazione, login, ecc.
# ============================================================

import os
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from dotenv import load_dotenv


def get_conn():
    """Apre e restituisce una connessione al database."""
    url = os.environ.get("DATABASE_URL", "NON_TROVATA")
    print(f"DATABASE_URL: {url[:30]}...")  # stampo solo i primi 30 caratteri
    return psycopg2.connect(url)


load_dotenv("credenziali.env")

# URL di connessione al database PostgreSQL
# Su Railway viene letta dalla variabile d'ambiente DATABASE_URL
DATABASE_URL = os.environ.get("DATABASE_URL", "").replace("postgres://", "postgresql://", 1)

def get_conn():
    """Apre e restituisce una connessione al database."""
    return psycopg2.connect(DATABASE_URL)


def init_db():
    """
    Crea le tabelle nel database se non esistono ancora.
    Viene chiamata all'avvio dell'app.
    """
    conn = get_conn()
    cur = conn.cursor()

    # Tabella codici invito
    cur.execute("""
        CREATE TABLE IF NOT EXISTS codici_invito (
            id SERIAL PRIMARY KEY,
            codice VARCHAR(50) UNIQUE NOT NULL,
            usato BOOLEAN DEFAULT FALSE,
            data_creazione TIMESTAMP DEFAULT NOW()
        )
    """)

    # Tabella utenti
    cur.execute("""
        CREATE TABLE IF NOT EXISTS utenti (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            stato VARCHAR(20) DEFAULT 'in_attesa',
            token_sessione VARCHAR(100),
            codice_invito_usato VARCHAR(50),
            data_registrazione TIMESTAMP DEFAULT NOW()
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Database inizializzato!")


def crea_codice_invito(codice):
    """Inserisce un nuovo codice invito nel database."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO codici_invito (codice) VALUES (%s) ON CONFLICT DO NOTHING",
        (codice,)
    )
    conn.commit()
    cur.close()
    conn.close()


def verifica_codice_invito(codice):
    """
    Controlla se il codice invito esiste e non è stato ancora usato.
    Restituisce True se valido, False altrimenti.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM codici_invito WHERE codice = %s AND usato = FALSE",
        (codice,)
    )
    risultato = cur.fetchone()
    cur.close()
    conn.close()
    return risultato is not None


def segna_codice_usato(codice):
    """Segna un codice invito come usato dopo la registrazione."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE codici_invito SET usato = TRUE WHERE codice = %s",
        (codice,)
    )
    conn.commit()
    cur.close()
    conn.close()


def registra_utente(nome, email, password, codice_invito):
    """
    Registra un nuovo utente con stato 'in_attesa'.
    La password viene hashata prima di essere salvata.
    Restituisce True se successo, False se email già esistente.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Hash sicuro della password — mai salvare la password in chiaro!
        password_hash = generate_password_hash(password)
        cur.execute("""
            INSERT INTO utenti (nome, email, password_hash, stato, codice_invito_usato)
            VALUES (%s, %s, %s, 'in_attesa', %s)
        """, (nome, email, password_hash, codice_invito))
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        # Email già registrata
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def login_utente(email, password):
    """
    Verifica le credenziali dell'utente.
    Se corrette e approvato, genera un nuovo token di sessione
    (invalidando automaticamente le sessioni precedenti).
    Restituisce l'utente o None se le credenziali sono errate.
    """
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT * FROM utenti WHERE email = %s",
        (email,)
    )
    utente = cur.fetchone()

    if not utente:
        cur.close()
        conn.close()
        return None, "Email non trovata"

    # Verifico la password
    if not check_password_hash(utente["password_hash"], password):
        cur.close()
        conn.close()
        return None, "Password errata"

    # Verifico che l'account sia approvato
    if utente["stato"] == "in_attesa":
        cur.close()
        conn.close()
        return None, "Account in attesa di approvazione"

    if utente["stato"] == "bloccato":
        cur.close()
        conn.close()
        return None, "Account bloccato"

    # Genero un nuovo token di sessione univoco
    # Questo invalida automaticamente qualsiasi altra sessione attiva
    nuovo_token = secrets.token_hex(32)
    cur.execute(
        "UPDATE utenti SET token_sessione = %s WHERE id = %s",
        (nuovo_token, utente["id"])
    )
    conn.commit()

    # Aggiorno il token nell'oggetto utente
    utente = dict(utente)
    utente["token_sessione"] = nuovo_token

    cur.close()
    conn.close()
    return utente, None


def verifica_token(user_id, token):
    """
    Verifica che il token di sessione sia ancora valido.
    Se qualcuno ha fatto login dallo stesso account,
    il token sarà cambiato e questa funzione restituirà False.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM utenti WHERE id = %s AND token_sessione = %s",
        (user_id, token)
    )
    risultato = cur.fetchone()
    cur.close()
    conn.close()
    return risultato is not None


def get_utenti_in_attesa():
    """Restituisce tutti gli utenti con stato 'in_attesa' per il pannello admin."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT id, nome, email, data_registrazione FROM utenti WHERE stato = 'in_attesa' ORDER BY data_registrazione"
    )
    utenti = cur.fetchall()
    cur.close()
    conn.close()
    return utenti


def get_tutti_utenti():
    """Restituisce tutti gli utenti per il pannello admin."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT id, nome, email, stato, data_registrazione FROM utenti ORDER BY data_registrazione DESC"
    )
    utenti = cur.fetchall()
    cur.close()
    conn.close()
    return utenti


def approva_utente(user_id):
    """Approva un utente permettendogli di accedere."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE utenti SET stato = 'approvato' WHERE id = %s",
        (user_id,)
    )
    conn.commit()
    cur.close()
    conn.close()


def blocca_utente(user_id):
    """Blocca un utente impedendogli l'accesso."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE utenti SET stato = 'bloccato' WHERE id = %s",
        (user_id,)
    )
    conn.commit()
    cur.close()
    conn.close()


def get_codici():
    """Restituisce tutti i codici invito per il pannello admin."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM codici_invito ORDER BY data_creazione DESC")
    codici = cur.fetchall()
    cur.close()
    conn.close()
    return codici