import streamlit as st
import json
import os
import glob
import base64

st.set_page_config(page_title="GenCost", layout="wide", page_icon="💰")

folder = os.path.dirname(os.path.abspath(__file__))
bg_path = os.path.join(folder, "background.jpg")
if os.path.exists(bg_path):
    with open(bg_path, "rb") as f:
        bg_base64 = base64.b64encode(f.read()).decode()
    st.markdown(f"""
    <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{bg_base64}");
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
        }}
        .stApp header {{ background-color: transparent; }}
        h1, h2, h3, .stMarkdown, .stCaption {{ color: #ffffff !important; text-shadow: 0 0 8px rgba(0,0,0,0.8); }}
    </style>
    """, unsafe_allow_html=True)

st.title("GenCost")
st.caption("AI Video Price Comparison – October 2026")
st.info("Use the sidebar to open individual platform pages.")

def clean_name(name):
    n = name.strip().lower()
    if "heygen" in n: return "HeyGen"
    if "kling" in n: return "Kling AI"
    if "ltx" in n: return "LTX Studio"
    if "invideo" in n: return "InVideo"
    if "capcut" in n: return "CapCut"
    if "higgs" in n: return "Higgsfield"
    if "runway" in n: return "Runway"
    if "synth" in n: return "Synthesia"
    if "pika" in n: return "Pika"
    if "luma" in n: return "Luma"
    if "viggle" in n: return "Viggle"
    return name.strip().title()

files = glob.glob(os.path.join(folder, "*-pricing.json"))
platforms = {}
for path in files:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            raw = data.get("platform") or os.path.basename(path).replace("-pricing.json", "")
            name = clean_name(raw)
            platforms[name] = data
    except:
        pass

order = ["HeyGen", "Higgsfield", "Runway", "Kling AI", "Synthesia", "Pika", "Luma", "Viggle", "InVideo", "CapCut", "LTX Studio"]
sorted_names = [n for n in order if n in platforms] + [n for n in platforms if n not in order]

cols = st.columns(3)
for i, name in enumerate(sorted_names):
    with cols[i % 3]:
        st.subheader(name)
        for plan in platforms[name].get("plans", []):
            price = plan.get("monthly_price_usd", 0)
            credits = plan.get("credits_or_minutes", "-")
            unit = plan.get("unit", "")
            st.write(f"**{plan.get('name', 'Plan')}**: ${price}/mo · {credits} {unit}")
        st.write("")

st.divider()
st.caption("Prices update automatically.")
