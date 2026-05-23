# ============================================================
# ReadAbile - Modulo Mappa Visiva (versione D3.js)
# Layout gerarchico top-down usando d3.tree() ufficiale
# ============================================================

import os
from dotenv import load_dotenv
from groq import Groq
import json

load_dotenv("credenziali.env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)


def estrai_struttura_mappa(testo):
    prompt = f"""Analizza questo testo e crea una mappa concettuale gerarchica.
Rispondi SOLO con un JSON valido, senza spiegazioni, senza markdown, senza backtick.
Crea massimo 4 rami principali e massimo 3 sotto-concetti per ramo.
I testi dei nodi devono essere BREVI: massimo 4 parole per nodo.

Il JSON deve avere questa struttura:
{{
  "concetto_centrale": "tema principale",
  "rami": [
    {{
      "concetto": "argomento 1",
      "sotto_concetti": ["dettaglio 1", "dettaglio 2"]
    }}
  ]
}}

Testo da analizzare:
{testo}"""

    risposta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Sei un esperto di mappe concettuali. Rispondi sempre e solo con JSON valido. Testi brevi: max 4 parole per nodo."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=800
    )

    testo_risposta = risposta.choices[0].message.content.strip()
    struttura = json.loads(testo_risposta)
    return struttura


def genera_mappa(testo, percorso_output="static/mappa.html"):
    print("Analizzo il testo con LLaMA 3...")
    struttura = estrai_struttura_mappa(testo)
    print(f"Struttura generata: {struttura['concetto_centrale']}")

    # Struttura ad albero per D3
    albero = {
        "name": struttura["concetto_centrale"],
        "level": 0,
        "children": []
    }

    for ramo in struttura["rami"]:
        nodo = {
            "name": ramo["concetto"],
            "level": 1,
            "children": [
                {"name": s, "level": 2, "children": []}
                for s in ramo.get("sotto_concetti", [])
            ]
        }
        albero["children"].append(nodo)

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
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{ width:100%; height:100%; overflow:hidden; }}
  body {{ background:#0d0d1a; font-family:'OpenDyslexic','Segoe UI',sans-serif; transition:background 0.3s; }}
  body.light {{ background:#f0f4ff; }}

  svg {{ position:absolute; top:0; left:0; }}

  .link {{
    fill: none;
    stroke: #4a9eff;
    stroke-width: 2px;
    stroke-opacity: 0.6;
  }}
  body.light .link {{ stroke: #1a6bab; }}

  .node rect {{
    rx: 10; ry: 10;
    stroke-width: 2px;
    cursor: grab;
    filter: drop-shadow(0 3px 8px rgba(0,0,0,0.4));
  }}
  .node rect:active {{ cursor: grabbing; }}
  .node:hover rect {{ filter: drop-shadow(0 5px 16px rgba(255,255,255,0.2)) brightness(1.1); }}

  .node text {{
    font-family: 'OpenDyslexic','Segoe UI',sans-serif;
    pointer-events: none;
    dominant-baseline: central;
    text-anchor: middle;
  }}

  .controls {{
    position: fixed;
    top: 12px;
    right: 12px;
    z-index: 100;
    display: flex;
    gap: 8px;
  }}

  .ctrl-btn {{
    background: rgba(255,255,255,0.1);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 50px;
    padding: 7px 16px;
    cursor: pointer;
    font-family: 'OpenDyslexic',sans-serif;
    font-size: 12px;
    color: white;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s;
    user-select: none;
  }}
  body.light .ctrl-btn {{ background:rgba(0,0,0,0.07); border-color:rgba(0,0,0,0.15); color:#333; }}
  .ctrl-btn:hover {{ transform: scale(1.05); }}

  .legenda {{
    position: fixed;
    bottom: 12px;
    left: 12px;
    z-index: 100;
    background: rgba(0,0,0,0.5);
    backdrop-filter: blur(8px);
    border-radius: 12px;
    padding: 10px 14px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }}
  body.light .legenda {{ background:rgba(255,255,255,0.9); box-shadow:0 2px 12px rgba(0,0,0,0.1); }}
  .leg {{ display:flex; align-items:center; gap:8px; font-size:11px; }}
  body.dark .leg, .leg {{ color:#ccc; }}
  body.light .leg {{ color:#444; }}
  .leg-sq {{ width:14px; height:14px; border-radius:4px; flex-shrink:0; }}

  .hint {{
    position: fixed;
    bottom: 12px;
    right: 12px;
    z-index: 100;
    font-size: 10px;
    color: rgba(255,255,255,0.3);
    font-family: 'OpenDyslexic',sans-serif;
  }}
  body.light .hint {{ color:rgba(0,0,0,0.3); }}
</style>
</head>
<body class="dark">

<div class="controls">
  <div class="ctrl-btn" onclick="toggleTema()">
    <span id="themeIcon">☀️</span>
    <span id="themeLabel">Tema chiaro</span>
  </div>
  <div class="ctrl-btn" onclick="resetZoom()">🔍 Reset zoom</div>
</div>

<div class="legenda">
  <div class="leg"><div class="leg-sq" style="background:#4a9eff"></div>Concetto centrale</div>
  <div class="leg"><div class="leg-sq" style="background:#9b59b6"></div>Argomenti principali</div>
  <div class="leg"><div class="leg-sq" style="background:#27ae60"></div>Dettagli</div>
</div>

<div class="hint">Scorri per zoomare · Trascina per muovere</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>
const DATA = {dati_json};

// Colori nodi per livello
const COLORS = {{
  dark: [
    {{ fill:'#1a5276', stroke:'#4a9eff', text:'#d6eaf8' }},
    {{ fill:'#512e5f', stroke:'#9b59b6', text:'#e8daef' }},
    {{ fill:'#145a32', stroke:'#27ae60', text:'#d5f5e3' }},
  ],
  light: [
    {{ fill:'#2980b9', stroke:'#1a5276', text:'white' }},
    {{ fill:'#8e44ad', stroke:'#512e5f', text:'white' }},
    {{ fill:'#27ae60', stroke:'#145a32', text:'white' }},
  ]
}};

// Padding nodi
const PAD = [
  {{ x:24, y:14, fs:14 }},
  {{ x:20, y:12, fs:12 }},
  {{ x:16, y:10, fs:11 }},
];

const W = window.innerWidth;
const H = window.innerHeight;

const svg = d3.select("body").append("svg")
  .attr("width", W)
  .attr("height", H);

// Zoom/pan sul gruppo principale
const gZoom = svg.append("g");
const zoom = d3.zoom().scaleExtent([0.15, 4]).on("zoom", e => gZoom.attr("transform", e.transform));
svg.call(zoom);

// Gerarchia e layout
const root = d3.hierarchy(DATA);

// Calcolo dimensioni nodi PRIMA del layout
function nodeSize(d) {{
  const lv = Math.min(d.data.level, 2);
  const p  = PAD[lv];
  const fs = p.fs;
  // Stima larghezza testo
  const words = d.data.name.split(" ");
  const maxW  = Math.max(...words.map(w => w.length)) * fs * 0.62;
  const lineW = d.data.name.length * fs * 0.52;
  const w     = Math.min(lineW, 180) + p.x * 2;
  const lines = Math.ceil(d.data.name.length / 14);
  const h     = lines * (fs + 4) + p.y * 2;
  return {{ w: Math.max(w, 80), h: Math.max(h, fs + p.y * 2) }};
}}

root.each(d => {{ const s = nodeSize(d); d.nw = s.w; d.nh = s.h; }});

// Layout tidy tree con nodeSize
const treeLayout = d3.tree()
  .nodeSize([0, 120])  // altezza livello 120px
  .separation((a, b) => {{
    const aw = a.nw / 2 + 20;
    const bw = b.nw / 2 + 20;
    return (aw + bw) / (a.parent === b.parent ? 80 : 100);
  }});

treeLayout(root);

// Normalizzo X: D3 tree usa x per orizzontale, y per profondità
// Converto: voglio top-down quindi scambio x↔y
root.each(d => {{
  const tmp = d.x;
  d.tx = d.y;  // profondità → verticale
  d.ty = tmp;  // posizione fratelli → orizzontale
}});

// Calcolo bounding box
const xs = root.descendants().map(d => d.ty);
const ys = root.descendants().map(d => d.tx);
const minX = Math.min(...xs) - 200;
const maxX = Math.max(...xs) + 200;
const minY = Math.min(...ys) - 80;
const maxY = Math.max(...ys) + 80;
const totalW = maxX - minX;
const totalH = maxY - minY;

// Offset per centrare
const offX = -minX;
const offY = -minY + 40;

// Fit iniziale
const scaleInit = Math.min(W / (totalW + 80), H / (totalH + 80), 1) * 0.9;
const tx0 = (W - totalW * scaleInit) / 2 - minX * scaleInit;
const ty0 = (H - totalH * scaleInit) / 2 - minY * scaleInit + 20;
svg.call(zoom.transform, d3.zoomIdentity.translate(tx0, ty0).scale(scaleInit));

let temaDark = true;

// Linee di connessione (bezier verticale)
function linkPath(s, t) {{
  const sx = s.ty + offX, sy = s.tx + s.nh/2 + offY;
  const tx = t.ty + offX, ty = t.tx - t.nh/2 + offY;
  const midY = (sy + ty) / 2;
  return `M${{sx}},${{sy}} C${{sx}},${{midY}} ${{tx}},${{midY}} ${{tx}},${{ty}}`;
}}

const gLinks = gZoom.append("g");
const linkEls = gLinks.selectAll("path")
  .data(root.links())
  .join("path")
  .attr("class", "link")
  .attr("d", d => linkPath(d.source, d.target));

// Nodi
const gNodes = gZoom.append("g");
const nodeEls = gNodes.selectAll("g")
  .data(root.descendants())
  .join("g")
  .attr("class", "node")
  .attr("transform", d => `translate(${{d.ty + offX - d.nw/2}},${{d.tx - d.nh/2 + offY}})`)
  .call(d3.drag()
    .on("drag", function(e, d) {{
      d.ty += e.dx;
      d.tx += e.dy;
      d3.select(this).attr("transform", `translate(${{d.ty + offX - d.nw/2}},${{d.tx - d.nh/2 + offY}})`);
      linkEls.attr("d", dd => linkPath(dd.source, dd.target));
    }})
  );

// Rettangoli
nodeEls.append("rect")
  .attr("width",  d => d.nw)
  .attr("height", d => d.nh)
  .attr("fill",   d => COLORS.dark[Math.min(d.data.level,2)].fill)
  .attr("stroke", d => COLORS.dark[Math.min(d.data.level,2)].stroke);

// Testo con wrapping
nodeEls.each(function(d) {{
  const lv   = Math.min(d.data.level, 2);
  const fs   = PAD[lv].fs;
  const name = d.data.name;
  const maxCharsPerLine = Math.floor((d.nw - PAD[lv].x * 2) / (fs * 0.55));
  const words = name.split(" ");
  const lines = [];
  let line = "";
  words.forEach(w => {{
    const test = line ? line + " " + w : w;
    if (test.length > maxCharsPerLine && line) {{
      lines.push(line);
      line = w;
    }} else {{
      line = test;
    }}
  }});
  if (line) lines.push(line);

  const el = d3.select(this).append("text")
    .attr("fill", COLORS.dark[lv].text)
    .attr("font-size", fs + "px");

  const totalH2 = lines.length * (fs + 4);
  const startY  = (d.nh - totalH2) / 2 + fs / 2 + 2;

  lines.forEach((l, i) => {{
    el.append("tspan")
      .attr("x", d.nw / 2)
      .attr("y", startY + i * (fs + 4))
      .text(l);
  }});
}});

// Toggle tema
function toggleTema() {{
  temaDark = !temaDark;
  document.body.className = temaDark ? "dark" : "light";
  document.getElementById("themeIcon").textContent  = temaDark ? "☀️" : "🌙";
  document.getElementById("themeLabel").textContent = temaDark ? "Tema chiaro" : "Tema scuro";

  const tema = temaDark ? "dark" : "light";
  nodeEls.selectAll("rect")
    .attr("fill",   d => COLORS[tema][Math.min(d.data.level,2)].fill)
    .attr("stroke", d => COLORS[tema][Math.min(d.data.level,2)].stroke);
  nodeEls.selectAll("text")
    .attr("fill",   d => COLORS[tema][Math.min(d.data.level,2)].text);
  gLinks.selectAll(".link")
    .attr("stroke", temaDark ? "#4a9eff" : "#1a6bab");
}}

// Reset zoom
function resetZoom() {{
  svg.transition().duration(500)
    .call(zoom.transform, d3.zoomIdentity.translate(tx0, ty0).scale(scaleInit));
}}

window.addEventListener("resize", () => {{
  svg.attr("width", window.innerWidth).attr("height", window.innerHeight);
}});
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
