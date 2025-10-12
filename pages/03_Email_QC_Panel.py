# 03_Email_QC_Panel.py
# Minimal, fixed layout: Tamil + English reference only (each 20vh).
import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="SME QC Panel", layout="wide")

# ---------- CSS (no sidebar, tight headings, 20vh panes) ----------
st.markdown("""
<style>
/* Hide sidebar & hamburger */
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display:none !important; }

/* Compact page padding */
.main .block-container { max-width: 1200px; padding: 10px 16px 16px; }

/* Slim colored separators */
.qc-hr{height:2px;border:0;margin:10px 0 6px;}
.qc-hr.ta{background:#22c55e;}     /* Tamil */
.qc-hr.en{background:#3b82f6;}     /* English */

/* Section label, stuck close to line */
.qc-h{font-size:12px;margin:0 0 2px 2px;opacity:.9;}

/* Read-only reference box: exactly 20vh, top-aligned, tighter line gaps */
.qc-ref{
  height:20dvh; min-height:20vh; max-height:20vh;
  overflow:auto; padding:2px 8px 6px; line-height:1.28;
  text-align:justify; color:#eaeaea;
  font-size:clamp(14px,1.95vh,18px);
}
.qc-ref p{margin:2px 0;}
</style>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
def _clean(x):
    if x is None: return ""
    s = str(x)
    s = s.replace("\\r\\n"," ").replace("\\n"," ").replace("\r\n"," ").replace("\n"," ")
    return re.sub(r"\s{2,}", " ", s).strip()

def _detect_mapping(cols):
    """Map expected keys -> actual df columns (case-insensitive + Tamil header lock)."""
    lc = {c.lower(): c for c in cols}
    # English
    en = {
        "en.q": ["en.q","question","en_question","q"],
        "en.o": ["en.o","questionoptions","options","choices","en_options"],
        "en.a": ["en.a","answers","answer","en_answer"],
        "en.e": ["en.e","explanation","en_explanation","exp"],
    }
    # Tamil (lock to your exact headers first)
    ta = {
        "ta.q": ["ta.q","tamil.q","ta_question","கேள்வி"],
        "ta.o": ["ta.o","tamil.o","ta_options","விருப்பங்கள்"],
        "ta.a": ["ta.a","tamil.a","ta_answer","பதில்"],
        "ta.e": ["ta.e","tamil.e","ta_explanation","விளக்கம்"],
    }
    m={}
    for k, cands in {**en, **ta}.items():
        found=None
        for c in cands:
            # exact Tamil names are case sensitive; others use lc
            if c in cols:
                found=c; break
            if c.lower() in lc:
                found=lc[c.lower()]; break
        m[k]=found
    return m

def _mk_en_html(row, m):
    q = _clean(row.get(m["en.q"])) if m["en.q"] else ""
    o = _clean(row.get(m["en.o"])) if m["en.o"] else ""
    a = _clean(row.get(m["en.a"])) if m["en.a"] else ""
    e = _clean(row.get(m["en.e"])) if m["en.e"] else ""
    parts=[]
    if q: parts.append(f"<p><b>Q :</b> {q}</p>")
    if o: parts.append(f"<p><b>Options (A–D) :</b> {o}</p>")
    if a: parts.append(f"<p><b>Answer :</b> {a}</p>")
    if e: parts.append(f"<p><b>Explanation :</b> {e}</p>")
    return "".join(parts) or "<i>No English content.</i>"

def _mk_ta_html(row, m):
    q = _clean(row.get(m["ta.q"])) if m["ta.q"] else ""
    o = _clean(row.get(m["ta.o"])) if m["ta.o"] else ""
    a = _clean(row.get(m["ta.a"])) if m["ta.a"] else ""
    e = _clean(row.get(m["ta.e"])) if m["ta.e"] else ""
    parts=[]
    if q: parts.append(f"<p><b>கேள்வி :</b> {q}</p>")
    if o: parts.append(f"<p><b>விருப்பங்கள் (A–D) :</b> {o}</p>")
    if a: parts.append(f"<p><b>பதில் :</b> {a}</p>")
    if e: parts.append(f"<p><b>விளக்கம் :</b> {e}</p>")
    return "".join(parts) or "<i>தமிழ் பதிவுகள் இல்லை.</i>"

def _load_df(uploaded):
    if not uploaded: return None
    name = uploaded.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded)
    data = uploaded.read()
    return pd.read_excel(io.BytesIO(data))

# ---------- UI: upload + load ----------
left, right = st.columns([1,3])
with left:
    file = st.file_uploader("Upload Excel/CSV", type=["xlsx","xls","csv"])
with right:
    if st.button("Load", use_container_width=True):
        df = _load_df(file)
        if df is None or df.empty:
            st.error("No rows found. Upload a valid file.")
        else:
            st.session_state.df = df
            st.session_state.map = _detect_mapping(df.columns)
            st.session_state.i = 0
            st.success("Loaded from file.")

df = st.session_state.get("df")
mp = st.session_state.get("map")
i  = st.session_state.get("i", 0)

# ---------- Render references only ----------
if df is None:
    st.info("Please upload a file and press **Load**.")
else:
    i = max(0, min(i, len(df)-1))
    row = df.iloc[i]

    # Tamil reference (20vh)
    st.markdown("<hr class='qc-hr ta'/>", unsafe_allow_html=True)
    st.markdown("<div class='qc-h'>தமிழ் மூலப் பதிவு</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='qc-ref'>{_mk_ta_html(row, mp)}</div>", unsafe_allow_html=True)

    # English reference (20vh)
    st.markdown("<hr class='qc-hr en'/>", unsafe_allow_html=True)
    st.markdown("<div class='qc-h'>English Version</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='qc-ref'>{_mk_en_html(row, mp)}</div>", unsafe_allow_html=True)
