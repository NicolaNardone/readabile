# ============================================================
# ReadAbile - Modulo Mappa Visiva (versione D3.js Algor-style)
# - Misura testo con Canvas API (precisione assoluta)
# - Colori per ramo
# - Auto-fit reale allo schermo
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

    palette = [
        {"dark": "#1a4f8a", "mid": "#2471a3", "light": "#aed6f1", "stroke": "#4a9eff"},
        {"dark": "#512e5f", "mid": "#7d3c98", "light": "#d7bde2", "stroke": "#a569bd"},
        {"dark": "#145a32", "mid": "#1e8449", "light": "#a9dfbf", "stroke": "#2ecc71"},
        {"dark": "#7d6608", "mid": "#b7950b", "light": "#f9e79f", "stroke": "#f1c40f"},
        {"dark": "#6e2c00", "mid": "#a04000", "light": "#f5cba7", "stroke": "#e67e22"},
    ]

    albero = {
        "name": struttura["concetto_centrale"],
        "level": 0,
        "colorIdx": -1,
        "children": []
    }

    for i, ramo in enumerate(struttura["rami"]):
        ci = i % len(palette)
        nodo = {
            "name": ramo["concetto"],
            "level": 1,
            "colorIdx": ci,
            "children": [
                {"name": s, "level": 2, "colorIdx": ci, "children": []}
                for s in ramo.get("sotto_concetti", [])
            ]
        }
        albero["children"].append(nodo)

    dati_json = json.dumps(albero, ensure_ascii=False)
    palette_json = json.dumps(palette)

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
  body {{
    background: #0d0d1a;
    font-family: 'OpenDyslexic','Segoe UI',sans-serif;
    transition: background 0.3s;
  }}
  body.light {{ background: #f5f7ff; }}

  .link {{
    fill: none;
    stroke-width: 2px;
    stroke-opacity: 0.7;
  }}
  .node rect {{
    stroke-width: 2px;
    cursor: grab;
    transition: filter 0.15s;
  }}
  .node rect:active {{ cursor: grabbing; }}
  .node:hover rect {{ filter: brightness(1.2); }}
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
    background: rgba(255,255,255,0.12);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 50px;
    padding: 7px 16px;
    cursor: pointer;
    font-family: 'OpenDyslexic',sans-serif;
    font-size: 11px;
    color: white;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s;
    user-select: none;
  }}
  body.light .ctrl-btn {{
    background: rgba(0,0,0,0.07);
    border-color: rgba(0,0,0,0.15);
    color: #333;
  }}
  .ctrl-btn:hover {{ transform: scale(1.05); }}

  .hint {{
    position: fixed;
    bottom: 12px;
    right: 12px;
    font-size: 10px;
    color: rgba(255,255,255,0.25);
    font-family: 'OpenDyslexic',sans-serif;
    z-index: 100;
  }}
  body.light .hint {{ color: rgba(0,0,0,0.25); }}
</style>
</head>
<body class="dark">

<div class="controls">
  <div class="ctrl-btn" onclick="toggleTema()">
    <span id="themeIcon">☀️</span>
    <span id="themeLabel">Tema chiaro</span>
  </div>
  <div class="ctrl-btn" onclick="resetZoom()">🔍 Fit schermo</div>
  <div class="ctrl-btn" onclick="scarica()">💾 Scarica SVG</div>
</div>
<div class="hint">Scorri per zoomare · Trascina per muovere</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>
const DATA    = {dati_json};
const PALETTE = {palette_json};

// Padding e font size per livello
const LV = [
  {{ fs: 15, px: 28, py: 14 }},
  {{ fs: 13, px: 22, py: 12 }},
  {{ fs: 11, px: 18, py: 10 }},
];

const LEVEL_GAP = 130;
let temaDark = true;

// ── Misura testo con Canvas API (precisione assoluta) ─────
const _canvas = document.createElement('canvas');
const _ctx    = _canvas.getContext('2d');

function misuraTesto(text, fs) {{
  _ctx.font = `600 ${{fs}}px OpenDyslexic, Segoe UI, sans-serif`;
  return _ctx.measureText(text).width;
}}

