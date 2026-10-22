import json
import os
from datetime import datetime

folder = os.path.dirname(os.path.abspath(__file__))
json_files = [
    "heygen-pricing.json",
    "higgsfield-pricing.json",
    "runway-pricing.json",
    "kling-pricing.json",
    "synthesia-pricing.json",
    "pika-pricing.json",
    "luma-pricing.json",
    "viggle-pricing.json",
    "invideo-pricing.json",
    "capcut-pricing.json",
    "ltx-pricing.json"
]

data = {}
for file in json_files:
    path = os.path.join(folder, file)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data[file] = json.load(f)

json_data = json.dumps(data)
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GenCost</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Inter:wght@400;500&display=swap');
  body {{
    margin: 0;
    font-family: 'Inter', sans-serif;
    color: #e0e0e0;
    background: 
      radial-gradient(ellipse at 0% 50%, rgba(0,212,255,0.15) 0%, transparent 50%),
      radial-gradient(ellipse at 100% 50%, rgba(123,104,238,0.15) 0%, transparent 50%),
      linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
    background-attachment: fixed;
  }}
  .overlay {{
    min-height: 100vh;
    padding: 40px 20px 60px;
  }}
  h1 {{
    text-align: center;
    font-family: 'Orbitron', sans-serif;
    font-size: 3.2em;
    letter-spacing: 4px;
    margin: 0;
    background: linear-gradient(90deg, #00d4ff, #7b68ee);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 30px rgba(0,212,255,0.3);
  }}
  .subtitle {{
    text-align: center;
    margin: 8px 0 4px 0;
    font-size: 1.1em;
    opacity: 0.8;
    letter-spacing: 1px;
  }}
  .timestamp {{
    text-align: center;
    font-size: 0.8em;
    opacity: 0.5;
    margin-bottom: 30px;
    letter-spacing: 0.5px;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 24px;
    max-width: 1400px;
    margin: 0 auto;
  }}
  .card {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    backdrop-filter: blur(10px);
    padding: 22px;
    border-radius: 16px;
    transition: all 0.3s ease;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    position: relative;
    overflow: hidden;
  }}
  .card:hover {{
    transform: translateY(-4px);
    border-color: rgba(0,212,255,0.3);
    box-shadow: 0 12px 40px rgba(0,212,255,0.15);
  }}
  .card h2 {{
    margin: 0 0 16px 0;
    font-size: 1.5em;
    font-family: 'Orbitron', sans-serif;
    letter-spacing: 1px;
  }}
  .card h2 a {{
    color: #fff;
    text-decoration: none;
  }}
  .card h2 a:hover {{
    color: #00d4ff;
  }}
  .plan {{
    margin: 8px 0;
    padding: 6px 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }}
  .plan:last-child {{ border-bottom: none; }}
  .cost {{
    font-size: 0.82em;
    opacity: 0.7;
    margin-left: 6px;
    color: #00d4ff;
  }}
  .particle {{
    position: absolute;
    width: 5px;
    height: 5px;
    background: #00d4ff;
    border-radius: 50%;
    pointer-events: none;
    z-index: 10;
  }}
  .footer {{
    text-align: center;
    margin-top: 50px;
    font-size: 0.8em;
    opacity: 0.55;
    letter-spacing: 0.6px;
  }}
  .footer-sub {{
    text-align: center;
    font-size: 0.7em;
    opacity: 0.35;
    margin-top: 4px;
  }}
  .contact {{
    text-align: center;
    font-size: 0.75em;
    opacity: 0.5;
    margin-top: 10px;
  }}
  .contact a {{
    color: #00d4ff;
    text-decoration: none;
  }}
  @media (max-width: 700px) {{
    .overlay {{ padding: 24px 12px 50px; }}
    h1 {{ font-size: 2.2em; letter-spacing: 2px; }}
    .grid {{ grid-template-columns: 1fr; gap: 16px; }}
    .card {{ padding: 16px; }}
    .card h2 {{ font-size: 1.3em; }}
  }}
</style>
</head>
<body>
<div class="overlay">
  <h1>GENCOST</h1>
  <p class="subtitle">AI VIDEO PRICE COMPARISON</p>
  <div class="timestamp">LAST UPDATED · {timestamp}</div>
  <div class="grid" id="content"></div>
  <div class="footer">Created by Grok & Bitbooz · 22.10.2026</div>
  <div class="footer-sub">Prices update automatically · Always double-check before buying</div>
  <div class="contact">Contact: <a href="mailto:bitbooz@protonmail.com">bitbooz@protonmail.com</a></div>
