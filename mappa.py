# ============================================================
# ReadAbile - Modulo Mappa Visiva (versione Groq + LLaMA)
# Usa LLaMA 3.3 70B gratuito via Groq per analizzare il testo
# e generare una mappa concettuale gerarchica intelligente.
# ============================================================

import os                          # gestione file e variabili di sistema
from dotenv import load_dotenv     # lettura chiavi API dal file credenziali.env
from groq import Groq              # client per le API di Groq (LLaMA 3)
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


def genera_mappa(testo, percorso_output="static/mappa.html"):
    """
    Genera una mappa concettuale con D3.js.
    Salva il JSON e l'HTML con la visualizzazione D3.
    """

    print("Analizzo il testo con LLaMA 3...")
    struttura = estrai_struttura_mappa(testo)
    print(f"Struttura generata: {struttura['concetto_centrale']}")

    # Converto la struttura in formato D3 (nodi e links)
    nodi = []
    links = []
    id_counter = [0]

    def aggiungi_nodo(nome, livello, parent_id=None):
        node_id = id_counter[0]
        id_counter[0] += 1
        nodi.append({
            "id": node_id,
            "nome": nome,
            "livello": livello
        })
        if parent_id is not None:
            links.append({
                "source": parent_id,
                "target": node_id
            })
        return node_id

    # Nodo centrale
    id_centrale = aggiungi_nodo(struttura["concetto_centrale"], 0)

    # Rami e sotto-concetti
    for ramo in struttura["rami"]:
        id_ramo = aggiungi_nodo(ramo["concetto"], 1, id_centrale)
        for sotto in ramo.get("sotto_concetti", []):
            aggiungi_nodo(sotto, 2, id_ramo)

    # Salvo il JSON
    dati_mappa = json.dumps({"nodi": nodi, "links": links})

    # Genero l'HTML con D3.js
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #0d0d1a; overflow: hidden; font-family: 'Segoe UI', sans-serif; }}

  .node circle {{
    stroke-width: 3px;
    filter: drop-shadow(0 4px 12px rgba(0,0,0,0.5));
    cursor: pointer;
    transition: r 0.2s;
  }}

  .node text {{
    pointer-events: none;
    font-weight: 600;
    text-shadow: 0 2px 4px rgba(0,0,0,0.8);
  }}

  .link {{
    fill: none;
    stroke-opacity: 0.6;
    stroke-width: 2px;
  }}

  .node:hover circle {{
    stroke-opacity: 1;
    filter: drop-shadow(0 6px 20px rgba(255,255,255,0.2));
  }}

  .tooltip {{
    position: absolute;
    background: rgba(20,20,40,0.95);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    color: white;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.2s;
    max-width: 200px;
    word-wrap: break-word;
  }}
</style>
</head>
<body>
<div class="tooltip" id="tooltip"></div>
<svg id="mappa" width="100%" height="100vh"></svg>

<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>
const dati = {dati_mappa};

const colori = {{
  0: {{ fill: "#4a9eff", stroke: "#7ab8ff", text: "white", r: 55 }},
  1: {{ fill: "#9b59b6", stroke: "#c27de8", text: "white", r: 40 }},
  2: {{ fill: "#2ecc71", stroke: "#55e898", text: "white", r: 30 }},
}};

const svg = d3.select("#mappa");
const width  = window.innerWidth;
const height = window.innerHeight;
svg.attr("viewBox", [0, 0, width, height]);

// Definisco frecce
const defs = svg.append("defs");
[0,1,2].forEach(liv => {{
  defs.append("marker")
    .attr("id", "arrow" + liv)
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", colori[liv].r + 8)
    .attr("refY", 0)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
    .append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", colori[Math.min(liv+1,2)].stroke);
}});

// Gruppo zoom/pan
const g = svg.append("g");
svg.call(d3.zoom()
  .scaleExtent([0.3, 3])
  .on("zoom", e => g.attr("transform", e.transform))
);

// Simulazione fisica
const sim = d3.forceSimulation(dati.nodi)
  .force("link", d3.forceLink(dati.links)
    .id(d => d.id)
    .distance(d => {{
      const src = dati.nodi[d.source.index ?? d.source];
      return src && src.livello === 0 ? 200 : 140;
    }})
    .strength(0.8)
  )
  .force("charge", d3.forceManyBody().strength(-400))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide().radius(d => colori[d.livello].r + 20));

// Links
const link = g.append("g").selectAll("line")
  .data(dati.links)
  .join("line")
  .attr("class", "link")
  .attr("stroke", d => {{
    const src = dati.nodi[d.source.index ?? d.source];
    return src ? colori[Math.min((src.livello || 0) + 1, 2)].stroke : "#666";
  }})
  .attr("marker-end", d => {{
    const src = dati.nodi[d.source.index ?? d.source];
    return src ? `url(#arrow${{src.livello || 0}})` : "url(#arrow0)";
  }});

// Nodi
const node = g.append("g").selectAll("g")
  .data(dati.nodi)
  .join("g")
  .attr("class", "node")
  .call(d3.drag()
    .on("start", (e, d) => {{ if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }})
    .on("drag",  (e, d) => {{ d.fx = e.x; d.fy = e.y; }})
    .on("end",   (e, d) => {{ if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }})
  );

// Cerchi
node.append("circle")
  .attr("r", d => colori[d.livello].r)
  .attr("fill", d => colori[d.livello].fill)
  .attr("stroke", d => colori[d.livello].stroke);

// Testo
node.append("text")
  .attr("text-anchor", "middle")
  .attr("dy", "0.35em")
  .attr("fill", d => colori[d.livello].text)
  .attr("font-size", d => d.livello === 0 ? "14px" : d.livello === 1 ? "12px" : "11px")
  .each(function(d) {{
    const el = d3.select(this);
    const r  = colori[d.livello].r;
    const parole = d.nome.split(" ");
    const righe = [];
    let riga = "";
    parole.forEach(p => {{
      if ((riga + " " + p).trim().length * 7 > r * 1.7) {{
        if (riga) righe.push(riga.trim());
        riga = p;
      }} else {{
        riga = (riga + " " + p).trim();
      }}
    }});
    if (riga) righe.push(riga.trim());
    const offset = -(righe.length - 1) * 8;
    righe.forEach((r, i) => {{
      el.append("tspan")
        .attr("x", 0)
        .attr("dy", i === 0 ? offset : 16)
        .text(r);
    }});
  }});

// Tooltip
const tooltip = d3.select("#tooltip");
node.on("mouseover", (e, d) => {{
  tooltip.style("opacity", 1)
    .style("left", (e.pageX + 12) + "px")
    .style("top",  (e.pageY - 28) + "px")
    .text(d.nome);
}}).on("mouseout", () => tooltip.style("opacity", 0));

// Aggiorno posizioni
sim.on("tick", () => {{
  link
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y);

  node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
}});
</script>
</body>
</html>"""

    # Salvo l'HTML
    with open(percorso_output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Mappa D3 salvata in: {percorso_output}")

# Questo blocco viene eseguito solo se avviamo direttamente questo file
if __name__ == "__main__":
    testo = input("Inserisci il testo: ")
    genera_mappa(testo)
    os.startfile("mappa.html")