// ── Calcola dimensione nodo basata sul testo reale ────────
function calcolaDim(name, lv) {{
  const cfg = LV[Math.min(lv, 2)];
  const tw  = misuraTesto(name, cfg.fs);
  const w   = tw + cfg.px * 2;
  const h   = cfg.fs + cfg.py * 2;
  return {{ w: Math.max(w, 80), h: Math.max(h, 36) }};
}}

// ── Colore nodo ───────────────────────────────────────────
function nodeColor(d, tema) {{
  if (d.data.level === 0) {{
    return tema === 'dark'
      ? {{ fill:'#0f2d4a', stroke:'#4a9eff', text:'#d6eaf8' }}
      : {{ fill:'#2980b9', stroke:'#1a5276', text:'white'   }};
  }}
  const p  = PALETTE[d.data.colorIdx] || PALETTE[0];
  const lv = d.data.level;
  return tema === 'dark'
    ? {{ fill: lv===1 ? p.dark : p.mid,   stroke: p.stroke, text:'#ffffff' }}
    : {{ fill: lv===1 ? p.mid  : p.light, stroke: p.dark,   text: lv===2 ? '#222':'#fff' }};
}}

// ── SVG e zoom ────────────────────────────────────────────
const svg   = d3.select('body').append('svg').style('position','absolute');
const gZoom = svg.append('g');
const zoom  = d3.zoom().scaleExtent([0.05, 5]).on('zoom', e => gZoom.attr('transform', e.transform));
svg.call(zoom);

function resize() {{ svg.attr('width', window.innerWidth).attr('height', window.innerHeight); }}
resize();
window.addEventListener('resize', () => {{ resize(); }});

// ── Gerarchia ─────────────────────────────────────────────
const root = d3.hierarchy(DATA);

// Precalcolo dimensioni nodi
root.each(d => {{
  const dim = calcolaDim(d.data.name, d.data.level);
  d.nw = dim.w;
  d.nh = dim.h;
}});

// ── Layout D3 tree con size adattivo ─────────────────────
// size([width, height]) distribuisce i nodi nello spazio in modo
// che non si sovrappongano mai — D3 gestisce tutto automaticamente
const nFoglie = root.leaves().length;
const treeW   = Math.max(nFoglie * 240, window.innerWidth  * 0.9);
const treeH   = Math.max((root.height + 1) * LEVEL_GAP, window.innerHeight * 0.75);

const tree = d3.tree().size([treeW, treeH]);
tree(root);

// D3 tree: d.x = posizione orizzontale, d.y = profondità
root.each(d => {{
  d.px = d.x;
  d.py = d.y;
}});

// ── Bounding box e auto-fit ───────────────────────────────
const nodes = root.descendants();
const xMin  = d3.min(nodes, d => d.px - d.nw / 2);
const xMax  = d3.max(nodes, d => d.px + d.nw / 2);
const yMin  = d3.min(nodes, d => d.py);
const yMax  = d3.max(nodes, d => d.py + d.nh);
const cW    = xMax - xMin;
const cH    = yMax - yMin;
const PAD   = 48;

function fitTransform() {{
  const W  = window.innerWidth;
  const H  = window.innerHeight;
  const sc = Math.min((W - PAD * 2) / cW, (H - PAD * 2) / cH, 1.1);
  const tx = W / 2 - (xMin + cW / 2) * sc;
  const ty = PAD - yMin * sc;
  return d3.zoomIdentity.translate(tx, ty).scale(sc);
}}

svg.call(zoom.transform, fitTransform());

// ── Links ─────────────────────────────────────────────────
function linkPath(s, t) {{
  const sx = s.px, sy = s.py + s.nh;
  const tx = t.px, ty = t.py;
  const my = (sy + ty) / 2;
  return `M${{sx}},${{sy}} C${{sx}},${{my}} ${{tx}},${{my}} ${{tx}},${{ty}}`;
}}