</div>

<script>
const allData = {json_data};

function cleanName(name) {{
  const n = (name || "").toLowerCase();
  if (n.includes("heygen")) return "HeyGen";
  if (n.includes("kling")) return "Kling AI";
  if (n.includes("ltx")) return "LTX Studio";
  if (n.includes("invideo")) return "InVideo";
  if (n.includes("capcut")) return "CapCut";
  if (n.includes("higgs")) return "Higgsfield";
  if (n.includes("runway")) return "Runway";
  if (n.includes("synth")) return "Synthesia";
  if (n.includes("pika")) return "Pika";
  if (n.includes("luma")) return "Luma";
  if (n.includes("viggle")) return "Viggle";
  return name;
}}

function getPage(name) {{
  const map = {{
    "HeyGen": "pages/heygen.html",
    "Higgsfield": "pages/higgsfield.html",
    "Runway": "pages/runway.html",
    "Kling AI": "pages/kling.html",
    "Synthesia": "pages/synthesia.html",
    "Pika": "pages/pika.html",
    "Luma": "pages/luma.html",
    "Viggle": "pages/viggle.html",
    "InVideo": "pages/invideo.html",
    "CapCut": "pages/capcut.html",
    "LTX Studio": "pages/ltx.html"
  }};
  return map[name] || "#";
}}

function estimateCost(plan) {{
  const price = plan.monthly_price_usd || 0;
  const credits = plan.credits_or_minutes || 0;
  if (!price || !credits || credits <= 0) return "";
  const costPer10s = (price / credits) * 10;
  if (costPer10s < 0.01) return "";
  return ` (~$${{costPer10s.toFixed(2)}} / 10s)`;
}}

function createParticles(e) {{
  e.preventDefault();
  const link = e.currentTarget;
  const card = link.closest('.card');
  const rect = card.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  for (let i = 0; i < 22; i++) {{
    const p = document.createElement('div');
    p.className = 'particle';
    p.style.left = x + 'px';
    p.style.top = y + 'px';
    const angle = Math.random() * Math.PI * 2;
    const speed = 1.5 + Math.random() * 5;
    const dx = Math.cos(angle) * speed;
    const dy = Math.sin(angle) * speed;
    card.appendChild(p);
    let px = x, py = y, life = 1;
    function anim() {{
      life -= 0.018;
      if (life <= 0) {{ p.remove(); return; }}
      px += dx;
      py += dy;
      p.style.left = px + 'px';
      p.style.top = py + 'px';
      p.style.opacity = life;
      requestAnimationFrame(anim);
    }}
    anim();
  }}
  setTimeout(() => {{ window.location.href = link.href; }}, 280);
}}

const order = ["HeyGen", "Higgsfield", "Runway", "Kling AI", "Synthesia", "Pika", "Luma", "Viggle", "InVideo", "CapCut", "LTX Studio"];
const content = document.getElementById("content");

const platforms = [];
for (const [file, data] of Object.entries(allData)) {{
  if (!data) continue;
  const raw = data.platform || file.replace("-pricing.json","");
  const name = cleanName(raw);
  platforms.push({{ name, data }});
}}

platforms.sort((a, b) => {{
  const ai = order.indexOf(a.name);
  const bi = order.indexOf(b.name);
  if (ai === -1 && bi === -1) return a.name.localeCompare(b.name);
  if (ai === -1) return 1;
  if (bi === -1) return -1;
  return ai - bi;
}});

for (const {{ name, data }} of platforms) {{
  const page = getPage(name);
  let html = `<div class="card"><h2><a href="${{page}}" onclick="createParticles(event)">${{name}}</a></h2>`;
  for (const plan of data.plans || []) {{
    const price = plan.monthly_price_usd ?? 0;
    const credits = plan.credits_or_minutes ?? "-";
    const unit = plan.unit || "";
    const est = estimateCost(plan);
    html += `<div class="plan"><strong>${{plan.name}}</strong>: $${{price}}/mo · ${{credits}} ${{unit}}<span class="cost">${{est}}</span></div>`;
  }}
  html += "</div>";
  content.innerHTML += html;
}}
</script>
</body>
</html>'''

with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
    f.write(html)

print("index.html regenerated with contact email.")
