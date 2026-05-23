# ============================================================
# ReadAbile - Modulo Mappa Visiva (versione D3.js)
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
    prompt = f"""Sei un esperto di didattica scolastica. Analizza il testo e crea una mappa concettuale gerarchica come Algor Education.

REGOLE OBBLIGATORIE:
- Rispondi SOLO con JSON valido, zero testo aggiuntivo
- Il concetto centrale deve essere il titolo del testo (2-4 parole)
- Crea 3-5 macro-argomenti principali (es: "Struttura", "Cause", "Effetti", "Tipi")
- Per ogni macro-argomento crea 2-4 sotto-argomenti specifici e informativi
- I nodi devono essere concisi ma informativi: 2-6 parole
- Usa termini precisi presi dal testo originale
- I sotto-argomenti devono essere fatti e informazioni concrete, non categorie generiche

JSON richiesto:
{{
  "concetto_centrale": "Titolo argomento",
  "rami": [
    {{
      "concetto": "Macro-argomento 1",
      "sotto_concetti": ["fatto specifico 1", "fatto specifico 2", "fatto specifico 3"]
    }}
  ]
}}

Testo:
{testo}"""

    risposta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Sei un esperto di didattica che crea mappe concettuali per studenti delle scuole superiori italiane. Rispondi SEMPRE e SOLO con JSON valido. Mappe complete con 3-5 rami e 2-4 sotto-concetti informativi e specifici per ramo."
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
    print("Analizzo il testo con LLaMA 3...")
    struttura = estrai_struttura_mappa(testo)
    print(f"Struttura generata: {struttura['concetto_centrale']}")

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
  .node:hover rect {{
    filter: drop-shadow(0 5px 16px rgba(255,255,255,0.2)) brightness(1.1);
  }}
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
  .leg {{ display:flex; align-items:center; gap:8px; font-size:11px; color:#ccc; }}
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

const PAD = [
  {{ x:24, y:14, fs:14 }},
  {{ x:20, y:12, fs:12 }},
  {{ x:16, y:10, fs:11 }},
];

const W = window.innerWidth;
const H = window.innerHeight;

const svg = d3.select("body").append("svg").attr("width", W).attr("height", H);
const gZoom = svg.append("g");
const zoom = d3.zoom().scaleExtent([0.1, 4]).on("zoom", e => gZoom.attr("transform", e.transform));
svg.call(zoom);

const root = d3.hierarchy(DATA);

// Calcola dimensioni nodi
root.each(d => {{
  const lv = Math.min(d.data.level, 2);
  const p  = PAD[lv];
  const fs = p.fs;
  const name = d.data.name;
  const maxW = 200;
  const estW = name.length * fs * 0.52;
  const w    = Math.min(estW, maxW) + p.x * 2;
  const lines = Math.ceil(estW / maxW) || 1;
  const h    = lines * (fs + 4) + p.y * 2;
  d.nw = Math.max(w, 80);
  d.nh = Math.max(h, fs + p.y * 2);
}});

// Layout tree con separazione basata su larghezza nodi
const treeLayout = d3.tree()
  .nodeSize([220, 140])
  .separation((a, b) => {{
    const gap = a.nw / 2 + b.nw / 2 + 40;
    return gap / 110;
  }});

treeLayout(root);

// Converti coordinate: d3.tree usa x orizzontale, y profondità
// Vogliamo top-down: profondità → y, posizione fratelli → x
root.each(d => {{
  d.tx = d.y;   // profondità → verticale
  d.ty = d.x;   // posizione → orizzontale (scalata)
}});

// Scala le posizioni orizzontali
const allDesc = root.descendants();
const tyMin = d3.min(allDesc, d => d.ty);
const tyMax = d3.max(allDesc, d => d.ty);
const txMax = d3.max(allDesc, d => d.tx);

// Normalizza e aggiunge margine
const MARGIN = 80;
const scaleY = 1;
allDesc.forEach(d => {{
  d.tx = d.tx * scaleY + MARGIN;
  d.ty = d.ty + MARGIN + (tyMax - tyMin) / 2 * 0 ;
}});

const totalW = (tyMax - tyMin) + MARGIN * 4 + d3.max(allDesc, d => d.nw);
const totalH = txMax + MARGIN * 2 + d3.max(allDesc, d => d.nh);

// Fit iniziale
const scaleInit = Math.min(W / totalW, H / totalH) * 0.88;
const tx0 = (W - totalW * scaleInit) / 2;
const ty0 = (H - totalH * scaleInit) / 2;
svg.call(zoom.transform, d3.zoomIdentity.translate(tx0, ty0).scale(scaleInit));

let temaDark = true;

// Percorso connessione a L
function linkPath(s, t) {{
  const sx = s.ty, sy = s.tx + s.nh;
  const tx = t.ty, ty2 = t.tx;
  const midY = (sy + ty2) / 2;
  return `M${{sx}},${{sy}} C${{sx}},${{midY}} ${{tx}},${{midY}} ${{tx}},${{ty2}}`;
}}

// Links
const gLinks = gZoom.append("g");
const linkEls = gLinks.selectAll("path")
  .data(root.links())
  .join("path")
  .attr("class", "link")
  .attr("d", d => linkPath(d.source, d.target));

// Nodi
const gNodes = gZoom.append("g");
const nodeEls = gNodes.selectAll("g")
  .data(allDesc)
  .join("g")
  .attr("class", "node")
  .attr("transform", d => `translate(${{d.ty - d.nw/2}},${{d.tx}})`)
  .call(d3.drag()
    .on("drag", function(e, d) {{
      d.ty += e.dx;
      d.tx += e.dy;
      d3.select(this).attr("transform", `translate(${{d.ty - d.nw/2}},${{d.tx}})`);
      linkEls.attr("d", dd => linkPath(dd.source, dd.target));
    }})
  );

// Rettangoli
nodeEls.append("rect")
  .attr("width",  d => d.nw)
  .attr("height", d => d.nh)
  .attr("rx", 10).attr("ry", 10)
  .attr("fill",   d => COLORS.dark[Math.min(d.data.level,2)].fill)
  .attr("stroke", d => COLORS.dark[Math.min(d.data.level,2)].stroke);

// Testo con wrapping
nodeEls.each(function(d) {{
  const lv   = Math.min(d.data.level, 2);
  const fs   = PAD[lv].fs;
  const name = d.data.name;
  const maxChars = Math.floor((d.nw - PAD[lv].x * 2) / (fs * 0.55));
  const words = name.split(" ");
  const lines = [];
  let line = "";
  words.forEach(w => {{
    const test = line ? line + " " + w : w;
    if (test.length > maxChars && line) {{ lines.push(line); line = w; }}
    else {{ line = test; }}
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
  gLinks.selectAll(".link").attr("stroke", temaDark ? "#4a9eff" : "#1a6bab");
}}

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