const gLinks  = gZoom.append('g');
const linkEls = gLinks.selectAll('path')
  .data(root.links())
  .join('path')
  .attr('class', 'link')
  .attr('stroke', d => {{
    const ci = d.target.data.colorIdx;
    return ci >= 0 ? PALETTE[ci].stroke : '#4a9eff';
  }})
  .attr('d', d => linkPath(d.source, d.target));

// ── Nodi ─────────────────────────────────────────────────
const gNodes  = gZoom.append('g');
const nodeEls = gNodes.selectAll('g')
  .data(nodes)
  .join('g')
  .attr('class', 'node')
  .attr('transform', d => `translate(${{d.px - d.nw/2}},${{d.py}})`)
  .call(d3.drag()
    .on('drag', function(e, d) {{
      d.px += e.dx;
      d.py += e.dy;
      d3.select(this).attr('transform', `translate(${{d.px - d.nw/2}},${{d.py}})`);
      linkEls.attr('d', dd => linkPath(dd.source, dd.target));
    }})
  );

// Rettangoli
nodeEls.append('rect')
  .attr('width',  d => d.nw)
  .attr('height', d => d.nh)
  .attr('rx', 10).attr('ry', 10)
  .attr('fill',   d => nodeColor(d, 'dark').fill)
  .attr('stroke', d => nodeColor(d, 'dark').stroke);

// Testo centrato (una sola riga — la larghezza è calcolata sul testo)
nodeEls.append('text')
  .attr('x', d => d.nw / 2)
  .attr('y', d => d.nh / 2)
  .attr('fill',        d => nodeColor(d, 'dark').text)
  .attr('font-size',   d => LV[Math.min(d.data.level,2)].fs + 'px')
  .attr('font-weight', d => d.data.level === 0 ? '700' : '600')
  .text(d => d.data.name);

// ── Toggle tema ───────────────────────────────────────────
function toggleTema() {{
  temaDark = !temaDark;
  const tema = temaDark ? 'dark' : 'light';
  document.body.className = tema;
  document.getElementById('themeIcon').textContent  = temaDark ? '☀️' : '🌙';
  document.getElementById('themeLabel').textContent = temaDark ? 'Tema chiaro' : 'Tema scuro';
  nodeEls.selectAll('rect')
    .attr('fill',   d => nodeColor(d, tema).fill)
    .attr('stroke', d => nodeColor(d, tema).stroke);
  nodeEls.selectAll('text')
    .attr('fill',   d => nodeColor(d, tema).text);
}}

// ── Fit schermo ───────────────────────────────────────────
function resetZoom() {{
  svg.transition().duration(500).call(zoom.transform, fitTransform());
}}
// ── Scarica mappa come PNG ────────────────────────────────
function scarica() {{
  const pad = 50;
  
  // ViewBox esatto sul contenuto reale (coordinate dei nodi)
  const vx = xMin - pad;
  const vy = yMin - pad;
  const vw = cW + pad * 2;
  const vh = cH + pad * 2;

  // Creo SVG pulito da zero
  const ns = 'http://www.w3.org/2000/svg';
  const out = document.createElementNS(ns, 'svg');
  out.setAttribute('xmlns', ns);
  out.setAttribute('width',   vw);
  out.setAttribute('height',  vh);
  out.setAttribute('viewBox', `${{vx}} ${{vy}} ${{vw}} ${{vh}}`);

  // Sfondo
  const bg = document.createElementNS(ns, 'rect');
  bg.setAttribute('x', vx); bg.setAttribute('y', vy);
  bg.setAttribute('width', vw); bg.setAttribute('height', vh);
  bg.setAttribute('fill', temaDark ? '#0d0d1a' : '#f5f7ff');
  out.appendChild(bg);

  // Copio links e nodi dal gZoom (già nelle coordinate corrette)
  const gClone = gZoom.node().cloneNode(true);
  gClone.removeAttribute('transform');
  out.appendChild(gClone);

  // Scarico
  const data = new XMLSerializer().serializeToString(out);
  const blob = new Blob([data], {{type:'image/svg+xml;charset=utf-8'}});
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.download = 'mappa-readabile.svg';
  a.href = url;
  a.click();
  URL.revokeObjectURL(url);
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
