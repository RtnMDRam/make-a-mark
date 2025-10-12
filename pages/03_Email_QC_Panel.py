# pages/03_Email_QC_Panel.py — fixed height version (no StreamlitInvalidHeightError)
import streamlit as st
import pandas as pd
import re
from io import BytesIO, StringIO

st.set_page_config(page_title="SME QC Panel", layout="wide", initial_sidebar_state="collapsed")

# ───────────────────────── CSS ─────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"], [data-testid="collapsedControl"]{display:none!important;}
.main .block-container{max-width:1200px;padding:10px 16px 14px 16px;}
.qc-hr{height:1px;border:0;margin:8px 0 4px;background:#63d063;}
.qc-hr.mid{background:#4f92ff;margin-top:6px;}
.qc-label{font-size:12px;opacity:.9;margin:0 0 2px 0;}
.qc-ref{
  height:20dvh;min-height:20vh;
  overflow:auto;padding:4px 8px;
  line-height:1.32;text-align:justify;
  color:#eaeaea;font-size:clamp(14px,1.9vh,18px);
}
.qc-ref p{margin:3px 0;}
.qc-edit{height:36dvh;min-height:36vh;}
</style>
""", unsafe_allow_html=True)

# ───────────────────────── Helpers ─────────────────────
def _clean(s):
    if s is None: return ""
    s = str(s)
    s = s.replace("**"," ").replace("\\r"," ").replace("\\n"," ").replace("\r"," ").replace("\n"," ")
    return re.sub(r"\s+"," ",s).strip()

def _read_any(up):
    name = (up.name or "").lower()
    data = up.read()
    if name.endswith((".xlsx",".xls")): return pd.read_excel(BytesIO(data))
    try: return pd.read_csv(StringIO(data.decode("utf-8")))
    except: return pd.read_csv(StringIO(data.decode("latin-1")))

def _auto_pick(cols, cands):
    low = {c.lower(): c for c in cols}
    for c in cands:
        if c.lower() in low: return low[c.lower()]
    for c in cands:
        for x in cols:
            if c.lower() in x.lower(): return x
    return None

def _guess_mapping(df):
    cols = list(df.columns)
    return {
        "en.q": _auto_pick(cols, ["en.q","en_q","question","Q"]),
        "en.o": _auto_pick(cols, ["en.o","en_o","options","questionOptions"]),
        "en.a": _auto_pick(cols, ["en.a","en_a","answer","answers"]),
        "en.e": _auto_pick(cols, ["en.e","en_e","explanation","explanations"]),
        "ta.q": _auto_pick(cols, ["ta.q","ta_q","question_ta","கேள்வி"]),
        "ta.o": _auto_pick(cols, ["ta.o","ta_o","options_ta","விருப்பங்கள்"]),
        "ta.a": _auto_pick(cols, ["ta.a","ta_a","answer_ta","பதில்"]),
        "ta.e": _auto_pick(cols, ["ta.e","ta_e","explanation_ta","விளக்கம்"]),
    }

def _mk_ta(row,m):
    q,o,a,e=[_clean(row.get(m.get(k,""),"")) for k in["ta.q","ta.o","ta.a","ta.e"]]
    out=["<div class='qc-label'>தமிழ் மூலப் பதிப்பு</div>"]
    if q: out.append(f"<p><b>கேள்வி :</b> {q}</p>")
    if o: out.append(f"<p><b>விருப்பங்கள் (A–D) :</b> {o}</p>")
    if a: out.append(f"<p><b>பதில் :</b> {a}</p>")
    if e: out.append(f"<p><b>விளக்கம் :</b> {e}</p>")
    if len(out)==1: out.append("<p><i>(தமிழ் பத்திகள் இல்லை)</i></p>")
    return "".join(out)

def _mk_en(row,m):
    q,o,a,e=[_clean(row.get(m.get(k,""),"")) for k in["en.q","en.o","en.a","en.e"]]
    out=["<div class='qc-label'>English Version</div>"]
    if q: out.append(f"<p><b>Q :</b> {q}</p>")
    if o: out.append(f"<p><b>Options (A–D) :</b> {o}</p>")
    if a: out.append(f"<p><b>Answer :</b> {a}</p>")
    if e: out.append(f"<p><b>Explanation :</b> {e}</p>")
    if len(out)==1: out.append("<p><i>(English columns missing)</i></p>")
    return "".join(out)

# ───────────────────────── File Loader ─────────────────
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
            st.error(f"Could not read file: {e}")

df = st.session_state.get("qc_df")
if df is None or df.empty: st.stop()

mapping = st.session_state.get("mapping") or _guess_mapping(df)
row = df.iloc[0]

# ───────────────────────── Main View ───────────────────
# Fixed safe height for textarea (was 0 earlier)
st.text_area("Editable Tamil (SME)", key="sme_edit_ta", height=250)

st.markdown("<hr class='qc-hr'/>", unsafe_allow_html=True)
st.markdown(f"<div class='qc-ref'>{_mk_ta(row,mapping)}</div>", unsafe_allow_html=True)

st.markdown("<hr class='qc-hr mid'/>", unsafe_allow_html=True)
st.markdown(f"<div class='qc-ref'>{_mk_en(row,mapping)}</div>", unsafe_allow_html=True)
