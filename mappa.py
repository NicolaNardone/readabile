# ============================================================
# ReadAbile - Modulo Mappa Visiva (versione Groq + LLaMA)
# Usa LLaMA 3.3 70B gratuito via Groq per analizzare il testo
# e generare una mappa concettuale gerarchica intelligente.
# ============================================================

import os                          # gestione file e variabili di sistema
from dotenv import load_dotenv     # lettura chiavi API dal file credenziali.env
from groq import Groq              # client per le API di Groq (LLaMA 3)
from pyvis.network import Network  # libreria per creare grafi interattivi HTML
import json                        # per convertire la risposta AI in dizionario Python

# Carico le variabili dal file credenziali.env
load_dotenv("credenziali.env")

# Leggo la chiave API di Groq dalla variabile d'ambiente
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Creo il client Groq che useremo per fare le chiamate all'AI
client = Groq(api_key=GROQ_API_KEY)


def estrai_struttura_mappa(testo):
    """
    Manda il testo a LLaMA 3 via Groq e chiede di restituire
    la struttura della mappa in formato JSON.
    """

    # Costruisco il prompt — le istruzioni precise per l'AI
    prompt = f"""Analizza questo testo e crea una mappa concettuale gerarchica.
Rispondi SOLO con un JSON valido, senza spiegazioni, senza markdown, senza backtick.

Il JSON deve avere questa struttura:
{{
  "concetto_centrale": "il tema principale del testo",
  "rami": [
    {{
      "concetto": "argomento principale 1",
      "sotto_concetti": ["dettaglio 1", "dettaglio 2"]
    }},
    {{
      "concetto": "argomento principale 2",
      "sotto_concetti": ["dettaglio 1", "dettaglio 2"]
    }}
  ]
}}

Testo da analizzare:
{testo}"""

    # Chiamo l'API di Groq con il modello LLaMA 3.3 70B
    risposta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # modello LLaMA 3.3 con 70 miliardi di parametri
        messages=[
            {
                "role": "system",
                "content": "Sei un esperto di mappe concettuali. Rispondi sempre e solo con JSON valido."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        # temperature 0.3 = leggermente creativo ma preciso, ideale per JSON
        temperature=0.3,
        # max_tokens = numero massimo di parole nella risposta
        max_tokens=1000
    )

    # Estraggo il testo della risposta
    testo_risposta = risposta.choices[0].message.content.strip()

    # Converto il JSON in dizionario Python
    struttura = json.loads(testo_risposta)
    return struttura


def genera_mappa(testo, percorso_output="mappa.html"):
    """
    Genera una mappa concettuale gerarchica dal testo.

    Struttura visiva:
    - Nodo BLU (grande) = concetto centrale
    - Nodi VIOLA (medi) = rami principali (livello 2)
    - Nodi VERDI (piccoli) = sotto-concetti (livello 3)
    """

    print("Analizzo il testo con LLaMA 3...")

    # Chiedo all'AI di analizzare il testo
    struttura = estrai_struttura_mappa(testo)

    print(f"Struttura generata: {struttura['concetto_centrale']}")

    # Creo la rete visiva con pyvis
    rete = Network(
        height="700px",
        width="100%",
        bgcolor="#1a1a2e",
        font_color="white",
        directed=False  # senza frecce direzionali per permettere la modifica
    )

    # Layout con fisica abilitata per permettere il trascinamento dei nodi
    rete.set_options("""
    {
        "physics": {
            "enabled": true,
            "stabilization": { "iterations": 200 },
            "barnesHut": {
                "gravitationalConstant": -8000,
                "springLength": 200
            }
        },
        "manipulation": {
            "enabled": true
        },
        "interaction": {
            "dragNodes": true,
            "dragView": true,
            "zoomView": true
        },
        "edges": {
            "color": "#4a9eff",
            "smooth": { "type": "cubicBezier" }
        }
    }
    """)

    # Nodo centrale — il più grande e prominente
    concetto_centrale = struttura["concetto_centrale"]
    rete.add_node(
        concetto_centrale,
        label=concetto_centrale,
        color="#4a9eff",   # blu
        size=45,
        shape="ellipse",
        font={"size": 20, "color": "white", "bold": True}
    )

    # Rami principali e sotto-concetti
    for ramo in struttura["rami"]:
        concetto = ramo["concetto"]

        # Nodo ramo principale (livello 2) — viola
        rete.add_node(
            concetto,
            label=concetto,
            color="#9b59b6",
            size=30,
            shape="ellipse",
            font={"size": 15, "color": "white"}
        )

        # Collegamento centrale → ramo
        rete.add_edge(concetto_centrale, concetto)

        # Sotto-concetti (livello 3) — verdi
        for sotto in ramo.get("sotto_concetti", []):
            rete.add_node(
                sotto,
                label=sotto,
                color="#2ecc71",
                size=20,
                shape="ellipse",
                font={"size": 13, "color": "white"}
            )
            rete.add_edge(concetto, sotto)

    # Salvo la mappa come file HTML interattivo
    rete.save_graph(percorso_output)
    print(f"Mappa salvata in: {percorso_output}")


# Questo blocco viene eseguito solo se avviamo direttamente questo file
if __name__ == "__main__":
    testo = input("Inserisci il testo: ")
    genera_mappa(testo)
    os.startfile("mappa.html")
