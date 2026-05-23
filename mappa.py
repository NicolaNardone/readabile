# ============================================================
# ReadAbile - Modulo Mappa Visiva (versione D3.js)
# Usa LLaMA 3.3 70B gratuito via Groq per analizzare il testo
# e genera una mappa concettuale gerarchica con D3.js
# ============================================================

import os
from dotenv import load_dotenv
from groq import Groq
import json

load_dotenv("credenziali.env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)


def estrai_struttura_mappa(testo):
    """
    Manda il testo a LLaMA 3 via Groq e chiede di restituire
    la struttura della mappa in formato JSON.
    """

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

    risposta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
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
        temperature=0.3,
        max_tokens=1000
    )

    testo_risposta = risposta.choices[0].message.content.strip()
    struttura = json.loads(testo_risposta)
    return struttura


def genera_mappa(testo, percorso_output="static/mappa.html"):
    """
    Genera una mappa concettuale gerarchica con D3.js.
    - Layout ad albero gerarchico (ordinato dall'inizio)
    - Font OpenDyslexic per accessibilità
    - Switch tema chiaro/scuro
    - Testo adattato alle dimensioni dei nodi
    """

    print("Analizzo il testo con LLaMA 3...")
    struttura = estrai_struttura_mappa(testo)
    print(f"Struttura generata: {struttura['concetto_centrale']}")

    # Costruisco struttura ad albero per D3.hierarchy
    albero = {
        "nome": struttura["concetto_centrale"],
        "livello": 0,
        "children": []
    }

    for ramo in struttura["rami"]:
        nodo_ramo = {
            "nome": ramo["concetto"],
            "livello": 1,
            "children": []
        }
        for sotto in ramo.get("sotto_concetti", []):
            nodo_ramo["children"].append({
                "nome": sotto,
                "livello": 2,
                "children": []
            })
        albero["children"].append(nodo_ramo)

    dati_json = json.dumps(albero, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<style>
  @font-face {{
    font-family: 'OpenDyslexic';
    src: url('https://cdn.jsdelivr.net/npm/open-dyslexic@1.0.3/open-dyslexic-regular.woff2') format('woff2');
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'OpenDyslexic', 'Segoe UI', sans-serif;
    overflow: hidden;
    transition: background 0.4s;
  }}

  body.dark  {{ background: #0d0d1a; }}
  body.light {{ background: #f0f4ff; }}

  /* SWITCH TEMA */
  .theme-switch {{
    position: fixed;
    top: 14px;
    right: 14px;
    z-index: 100;
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(255,255,255,0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 50px;
    padding: 6px 14px;
    cursor: pointer;
    font-size: 13px;
    font-family: 'OpenDyslexic', sans-serif;
    color: white;
    transition: all 0.3s;
    user-select: none;
  }}

  body.light .theme-switch {{
    background: rgba(0,0,0,0.08);
    border-color: rgba(0,0,0,0.15);
    color: #333;
  }}

  .theme-switch:hover {{ transform: scale(1.05); }}

  /* LEGENDA */
  .legenda {{
    position: fixed;
    bottom: 14px;
    left: 14px;
    z-index: 100;
    display: flex;
    flex-direction: column;
    gap: 6px;
    background: rgba(0,0,0,0.4);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 11px;
    font-family: 'OpenDyslexic', sans-serif;
  }}

  body.light .legenda {{
    background: rgba(255,255,255,0.8);
  }}

  .legenda-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    color: white;
  }}

  body.light .legenda-item {{ color: #333; }}

  .legenda-dot {{
    width: 14px;
    height: 14px;
    border-radius: 50%;
    flex-shrink: 0;
  }}

  /* LINKS */
  .link {{
    fill: none;
    stroke-width: 2.5px;
    stroke-opacity: 0.5;
  }}

  body.dark  .link {{ stroke: #4a9eff; }}
  body.light .link {{ stroke: #1a6bab; }}

  /* NODI */
  .node circle {{
    stroke-width: 3px;
    cursor: grab;
    transition: filter 0.2s;
  }}

  .node circle:active {{ cursor: grabbing; }}

  .node:hover circle {{
    filter: brightness(1.2) drop-shadow(0 0 12px rgba(255,255,255,0.3));
  }}

  .node text {{
    pointer-events: none;
    font-family: 'OpenDyslexic', 'Segoe UI', sans-serif;
    font-weight: 600;
  }}

  /* TOOLTIP */
  .tooltip {{
    position: fixed;
    background: rgba(10,10,30,0.95);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 12px;
    font-family: 'OpenDyslexic', sans-serif;
    color: white;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.15s;
    max-width: 220px;
    word-wrap: break-word;
    z-index: 200;
  }}
</style>
</head>
<body class="dark">

<div class="theme-switch" onclick="toggleTema()">
  <span id="temaIcon">☀️</span>
  <span id="temaLabel">Tema chiaro</span>
</div>

<div class="legenda">
  <div class="legenda-item">
    <div class="legenda-dot" style="background:#4a9eff"></div>
    <span>Concetto centrale</span>
  </div>
  <div class="legenda-item">
    <div class="legenda-dot" style="background:#9b59b6"></div>
    <span>Argomenti principali</span>
  </div>
  <div class="legenda-item">
    <div class="legenda-dot" style="background:#2ecc71"></div>
    <span>Dettagli</span>
  </div>
</div>

<div class="tooltip" id="tooltip"></div>
<svg id="mappa" width="100%" height="100vh"></svg>

<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>
const datiAlbero = {dati_json};

// Configurazione nodi per livello
const cfg = {{
  0: {{ fill: "#4a9eff", stroke: "#7ab8ff", fillLight: "#1a6bab", strokeLight: "#4a9eff", r: 70,  fs: 13 }},
  1: {{ fill: "#9b59b6", stroke: "#c27de8", fillLight: "#7d3c98", strokeLight: "#9b59b6", r: 52,  fs: 11 }},
  2: {{ fill: "#2ecc71", stroke: "#55e898", fillLight: "#1a8a4a", strokeLight: "#2ecc71", r: 40,  fs: 10 }},
}};

const svg    = d3.select("#mappa");
const width  = window.innerWidth;
const height = window.innerHeight;
svg.attr("viewBox", [0, 0, width, height]);

// Frecce per i link
const defs = svg.append("defs");
[0,1,2].forEach(liv => {{
  ["dark","light"].forEach(tema => {{
    defs.append("marker")
      .attr("id", `arrow-${{liv}}-${{tema}}`)
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", cfg[Math.min(liv+1,2)].r + 10)
      .attr("refY", 0)
      .attr("markerWidth", 7)
      .attr("markerHeight", 7)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", tema === "dark"
        ? cfg[Math.min(liv+1,2)].stroke
        : cfg[Math.min(liv+1,2)].strokeLight);
  }});
}});

// Gruppo principale con zoom/pan
const g = svg.append("g");
svg.call(d3.zoom()
  .scaleExtent([0.2, 4])
  .on("zoom", e => g.attr("transform", e.transform))
);

// Layout radiale (più ordinato dall'inizio)
const root = d3.hierarchy(datiAlbero);
const layout = d3.tree()
  .size([2 * Math.PI, Math.min(width, height) * 0.38])
  .separation((a, b) => (a.parent === b.parent ? 1.2 : 2.5) / a.depth);

layout(root);

// Converto coordinate polari in cartesiane
const cx = width  / 2;
const cy = height / 2;

root.each(d => {{
  d.x0 = d.x;
  d.y0 = d.y;
  d.px = cx + d.y * Math.cos(d.x - Math.PI / 2);
  d.py = cy + d.y * Math.sin(d.x - Math.PI / 2);
}});

// Disegno links
const linkGen = d3.linkRadial()
  .angle(d => d.x)
  .radius(d => d.y);

let temaDark = true;

const linkEls = g.append("g")
  .selectAll("path")
  .data(root.links())
  .join("path")
  .attr("class", "link")
  .attr("transform", `translate(${{cx}},${{cy}})`)
  .attr("d", linkGen)
  .attr("marker-end", d => `url(#arrow-${{d.source.data.livello}}-dark)`);

// Disegno nodi
const nodeEls = g.append("g")
  .selectAll("g")
  .data(root.descendants())
  .join("g")
  .attr("class", "node")
  .attr("transform", d => `translate(${{d.px}},${{d.py}})`)
  .call(d3.drag()
    .on("start", function(e, d) {{ d.dragging = true; }})
    .on("drag",  function(e, d) {{
      d.px = e.x; d.py = e.y;
      d3.select(this).attr("transform", `translate(${{e.x}},${{e.y}})`);
      linkEls.attr("d", dd => {{
        if (dd.source === d || dd.target === d) {{
          return `M${{dd.source.px}},${{dd.source.py}}L${{dd.target.px}},${{dd.target.py}}`;
        }}
        return null;
      }});
    }})
    .on("end", function(e, d) {{ d.dragging = false; }})
  );

// Cerchi
nodeEls.append("circle")
  .attr("r", d => cfg[d.data.livello].r)
  .attr("fill", d => cfg[d.data.livello].fill)
  .attr("stroke", d => cfg[d.data.livello].stroke);

// Testo nei nodi con a capo automatico
nodeEls.append("text")
  .attr("text-anchor", "middle")
  .attr("fill", "white")
  .attr("font-size", d => cfg[d.data.livello].fs + "px")
  .each(function(d) {{
    const el   = d3.select(this);
    const r    = cfg[d.data.livello].r * 1.6;
    const fs   = cfg[d.data.livello].fs;
    const nome = d.data.nome;
    const parole = nome.split(" ");
    const righe  = [];
    let   riga   = "";

    parole.forEach(p => {{
      const test = riga ? riga + " " + p : p;
      if (test.length * fs * 0.58 > r) {{
        if (riga) righe.push(riga);
        riga = p;
      }} else {{
        riga = test;
      }}
    }});
    if (riga) righe.push(riga);

    const altezzaTot = righe.length * (fs + 3);
    righe.forEach((r, i) => {{
      el.append("tspan")
        .attr("x", 0)
        .attr("y", -altezzaTot / 2 + i * (fs + 3) + fs)
        .text(r);
    }});
  }});

// Tooltip
const tooltip = d3.select("#tooltip");
nodeEls
  .on("mouseover", (e, d) => {{
    tooltip
      .style("opacity", 1)
      .style("left", (e.clientX + 14) + "px")
      .style("top",  (e.clientY - 14) + "px")
      .text(d.data.nome);
  }})
  .on("mouseout", () => tooltip.style("opacity", 0));

// Toggle tema chiaro/scuro
function toggleTema() {{
  temaDark = !temaDark;
  const body = document.body;

  if (temaDark) {{
    body.className = "dark";
    document.getElementById("temaIcon").textContent  = "☀️";
    document.getElementById("temaLabel").textContent = "Tema chiaro";
    nodeEls.selectAll("circle")
      .attr("fill",   d => cfg[d.data.livello].fill)
      .attr("stroke", d => cfg[d.data.livello].stroke);
    nodeEls.selectAll("text").attr("fill", "white");
    linkEls
      .attr("stroke", "#4a9eff")
      .attr("marker-end", d => `url(#arrow-${{d.source.data.livello}}-dark)`);
  }} else {{
    body.className = "light";
    document.getElementById("temaIcon").textContent  = "🌙";
    document.getElementById("temaLabel").textContent = "Tema scuro";
    nodeEls.selectAll("circle")
      .attr("fill",   d => cfg[d.data.livello].fillLight)
      .attr("stroke", d => cfg[d.data.livello].strokeLight);
    nodeEls.selectAll("text").attr("fill", "white");
    linkEls
      .attr("stroke", "#1a6bab")
      .attr("marker-end", d => `url(#arrow-${{d.source.data.livello}}-light)`);
  }}
}}
</script>
</body>
</html>"""

    with open(percorso_output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Mappa D3 salvata in: {percorso_output}")


# Questo blocco viene eseguito solo se avviamo direttamente questo file
if __name__ == "__main__":
    testo = input("Inserisci il testo: ")
    genera_mappa(testo)
    os.startfile("static/mappa.html")
