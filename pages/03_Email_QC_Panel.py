# pages/03_Email_QC_Panel.py
import re
import datetime as dt
from typing import Dict, Any

import pandas as pd
import streamlit as st

# Top bar (date/time + actions + link/upload already wired)
from lib.top_strip import render_top_strip


# -------------------------------------------------------
# Page + CSS (palm-leaf sheet look, thin green borders)
# -------------------------------------------------------
st.set_page_config(
    page_title="SME QC Panel",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* Hide Streamlit left nav for SMEs */
[data-testid="stSidebar"], [data-testid="stSidebarNav"] { display:none !important; }
.block-container { padding-top: .5rem !important; padding-bottom: 1rem !important; }

/* Sheet theme */
:root { --sheet-bg:#fbf4e2; --grid:#26803a; --soft:#dde7f8; --soft2:#e8f6e8; }
body { background: var(--sheet-bg) !important; }

/* Section bars */
.sheet-label {
  font-weight:600; margin: .25rem 0 .35rem 0;
}

/* Grid frame */
.frame { border: 2px solid var(--grid); border-radius: 6px; padding: 8px 10px; background: #fff; }
.row      { display:flex; gap:10px; }
.col      { flex:1; }
.col-2    { flex:2; }
.col-3    { flex:3; }
hr.thin   { border:none; border-top:1px solid var(--grid); margin:.5rem 0; }

/* Inputs compact */
.stTextInput, .stTextArea, .stSelectbox { margin-bottom:.35rem !important; }
textarea { line-height:1.3 !important; }

/* Cards for reference blocks */
.card      { border:2px solid var(--grid); border-radius:6px; background:#fff; padding:10px 12px; }
.card.ta   { background: #eef8ee; }
.card.en   { background: #eef3ff; }

/* Kill the floating “Manage app” button for SMEs */
button[aria-label="Manage app"] { display:none !important; }
</style>
""", unsafe_allow_html=True)


# -------------- Helpers --------------
def df_ready() -> bool:
    return isinstance(st.session_state.get("qc_df"), pd.DataFrame) and isinstance(st.session_state.get("qc_idx"), int)

def current_row() -> Dict[str, Any]:
    df: pd.DataFrame = st.session_state.get("qc_df")
    idx: int = st.session_state.get("qc_idx", 0)
    if df is None or df.empty: return {}
    idx = max(0, min(idx, len(df)-1))
    rec = df.iloc[idx]
    return rec.to_dict() if isinstance(rec, pd.Series) else dict(rec)

# Try to resolve columns whatever their names are
def pick(rec, patterns):
    for k,v in rec.items():
        name = str(k).lower()
        if any(re.search(p, name) for p in patterns):
            if pd.notna(v): return str(v).strip()
    return ""

def guess_fields(rec: Dict[str,Any]) -> Dict[str,str]:
    g = {k:"" for k in
         "q_ta A_ta B_ta C_ta D_ta ans_ta exp_ta q_en A_en B_en C_en D_en ans_en exp_en".split()}
    if not rec: return g
    # Direct name hits first
    def get(col): 
        v = rec.get(col, "")
        return str(v).strip() if pd.notna(v) else ""
    for k in g.keys():
        g[k] = get(k)

    # Fallbacks
    g["q_ta"]   = g["q_ta"]   or pick(rec, [r"^q.*ta", r"tamil.*q", r"q[_-]?ta"])
    g["A_ta"]   = g["A_ta"]   or pick(rec, [r"(^a$|^opt[_-]?a)", r"choice[_-]?a"])
    g["B_ta"]   = g["B_ta"]   or pick(rec, [r"(^b$|^opt[_-]?b)", r"choice[_-]?b"])
    g["C_ta"]   = g["C_ta"]   or pick(rec, [r"(^c$|^opt[_-]?c)", r"choice[_-]?c"])
    g["D_ta"]   = g["D_ta"]   or pick(rec, [r"(^d$|^opt[_-]?d)", r"choice[_-]?d"])
    g["ans_ta"] = g["ans_ta"] or pick(rec, [r"^ans.*ta", r"answer.*ta", r"tamil.*ans"])
    g["exp_ta"] = g["exp_ta"] or pick(rec, [r"^exp.*ta", r"expla.*ta", r"tamil.*exp"])

    g["q_en"]   = g["q_en"]   or pick(rec, [r"^q($|.*en)", r"english.*q"])
    for ch in "ABCD":
        k=f"{ch}_en"
        g[k] = g[k] or pick(rec,[fr"(^[{ch.lower()}|{ch}]$|^opt[_-]?{ch.lower()}|^opt[_-]?{ch})", fr"choice[_-]?{ch.lower()}"])
    g["ans_en"] = g["ans_en"] or pick(rec, [r"^ans($|.*en)", r"answer($|.*en)", r"english.*ans"])
    g["exp_en"] = g["exp_en"] or pick(rec, [r"^exp($|.*en)", r"expla($|.*en)", r"english.*exp"])
    return g


# -------------- UI --------------
render_top_strip()  # header (date/title/time + Save / Complete / Next / Download + link/upload)

if not df_ready():
    st.info("Paste a link or upload a file at the top strip to begin.")
    st.stop()

rec = current_row()
G   = guess_fields(rec)

# Unique suffix to keep widget keys stable per row
row_key = f"{st.session_state.get('qc_idx',0)}"

# ========== EDIT BLOCK (TOP) ==========
st.markdown('<div class="sheet-label">கேள்வி :</div>', unsafe_allow_html=True)
with st.container():
    # Question (full width)
    st.text_area(
        label="",
        value=G["q_ta"],
        key=f"q_ta_{row_key}",
        height=92
    )

    # Options grid A/B (left) vs C/D (right)
    left, right = st.columns(2)
    with left:
        st.text_input('Auto Display "A"', value=G["A_ta"], key=f"A_ta_{row_key}")
        st.text_input('Auto Display "B"', value=G["B_ta"], key=f"B_ta_{row_key}")
    with right:
        st.text_input('Auto Display "C"', value=G["C_ta"], key=f"C_ta_{row_key}")
        st.text_input('Auto Display "D"', value=G["D_ta"], key=f"D_ta_{row_key}")

    # Glossary (left) / Correct Answer (right)
    st.markdown('<hr class="thin">', unsafe_allow_html=True)
    gL, gR = st.columns(2)
    with gL:
        st.text_input('சொல் அகராதி / Glossary (Type the word )', key=f"gloss_{row_key}", value="")
    with gR:
        st.text_input('சரியான பதில் / Correct Answer (Auto from options if A/B/C/D)', 
                      key=f"ans_ta_{row_key}", value=G["ans_ta"])

    # Explanation
    st.markdown('<div class="sheet-label">விளக்கங்கள் :</div>', unsafe_allow_html=True)
    st.text_area("", value=G["exp_ta"], key=f"exp_ta_{row_key}", height=140)

st.markdown('<hr class="thin">', unsafe_allow_html=True)

# ========== TAMIL ORIGINAL (MIDDLE) ==========
st.markdown('<div class="sheet-label">தமிழ் அசல்</div>', unsafe_allow_html=True)
with st.container():
    with st.container():
        st.markdown(
            f"""
<div class="card ta">
<b>Q:</b> {G['q_ta'] or '—'}  
<b>Options (A–D):</b> {G['A_ta'] or '—'} | {G['B_ta'] or '—'} | {G['C_ta'] or '—'} | {G['D_ta'] or '—'}  
<b>Answer:</b> {G['ans_ta'] or '—'}  
<b>Explanation:</b> {G['exp_ta'] or '—'}
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="thin">', unsafe_allow_html=True)

# ========== ENGLISH (BOTTOM) ==========
st.markdown('<div class="sheet-label">English</div>', unsafe_allow_html=True)
with st.container():
    st.markdown(
        f"""
<div class="card en">
<b>Q:</b> {G['q_en'] or '—'}  
<b>Options (A–D):</b> {G['A_en'] or '—'} | {G['B_en'] or '—'} | {G['C_en'] or '—'} | {G['D_en'] or '—'}  
<b>Answer:</b> {G['ans_en'] or '—'}  
<b>Explanation:</b> {G['exp_en'] or '—'}
</div>
""", unsafe_allow_html=True)
