import json
import os
from datetime import datetime

folder = os.path.dirname(os.path.abspath(__file__))
json_files = [
    "heygen-pricing.json", "higgsfield-pricing.json", "runway-pricing.json",
    "kling-pricing.json", "synthesia-pricing.json", "pika-pricing.json",
    "luma-pricing.json", "viggle-pricing.json", "invideo-pricing.json",
    "capcut-pricing.json", "ltx-pricing.json", "hailuo-pricing.json",
    "veo-pricing.json", "hedra-pricing.json", "sora-pricing.json",
    "vidu-pricing.json", "krea-pricing.json"
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
<script async src="https://www.googletagmanager.com/gtag/js?id=G-6DHTT2ZTBK"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-6DHTT2ZTBK');
</script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Inter:wght@400;500&display=swap');
  body {{
    margin: 0;
    font-family: 'Inter', sans-serif;
    color: #e0e0e0;
    background: url('/Background.jpg') center/cover fixed no-repeat,
                radial-gradient(ellipse at 0% 50%, rgba(0,212,255,0.15) 0%, transparent 50%),
                radial-gradient(ellipse at 100% 50%, rgba(123,104,238,0.15) 0%, transparent 50%),
                linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
  }}
  .overlay {{
    min-height: 100vh;
    padding: 40px 20px 60px;
    background: rgba(10, 10, 15, 0.75);
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
  }}
  .subtitle {{ text-align: center; margin: 8px 0 4px 0; font-size: 1.1em; opacity: 0.8; }}
  .timestamp {{ text-align: center; font-size: 0.8em; opacity: 0.5; margin-bottom: 30px; }}
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
  }}
  .card h2 {{ margin: 0 0 16px 0; font-size: 1.5em; font-family: 'Orbitron', sans-serif; }}
  .card h2 a {{ color: #fff; text-decoration: none; }}
  .plan {{ margin: 8px 0; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }}
  .cost {{ font-size: 0.95em; opacity: 0.9; margin-left: 6px; color: #00d4ff; font-weight:600; }}
  @media (max-width: 768px) {{
    div[style*="grid-template-columns:1fr 1fr"] {{
      grid-template-columns: 1fr !important;
      max-width: 100% !important;
      padding: 0 16px !important;
      margin-left: auto !important;
      margin-right: auto !important;
    }}
  }}
</style>
</head>
<body>
<div style="background:#1a1a2e; border:1px solid #00d4ff; border-radius:8px; padding:1rem; margin:1rem auto; max-width:1400px; color:#e0e0e0; text-align:center;">
  <strong>Best value right now</strong><br>
  Kling AI Standard is often among the lowest entry prices (~$8–10/mo). Check the cards below for the latest.
</div>
<div style="max-width:1400px; margin:10px auto 20px; display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; padding:0 16px;">
  <div style="background:rgba(0,212,255,0.08); border:1px solid #00d4ff; border-radius:10px; padding:14px; text-align:center;">
    <strong>Cheapest video</strong><br><span style="font-size:0.9em;">Kling AI Standard ~$8–10/mo</span>
  </div>
  <div style="background:rgba(123,104,238,0.08); border:1px solid #7b68ee; border-radius:10px; padding:14px; text-align:center;">
    <strong>Cheapest avatar</strong><br><span style="font-size:0.9em;">Synthesia Starter ~$19/mo</span>
  </div>
  <div style="background:rgba(0,212,255,0.06); border:1px solid #00d4ff; border-radius:10px; padding:14px; text-align:center;">
    <strong>Cheapest voice</strong><br><span style="font-size:0.9em;">Cartesia Pro ~$5/mo</span>
  </div>
</div>
<div style="max-width:1400px; margin:0 auto 20px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); border-radius:10px; padding:16px; text-align:center;">
  <strong>Around $10 / $30</strong><br>
  <span style="font-size:0.9em;">~$10: Kling Standard or Pika Starter &nbsp;|&nbsp; ~$30: Runway Pro, Luma Plus or HeyGen Creator</span>
</div>
<p style="color:#aaa; font-size:0.9rem; text-align:center;">
  <strong>Last updated:</strong> {timestamp}<br>
  Prices change often — always confirm inside the tool before generating.
</p>
<div class="overlay">
  <h1>GENCOST</h1>
  <p class="subtitle">AI VIDEO PRICE COMPARISON</p>
  <div class="timestamp">LAST UPDATED · {timestamp}</div>
  <div style="max-width:1400px; margin:20px auto 40px; display:grid; grid-template-columns:1fr 1fr; gap:20px; padding:0 20px;">
    <div style="background:rgba(0,212,255,0.08); border:1px solid #00d4ff; border-radius:12px; padding:22px; text-align:center;">
      <a href="/voice.html" style="color:#00d4ff; font-size:1.3em; font-weight:600; text-decoration:none;">AI Voice Price Comparison →</a>
      <p style="margin:10px 0 0 0; font-size:0.95em; color:#ddd;">Compare ElevenLabs, PlayHT, Cartesia and more in real dollars.<br><small>Updated automatically with the latest prices.</small></p>
    </div>
    <div style="background:rgba(123,104,238,0.08); border:1px solid #7b68ee; border-radius:12px; padding:22px; text-align:center;">
      <a href="/music.html" style="color:#7b68ee; font-size:1.3em; font-weight:600; text-decoration:none;">AI Music Price Comparison →</a>
      <p style="margin:10px 0 0 0; font-size:0.95em; color:#ddd;">Compare Suno, Udio, Soundraw, AIVA and Boomy in real dollars.<br><small>Updated automatically with the latest prices.</small></p>
    </div>
  </div>
  <div class="grid" id="content"></div>
  <h2 style="margin-top:2rem;">Free tiers available</h2>
  <p style="color:#aaa;">HeyGen, Runway, Pika, Synthesia and others still offer free plans.</p>
  <div style="max-width:1400px; margin:40px auto 20px; display:grid; grid-template-columns:1fr 1fr; gap:20px; padding:0 20px;">
    <div style="background:rgba(0,212,255,0.08); border:1px solid #00d4ff; border-radius:12px; padding:22px; text-align:center;">
      <a href="/voice.html" style="color:#00d4ff; font-size:1.3em; font-weight:600; text-decoration:none;">AI Voice Price Comparison →</a>
      <p style="margin:10px 0 0 0; font-size:0.95em; color:#ddd;">Compare ElevenLabs, PlayHT, Cartesia and more in real dollars.<br><small>Updated automatically with the latest prices.</small></p>
    </div>
    <div style="background:rgba(123,104,238,0.08); border:1px solid #7b68ee; border-radius:12px; padding:22px; text-align:center;">
      <a href="/music.html" style="color:#7b68ee; font-size:1.3em; font-weight:600; text-decoration:none;">AI Music Price Comparison →</a>
      <p style="margin:10px 0 0 0; font-size:0.95em; color:#ddd;">Compare Suno, Udio, Soundraw, AIVA and Boomy in real dollars.<br><small>Updated automatically with the latest prices.</small></p>
    </div>
  </div>
  <div style="text-align:center; margin-top:40px; font-size:0.8em; opacity:0.6;">
    Created by Grok & Bitbooz · Contact: bitbooz@protonmail.com
  </div>
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
  if (n.includes("hailuo")) return "Hailuo AI";
  if (n.includes("veo")) return "Google Veo";
  if (n.includes("hedra")) return "Hedra";
  if (n.includes("sora")) return "Sora";
  if (n.includes("vidu")) return "Vidu";
  if (n.includes("krea")) return "Krea";
  return name;
}}
function getPage(name) {{
  const map = {{
    "HeyGen":"pages/heygen.html","Higgsfield":"pages/higgsfield.html","Runway":"pages/runway.html",
    "Kling AI":"pages/kling.html","Synthesia":"pages/synthesia.html","Pika":"pages/pika.html",
    "Luma":"pages/luma.html","Viggle":"pages/viggle.html","InVideo":"pages/invideo.html",
    "CapCut":"pages/capcut.html","LTX Studio":"pages/ltx.html","Hailuo AI":"pages/hailuo.html",
    "Google Veo":"pages/veo.html","Hedra":"pages/hedra.html","Sora":"pages/sora.html",
    "Vidu":"pages/vidu.html","Krea":"pages/krea.html"
  }};
  return map[name] || "#";
}}
function estimateCost(plan) {{
  const price = plan.monthly_price_usd || 0;
  const credits = plan.credits_or_minutes || 0;
  if (!price || !credits || credits <= 0) return "";
  const costPer10s = (price / credits) * 10;
  return costPer10s >= 0.01 ? ` (~$${{costPer10s.toFixed(2)}} / 10s)` : "";
}}
function createParticles(e) {{
  const x = e.clientX, y = e.clientY;
  for (let i = 0; i < 12; i++) {{
    const p = document.createElement("div");
    p.style.cssText = "position:fixed; width:6px; height:6px; background:#00d4ff; border-radius:50%; pointer-events:none; z-index:9999;";
    p.style.left = x + "px";
    p.style.top = y + "px";
    document.body.appendChild(p);
    const angle = Math.random() * Math.PI * 2;
    const speed = 2 + Math.random() * 4;
    const vx = Math.cos(angle) * speed;
    const vy = Math.sin(angle) * speed;
    let px = x, py = y, life = 30;
    const anim = setInterval(() => {{
      px += vx; py += vy; life--;
      p.style.left = px + "px";
      p.style.top = py + "px";
      p.style.opacity = life / 30;
      if (life <= 0) {{ clearInterval(anim); p.remove(); }}
    }}, 16);
  }}
}}
const order = ["HeyGen","Higgsfield","Runway","Kling AI","Synthesia","Pika","Luma","Viggle","InVideo","CapCut","LTX Studio","Hailuo AI","Google Veo","Hedra","Sora","Vidu","Krea"];
const content = document.getElementById("content");
const platforms = [];
for (const [file, data] of Object.entries(allData)) {{
  if (!data) continue;
  const name = cleanName(data.platform || file.replace("-pricing.json",""));
  platforms.push({{ name, data }});
}}
platforms.sort((a, b) => {{
  const ai = order.indexOf(a.name), bi = order.indexOf(b.name);
  if (ai === -1 && bi === -1) return a.name.localeCompare(b.name);
  if (ai === -1) return 1;
  if (bi === -1) return -1;
  return ai - bi;
}});
for (const {{ name, data }} of platforms) {{
  const page = getPage(name);
  const checked = data.last_checked || data.checked || "recently";
  const source = data.source || data.source_url || "";
  let html = `<div class="card"><h2><a href="${{page}}" onclick="createParticles(event)">${{name}}</a></h2>`;
  if (source) {{
    html += `<div style="font-size:0.75em; opacity:0.6; margin-bottom:8px;">Checked: ${{checked}} · <a href="${{source}}" target="_blank" style="color:#00d4ff;">Source</a></div>`;
  }} else {{
    html += `<div style="font-size:0.75em; opacity:0.6; margin-bottom:8px;">Checked: ${{checked}}</div>`;
  }}
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
print("index.html regenerated cleanly.")

# === VOICE PAGE ===
voice_folder = os.path.join(folder, "voice")
voice_files = [
    "elevenlabs-pricing.json", "murf-pricing.json", "cartesia-pricing.json",
    "speechify-pricing.json", "descript-pricing.json"
]

voice_data = {}
for file in voice_files:
    path = os.path.join(voice_folder, file)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            voice_data[file] = json.load(f)

voice_json = json.dumps(voice_data)

voice_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Voice Price Comparison 2026 | GenCost</title>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-6DHTT2ZTBK"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-6DHTT2ZTBK');
</script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Inter:wght@400;500&display=swap');
  body {{
    margin: 0;
    font-family: 'Inter', sans-serif;
    color: #e0e0e0;
    background: url('/Background.jpg') center/cover fixed no-repeat,
                radial-gradient(ellipse at 0% 50%, rgba(0,212,255,0.15) 0%, transparent 50%),
                radial-gradient(ellipse at 100% 50%, rgba(123,104,238,0.15) 0%, transparent 50%),
                linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
  }}
  .overlay {{
    min-height: 100vh;
    padding: 40px 20px 60px;
    background: rgba(10, 10, 15, 0.75);
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
  }}
  .subtitle {{ text-align: center; margin: 8px 0 4px 0; font-size: 1.1em; opacity: 0.8; }}
  .timestamp {{ text-align: center; font-size: 0.8em; opacity: 0.5; margin-bottom: 30px; }}
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
  }}
  .card h2 {{ margin: 0 0 16px 0; font-size: 1.5em; font-family: 'Orbitron', sans-serif; }}
  .plan {{ margin: 8px 0; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }}
  .cost {{ font-size: 0.95em; opacity: 0.9; margin-left: 6px; color: #00d4ff; font-weight:600; }}
</style>
</head>
<body>
<div class="overlay">
  <h1>GENCOST VOICE</h1>
  <p class="subtitle">AI VOICE PRICE COMPARISON</p>
  <div class="timestamp">LAST UPDATED · {timestamp}</div>
  <div class="grid" id="content"></div>
  <div style="text-align:center; margin-top:40px; font-size:0.8em; opacity:0.6;">
    <a href="/" style="color:#00d4ff;">← Back to video comparison</a><br><br>
    Created by Grok & Bitbooz · Contact: bitbooz@protonmail.com
  </div>
</div>
<script>
const allData = {voice_json};
function cleanName(name) {{
  const n = (name || "").toLowerCase();
  if (n.includes("eleven")) return "ElevenLabs";
  if (n.includes("murf")) return "Murf AI";
  if (n.includes("cartesia")) return "Cartesia";
  if (n.includes("speechify")) return "Speechify";
  if (n.includes("descript")) return "Descript";
  if (n.includes("playht") || n.includes("play.ht")) return "PlayHT";
  if (n.includes("wellsaid")) return "WellSaid Labs";
  return name;
}}
function getPage(name) {{
  const map = {{
    "ElevenLabs":"pages/voice/elevenlabs.html",
    "Murf AI":"pages/voice/murf.html",
    "Cartesia":"pages/voice/cartesia.html",
    "Speechify":"pages/voice/speechify.html",
    "Descript":"pages/voice/descript.html",
    "PlayHT":"pages/voice/playht.html",
    "WellSaid Labs":"pages/voice/wellsaid.html"
  }};
  return map[name] || "#";
}}
function estimateCost(plan) {{
  const price = plan.monthly_price_usd || 0;
  const credits = plan.credits_or_minutes || 0;
  if (!price || !credits || credits <= 0) return "";
  if (plan.unit && plan.unit.toLowerCase().includes("character")) {{
    const costPer1k = (price / credits) * 1000;
    return costPer1k >= 0.001 ? ` (~$${{costPer1k.toFixed(3)}} / 1k chars)` : "";
  }}
  return "";
}}
function createParticles(e) {{
  const x = e.clientX, y = e.clientY;
  for (let i = 0; i < 12; i++) {{
    const p = document.createElement("div");
    p.style.cssText = "position:fixed; width:6px; height:6px; background:#00d4ff; border-radius:50%; pointer-events:none; z-index:9999;";
    p.style.left = x + "px";
    p.style.top = y + "px";
    document.body.appendChild(p);
    const angle = Math.random() * Math.PI * 2;
    const speed = 2 + Math.random() * 4;
    const vx = Math.cos(angle) * speed;
    const vy = Math.sin(angle) * speed;
    let px = x, py = y, life = 30;
    const anim = setInterval(() => {{
      px += vx; py += vy; life--;
      p.style.left = px + "px";
      p.style.top = py + "px";
      p.style.opacity = life / 30;
      if (life <= 0) {{ clearInterval(anim); p.remove(); }}
    }}, 16);
  }}
}}
const order = ["ElevenLabs","Murf AI","Cartesia","Speechify","Descript"];
const content = document.getElementById("content");
const platforms = [];
for (const [file, data] of Object.entries(allData)) {{
  if (!data) continue;
  const name = cleanName(data.platform || file.replace("-pricing.json",""));
  platforms.push({{ name, data }});
}}
platforms.sort((a, b) => {{
  const ai = order.indexOf(a.name), bi = order.indexOf(b.name);
  if (ai === -1 && bi === -1) return a.name.localeCompare(b.name);
  if (ai === -1) return 1;
  if (bi === -1) return -1;
  return ai - bi;
}});
for (const {{ name, data }} of platforms) {{
  const page = getPage(name);
  const checked = data.last_checked || data.checked || "recently";
  const source = data.source || data.source_url || "";
  let html = `<div class="card"><h2><a href="${{page}}" onclick="createParticles(event)">${{name}}</a></h2>`;
  if (source) {{
    html += `<div style="font-size:0.75em; opacity:0.6; margin-bottom:8px;">Checked: ${{checked}} · <a href="${{source}}" target="_blank" style="color:#00d4ff;">Source</a></div>`;
  }} else {{
    html += `<div style="font-size:0.75em; opacity:0.6; margin-bottom:8px;">Checked: ${{checked}}</div>`;
  }}
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

with open(os.path.join(folder, "voice.html"), "w", encoding="utf-8") as f:
    f.write(voice_html)
print("voice.html regenerated.")

# === MUSIC PAGE ===
music_folder = os.path.join(folder, "music")
music_files = [
    "suno-pricing.json", "udio-pricing.json", "soundraw-pricing.json",
    "aiva-pricing.json", "boomy-pricing.json"
]

music_data = {}
for file in music_files:
    path = os.path.join(music_folder, file)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            music_data[file] = json.load(f)

music_json = json.dumps(music_data)

music_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Music Price Comparison 2026 | GenCost</title>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-6DHTT2ZTBK"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-6DHTT2ZTBK');
</script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Inter:wght@400;500&display=swap');
  body {{
    margin: 0;
    font-family: 'Inter', sans-serif;
    color: #e0e0e0;
    background: url('/Background.jpg') center/cover fixed no-repeat,
                radial-gradient(ellipse at 0% 50%, rgba(0,212,255,0.15) 0%, transparent 50%),
                radial-gradient(ellipse at 100% 50%, rgba(123,104,238,0.15) 0%, transparent 50%),
                linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
  }}
  .overlay {{
    min-height: 100vh;
    padding: 40px 20px 60px;
    background: rgba(10, 10, 15, 0.75);
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
  }}
  .subtitle {{ text-align: center; margin: 8px 0 4px 0; font-size: 1.1em; opacity: 0.8; }}
  .timestamp {{ text-align: center; font-size: 0.8em; opacity: 0.5; margin-bottom: 30px; }}
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
  }}
  .card h2 {{ margin: 0 0 16px 0; font-size: 1.5em; font-family: 'Orbitron', sans-serif; }}
  .card h2 a {{ color: #fff; text-decoration: none; }}
  .plan {{ margin: 8px 0; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }}
  .cost {{ font-size: 0.95em; opacity: 0.9; margin-left: 6px; color: #00d4ff; font-weight:600; }}
</style>
</head>
<body>
<div class="overlay">
  <h1>GENCOST MUSIC</h1>
  <p class="subtitle">AI MUSIC PRICE COMPARISON</p>
  <div class="timestamp">LAST UPDATED · {timestamp}</div>
  <div class="grid" id="content"></div>
  <div style="text-align:center; margin-top:40px; font-size:0.8em; opacity:0.6;">
    <a href="/" style="color:#00d4ff;">← Back to video comparison</a><br><br>
    Created by Grok & Bitbooz · Contact: bitbooz@protonmail.com
  </div>
</div>
<script>
const allData = {music_json};
function cleanName(name) {{
  const n = (name || "").toLowerCase();
  if (n.includes("suno")) return "Suno";
  if (n.includes("udio")) return "Udio";
  if (n.includes("soundraw")) return "Soundraw";
  if (n.includes("aiva")) return "AIVA";
  if (n.includes("boomy")) return "Boomy";
  return name;
}}
function getPage(name) {{
  const map = {{
    "Suno": "pages/music/suno.html",
    "Udio": "pages/music/udio.html",
    "Soundraw": "pages/music/soundraw.html",
    "AIVA": "pages/music/aiva.html",
    "Boomy": "pages/music/boomy.html"
  }};
  return map[name] || "#";
}}
function estimateCost(plan) {{
  const price = plan.monthly_price_usd || 0;
  const credits = plan.credits_or_minutes || 0;
  if (!price || !credits || credits <= 0) return "";
  const costPerSong = price / credits;
  return costPerSong >= 0.01 ? ` (~$${{costPerSong.toFixed(2)}} / song)` : "";
}}
function createParticles(e) {{
  const x = e.clientX, y = e.clientY;
  for (let i = 0; i < 12; i++) {{
    const p = document.createElement("div");
    p.style.cssText = "position:fixed; width:6px; height:6px; background:#00d4ff; border-radius:50%; pointer-events:none; z-index:9999;";
    p.style.left = x + "px";
    p.style.top = y + "px";
    document.body.appendChild(p);
    const angle = Math.random() * Math.PI * 2;
    const speed = 2 + Math.random() * 4;
    const vx = Math.cos(angle) * speed;
    const vy = Math.sin(angle) * speed;
    let px = x, py = y, life = 30;
    const anim = setInterval(() => {{
      px += vx; py += vy; life--;
      p.style.left = px + "px";
      p.style.top = py + "px";
      p.style.opacity = life / 30;
      if (life <= 0) {{ clearInterval(anim); p.remove(); }}
    }}, 16);
  }}
}}
const order = ["Suno","Udio","Soundraw","AIVA","Boomy"];
const content = document.getElementById("content");
const platforms = [];
for (const [file, data] of Object.entries(allData)) {{
  if (!data) continue;
  const name = cleanName(data.platform || file.replace("-pricing.json",""));
  platforms.push({{ name, data }});
}}
platforms.sort((a, b) => {{
  const ai = order.indexOf(a.name), bi = order.indexOf(b.name);
  if (ai === -1 && bi === -1) return a.name.localeCompare(b.name);
  if (ai === -1) return 1;
  if (bi === -1) return -1;
  return ai - bi;
}});
for (const {{ name, data }} of platforms) {{
  const page = getPage(name);
  const checked = data.last_checked || data.checked || "recently";
  const source = data.source || data.source_url || "";
  let html = `<div class="card"><h2><a href="${{page}}" onclick="createParticles(event)">${{name}}</a></h2>`;
  if (source) {{
    html += `<div style="font-size:0.75em; opacity:0.6; margin-bottom:8px;">Checked: ${{checked}} · <a href="${{source}}" target="_blank" style="color:#00d4ff;">Source</a></div>`;
  }} else {{
    html += `<div style="font-size:0.75em; opacity:0.6; margin-bottom:8px;">Checked: ${{checked}}</div>`;
  }}
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

with open(os.path.join(folder, "music.html"), "w", encoding="utf-8") as f:
    f.write(music_html)
print("music.html regenerated.")