# ============================================================
# ReadAbile - Modulo Mappa Visiva (versione D3.js tree layout)
# Layout gerarchico top-down come Algor Maps
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
Crea massimo 3 rami principali e massimo 3 sotto-concetti per ramo.

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
                "content": "Sei un esperto di mappe concettuali. Rispondi sempre e solo con JSON valido. Usa massimo 3 rami e 3 sotto-concetti per ramo. Tieni i testi brevi (massimo 4 parole per nodo)."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_tokens=800
    )

    testo_risposta = risposta.choices[0].message.content.strip()
    struttura = json.loads(testo_risposta)
    return struttura


def genera_mappa(testo, percorso_output="static/mappa.html"):
    """
    Genera una mappa concettuale gerarchica con D3.js tree layout.
    - Layout top-down ordinato
    - Nodi ben spaziati
    - Font OpenDyslexic
    - Switch tema chiaro/scuro
    - Auto-adattamento alla dimensione del contenuto
    """

    print("Analizzo il testo con LLaMA 3...")
    struttura = estrai_struttura_mappa(testo)
    print(f"Struttura generata: {struttura['concetto_centrale']}")

    # Costruisco struttura ad albero
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
  body.light {{ background: #f5f7ff; }}

  svg {{ display: block; }}

  /* LINK */
  .link {{
    fill: none;
    stroke-width: 2px;
    stroke-opacity: 0.7;
  }}

  /* NODI */
  .node rect {{
    rx: 12;
    ry: 12;
    stroke-width: 2.5px;
    cursor: pointer;
    transition: filter 0.2s;
  }}

  .node:hover rect {{
    filter: brightness(1.15) drop-shadow(0 4px 16px rgba(255,255,255,0.15));
  }}

  .node text {{
    pointer-events: none;
    font-family: 'OpenDyslexic', 'Segoe UI', sans-serif;
    dominant-baseline: middle;
    text-anchor: middle;
  }}

  /* SWITCH TEMA */
  .theme-btn {{
    position: fixed;
    top: 12px;
    right: 12px;
    z-index: 100;
    background: rgba(255,255,255,0.12);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 50px;
    padding: 7px 16px;
    cursor: pointer;
    font-family: 'OpenDyslexic', sans-serif;
    font-size: 12px;
    color: white;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.3s;
    user-select: none;
  }}

  body.light .theme-btn {{
    background: rgba(0,0,0,0.07);
    border-color: rgba(0,0,0,0.12);
    color: #333;
  }}

  .theme-btn:hover {{ transform: scale(1.05); }}

  /* LEGENDA */
  .legenda {{
    position: fixed;
    bottom: 12px;
    left: 12px;
    z-index: 100;
    background: rgba(0,0,0,0.45);
    backdrop-filter: blur(8px);
    border-radius: 12px;
    padding: 10px 14px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }}

  body.light .legenda {{ background: rgba(255,255,255,0.85); box-shadow: 0 2px 12px rgba(0,0,0,0.1); }}

  .leg-item {{ display: flex; align-items: center; gap: 8px; font-size: 11px; font-family: 'OpenDyslexic', sans-serif; }}
  body.dark  .leg-item {{ color: #ccc; }}
  body.light .leg-item {{ color: #444; }}

  .leg-dot {{ width: 13px; height: 13px; border-radius: 3px; flex-shrink: 0; }}

  /* TOOLTIP */
  .tooltip {{
    position: fixed;
    background: rgba(10,10,30,0.95);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 11px;
    font-family: 'OpenDyslexic', sans-serif;
    color: white;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.15s;
    z-index: 200;
    max-width: 200px;
  }}
</style>
</head>
<body class="dark">

<div class="theme-btn" onclick="toggleTema()" id="themeBtn">
  <span id="themeIcon">☀️</span>
  <span id="themeLabel">Tema chiaro</span>
</div>

<div class="legenda">
  <div class="leg-item"><div class="leg-dot" style="background:#4a9eff"></div>Concetto centrale</div>
  <div class="leg-item"><div class="leg-dot" style="background:#9b59b6"></div>Argomenti principali</div>
  <div class="leg-item"><div class="leg-dot" style="background:#2ecc71"></div>Dettagli</div>
</div>

<div class="tooltip" id="tooltip"></div>
<svg id="mappa"></svg>

<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>
const datiAlbero = {dati_json};

// Colori per livello — dark e light
const CFG = {{
  0: {{ dark: {{ fill:"#1a4f8a", stroke:"#4a9eff", text:"#e8f4ff" }}, light: {{ fill:"#4a9eff", stroke:"#1a6bab", text:"white" }}, padX:28, padY:14, fs:13 }},
  1: {{ dark: {{ fill:"#4a1a6a", stroke:"#9b59b6", text:"#f0e0ff" }}, light: {{ fill:"#9b59b6", stroke:"#6c3483", text:"white" }}, padX:22, padY:12, fs:12 }},
  2: {{ dark: {{ fill:"#0d4a2a", stroke:"#2ecc71", text:"#d0ffe8" }}, light: {{ fill:"#2ecc71", stroke:"#1a8a4a", text:"white" }}, padX:18, padY:10, fs:11 }},
}};

const NODE_SEP   = 40;   // spazio orizzontale tra nodi fratelli
const LEVEL_SEP  = 100;  // spazio verticale tra livelli
const MARGIN     = 60;   // margine bordi

let temaDark = true;

// Calcolo dimensione testo
function misuratesto(testo, fs) {{
  const canvas = document.createElement("canvas");
  const ctx    = canvas.getContext("2d");
  ctx.font     = `${{fs}}px OpenDyslexic, Segoe UI`;
  return ctx.measureText(testo).width;
}}

// Calcolo larghezza nodo (basata sul testo)
function nodW(d) {{
  const c = CFG[d.data.livello];
  return Math.max(misuratesto(d.data.nome, c.fs) + c.padX * 2, 80);
}}

function nodH(d) {{
  return CFG[d.data.livello].fs * 2 + CFG[d.data.livello].padY * 2;
}}

// Costruisco gerarchia
const root = d3.hierarchy(datiAlbero);

// Layout custom top-down con spaziatura adattiva
function layoutAlbero(root) {{
  // Calcolo larghezze nodi
  root.each(d => {{
    d.w = nodW(d);
    d.h = nodH(d);
  }});

  // Calcolo posizioni ricorsivamente
  function calcolaX(node) {{
    if (!node.children || node.children.length === 0) {{
      return node.w;
    }}
    node.children.forEach(calcolaX);
    const totW = node.children.reduce((s,c) => s + c.subtreeW, 0)
               + NODE_SEP * (node.children.length - 1);
    node.subtreeW = Math.max(totW, node.w);
    return node.subtreeW;
  }}

  calcolaX(root);

  function assegnaXY(node, startX, depth) {{
    node.y = MARGIN + depth * (80 + LEVEL_SEP);

    if (!node.children || node.children.length === 0) {{
      node.x = startX + node.subtreeW / 2;
      return;
    }}

    let curX = startX;
    node.children.forEach(child => {{
      assegnaXY(child, curX, depth + 1);
      curX += child.subtreeW + NODE_SEP;
    }});

    const firstX = node.children[0].x;
    const lastX  = node.children[node.children.length - 1].x;
    node.x = (firstX + lastX) / 2;
  }}

  assegnaXY(root, MARGIN, 0);
}}

layoutAlbero(root);

// Dimensioni totali
const allNodes = root.descendants();
const maxX = d3.max(allNodes, d => d.x + d.w / 2) + MARGIN;
const maxY = d3.max(allNodes, d => d.y + d.h) + MARGIN;

const svg = d3.select("#mappa")
  .attr("width",  maxX)
  .attr("height", maxY)
  .attr("viewBox", `0 0 ${{maxX}} ${{maxY}}`);

// Zoom/pan
const g = svg.append("g");
svg.call(d3.zoom()
  .scaleExtent([0.3, 3])
  .on("zoom", e => g.attr("transform", e.transform))
);

// Fit iniziale nella finestra
const scaleX = window.innerWidth  / maxX;
const scaleY = window.innerHeight / maxY;
const scale  = Math.min(scaleX, scaleY) * 0.9;
const tx     = (window.innerWidth  - maxX * scale) / 2;
const ty     = (window.innerHeight - maxY * scale) / 2;
svg.attr("width", "100%").attr("height", "100vh");
svg.call(d3.zoom().transform, d3.zoomIdentity.translate(tx, ty).scale(scale));
g.attr("transform", `translate(${{tx}},${{ty}}) scale(${{scale}})`);

// Disegno connessioni (linee verticali → orizzontali)
function pathLink(s, t) {{
  const midY = (s.y + s.h + t.y) / 2;
  return `M${{s.x}},${{s.y + s.h}} L${{s.x}},${{midY}} L${{t.x}},${{midY}} L${{t.x}},${{t.y}}`;
}}

const linkEls = g.append("g")
  .selectAll("path")
  .data(root.links())
  .join("path")
  .attr("class", "link")
  .attr("stroke", "#4a9eff")
  .attr("d", d => pathLink(d.source, d.target));

// Disegno nodi
const nodeEls = g.append("g")
  .selectAll("g")
  .data(allNodes)
  .join("g")
  .attr("class", "node")
  .attr("transform", d => `translate(${{d.x - d.w/2}},${{d.y}})`)
  .call(d3.drag()
    .on("drag", function(e, d) {{
      d.x += e.dx;
      d.y += e.dy;
      d3.select(this).attr("transform", `translate(${{d.x - d.w/2}},${{d.y}})`);
      linkEls.attr("d", dd => pathLink(dd.source, dd.target));
    }})
  );

// Rettangoli
nodeEls.append("rect")
  .attr("width",  d => d.w)
  .attr("height", d => d.h)
  .attr("rx", 12)
  .attr("ry", 12)
  .attr("fill",   d => CFG[d.data.livello].dark.fill)
  .attr("stroke", d => CFG[d.data.livello].dark.stroke);

// Testo
nodeEls.append("text")
  .attr("x", d => d.w / 2)
  .attr("y", d => d.h / 2)
  .attr("fill", d => CFG[d.data.livello].dark.text)
  .attr("font-size", d => CFG[d.data.livello].fs + "px")
  .text(d => d.data.nome);

// Tooltip per testi lunghi
const tooltip = d3.select("#tooltip");
nodeEls
  .on("mouseover", (e, d) => {{
    tooltip.style("opacity", 1)
      .style("left", (e.clientX + 12) + "px")
      .style("top",  (e.clientY - 10) + "px")
      .text(d.data.nome);
  }})
  .on("mouseout", () => tooltip.style("opacity", 0));

// Toggle tema
function toggleTema() {{
  temaDark = !temaDark;
  document.body.className = temaDark ? "dark" : "light";
  document.getElementById("themeIcon").textContent  = temaDark ? "☀️" : "🌙";
  document.getElementById("themeLabel").textContent = temaDark ? "Tema chiaro" : "Tema scuro";

  const tema = temaDark ? "dark" : "light";

  nodeEls.selectAll("rect")
    .attr("fill",   d => CFG[d.data.livello][tema].fill)
    .attr("stroke", d => CFG[d.data.livello][tema].stroke);

  nodeEls.selectAll("text")
    .attr("fill", d => CFG[d.data.livello][tema].text);

  linkEls.attr("stroke", temaDark ? "#4a9eff" : "#1a6bab");
}}
</script>
</body>
</html>"""

    with open(percorso_output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Mappa D3 salvata in: {percorso_output}")


if __name__ == "__main__":
    testo = input("Inserisci il testo: ")
    genera_mappa(testo)
    import webbrowser
    webbrowser.open("static/mappa.html")
