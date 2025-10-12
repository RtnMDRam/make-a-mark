# pages/03_Email_QC_Panel.py  — Teacher view (strict 20vh refs, full content)
import streamlit as st
import pandas as pd
import re
from io import BytesIO, StringIO

st.set_page_config(page_title="SME QC Panel", layout="wide", initial_sidebar_state="collapsed")

# ───────────────────────── CSS (tight layout, iPad-safe 20vh) ─────────────────
st.markdown("""
<style>
/* hide sidebar & “>” nub */
[data-testid="stSidebar"], [data-testid="collapsedControl"]{display:none!important;}
/* page padding */
.main .block-container{max-width:1200px;padding:10px 16px 14px 16px;}
/* separators */
.qc-hr{height:1px;border:0;margin:10px 0 4px;background:#63d063;}
.qc-hr.mid{background:#4f92ff;margin-top:8px;}
/* inline section label glued to line */
.qc-label{font-size:12px;opacity:.9;margin:0 0 2px 0;}
/* reference areas: EXACT 20vh on iPad/desktop */
.qc-ref{
  height:20dvh;                 /* iPad/iOS dynamic viewport */
  min-height:20vh;              /* desktop fallback */
  overflow:auto;
  padding:4px 8px;
  line-height:1.32;
  text-align:justify;
  color:#eaeaea;
  /* sized to “fill but not shout” on tablets */
  font-size:clamp(14px, 1.9vh, 18px);
}
.qc-ref p{margin:3px 0;}
/* SME editor */
.qc-edit{height:36dvh; min-height:36vh;}
/* tighten st.text_area internal paddings on mobile */
textarea{padding:8px!important; line-height:1.32!important;}
</style>
""", unsafe_allow_html=True)

# ───────────────────────────── helpers ────────────────────────────────────────
def _clean(s):
    if s is None: return ""
    s = str(s)
    s = s.replace("**"," ")                      # remove markdown stars
    s = s.replace("\\r"," ").replace("\\n"," ")
    s = s.replace("\r"," ").replace("\n"," ")
    return re.sub(r"\s+"," ",s).strip()

def _read_any(up):
    name = (up.name or "").lower()
    data = up.read()
    if name.endswith((".xlsx",".xls")):
        return pd.read_excel(BytesIO(data))
    # CSV fallbacks
    try:    return pd.read_csv(StringIO(data.decode("utf-8")))
    except: return pd.read_csv(StringIO(data.decode("latin-1")))

def _auto_pick(cols, candidates):
    low = {c.lower(): c for c in cols}
    for key in candidates:
        if key.lower() in low: return low[key.lower()]
    # soft contain search
    for key in candidates:
        for c in cols:
            if key.lower() in c.lower(): return c
    return None

def _guess_mapping(df):
    cols = list(df.columns)
    # include English variants AND Tamil literals
    return {
        "en.q": _auto_pick(cols, ["en.q","en_q","question_en","question","Q"]),
        "en.o": _auto_pick(cols, ["en.o","en_o","options","questionOptions"]),
        "en.a": _auto_pick(cols, ["en.a","en_a","answer","answers"]),
        "en.e": _auto_pick(cols, ["en.e","en_e","explanation","explanations"]),
        "ta.q": _auto_pick(cols, ["ta.q","ta_q","question_ta","கேள்வி","கேள்வி :","கேள்வி:"]),
        "ta.o": _auto_pick(cols, ["ta.o","ta_o","options_ta","விருப்பங்கள்","விருப்பங்கள் (A–D)","விருப்பங்கள் (A-D)"]),
        "ta.a": _auto_pick(cols, ["ta.a","ta_a","answer_ta","பதில்","பதில் :","பதில்:"]),
        "ta.e": _auto_pick(cols, ["ta.e","ta_e","explanation_ta","விளக்கம்","விளக்கம் :","விளக்கம்:"]),
    }

def _mk_ta(row, m):
    q = _clean(row.get(m.get("ta.q",""), ""))
    o = _clean(row.get(m.get("ta.o",""), ""))
    a = _clean(row.get(m.get("ta.a",""), ""))
    e = _clean(row.get(m.get("ta.e",""), ""))
    parts = ["<div class='qc-label'>தமிழ் மூலப் பதிப்பு</div>"]
    if q: parts.append(f"<p><b>கேள்வி :</b> {q}</p>")
    if o: parts.append(f"<p><b>விருப்பங்கள் (A–D) :</b> {o}</p>")
    if a: parts.append(f"<p><b>பதில் :</b> {a}</p>")
    if e: parts.append(f"<p><b>விளக்கம் :</b> {e}</p>")
    if len(parts)==1: parts.append("<p><i>(தமிழ் பத்திகள் இல்லை)</i></p>")
    return "".join(parts)

def _mk_en(row, m):
    q = _clean(row.get(m.get("en.q",""), ""))
    o = _clean(row.get(m.get("en.o",""), ""))
    a = _clean(row.get(m.get("en.a",""), ""))
    e = _clean(row.get(m.get("en.e",""), ""))
    parts = ["<div class='qc-label'>English Version</div>"]
    if q: parts.append(f"<p><b>Q :</b> {q}</p>")
    if o: parts.append(f"<p><b>Options (A–D) :</b> {o}</p>")
    if a: parts.append(f"<p><b>Answer :</b> {a}</p>")
    if e: parts.append(f"<p><b>Explanation :</b> {e}</p>")
    if len(parts)==1: parts.append("<p><i>(English columns missing)</i></p>")
    return "".join(parts)

# ─────────────────────────── top: file loader (simple) ────────────────────────
up = st.file_uploader("Upload Excel/CSV then press Load", type=["xlsx","xls","csv"])
if st.button("Load", type="primary"):
    if not up:
        st.warning("Choose a file first.")
    else:
        try:
            df = _read_any(up)
            st.session_state["qc_df"] = df
            st.session_state["mapping"] = _guess_mapping(df)
            st.success("Loaded from file.")
        except Exception as e:
            st.error(f"Could not read the file: {e}")

df = st.session_state.get("qc_df")
if df is None or df.empty:
    st.stop()

mapping = st.session_state.get("mapping") or _guess_mapping(df)
row = df.iloc[0]

# ─────────────────────────── Teacher view (frozen) ────────────────────────────
st.text_area("Editable Tamil (SME)", key="sme_edit_ta", height=0, placeholder="", help=None, label_visibility="visible", disabled=False)
st.markdown("<div class='qc-edit'></div>", unsafe_allow_html=True)  # visual area behind the textarea

# Tamil reference
st.markdown("<hr class='qc-hr'/>", unsafe_allow_html=True)
st.markdown(f"<div class='qc-ref'>{_mk_ta(row, mapping)}</div>", unsafe_allow_html=True)

# English reference
st.markdown("<hr class='qc-hr mid'/>", unsafe_allow_html=True)
st.markdown(f"<div class='qc-ref'>{_mk_en(row, mapping)}</div>", unsafe_allow_html=True)
