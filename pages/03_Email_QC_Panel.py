# pages/03_Email_QC_Panel.py  (Teacher View - frozen UI)
import streamlit as st
import pandas as pd
import re
from io import BytesIO, StringIO

st.set_page_config(page_title="SME QC Panel", layout="wide", initial_sidebar_state="collapsed")

# ==== HARD HIDE THE SIDEBAR & widen main ====
st.markdown("""
<style>
/* remove sidebar & its toggle */
[data-testid="stSidebar"]{display:none !important;}
[data-testid="collapsedControl"]{display:none !important;}
/* widen content and tighten paddings */
.main .block-container{max-width:1200px;padding:12px 16px 18px 16px;}
/* titles and separators */
.qc-title{font-size:14px;font-weight:700;margin:0 0 6px 0;color:#e5e5e5;}
.qc-hr{height:1px;border:0;margin:8px 0;}
.qc-hr.top{background:#63d063;}
.qc-hr.mid{background:#4f92ff;}
/* blocks */
.qc-edit{height:36vh;border-radius:10px;background:rgba(255,255,255,0.04);}
.qc-ref{height:20vh;overflow:auto;line-height:1.35;color:#eaeaea;padding:6px 10px;text-align:justify;font-size:16px;}
.qc-ref p{margin:4px 0;}
.qc-label{font-size:12px;opacity:.85;margin:0 0 4px 0;}
</style>
""", unsafe_allow_html=True)

# ===== helpers =====
def _clean(s):
    if s is None: return ""
    s = str(s).replace("**"," ").replace("\\r"," ").replace("\\n"," ").replace("\r"," ").replace("\n"," ")
    return re.sub(r"\s+"," ",s).strip()

def _read_any(up):
    name = (up.name or "").lower()
    data = up.read()
    if name.endswith((".xlsx",".xls")):
        return pd.read_excel(BytesIO(data))
    # CSV fallbacks
    try:
        return pd.read_csv(StringIO(data.decode("utf-8")))
    except Exception:
        return pd.read_csv(StringIO(data.decode("latin-1")))

def _auto_pick(cols, candidates):
    low = {c.lower(): c for c in cols}
    for c in candidates:
        if c.lower() in low: return low[c.lower()]
    return None

def _guess_mapping(df):
    cols = list(df.columns)
    return {
        "en.q": _auto_pick(cols, ["en.q","en_q","question","Question","Q","question_en"]),
        "en.o": _auto_pick(cols, ["en.o","en_o","options","Options","questionOptions"]),
        "en.a": _auto_pick(cols, ["en.a","en_a","answer","Answer","answers"]),
        "en.e": _auto_pick(cols, ["en.e","en_e","explanation","Explanation","explanations"]),
        "ta.q": _auto_pick(cols, ["ta.q","ta_q","taQuestion","question_ta","கேள்வி"]),
        "ta.o": _auto_pick(cols, ["ta.o","ta_o","taOptions","options_ta","விருப்பங்கள்"]),
        "ta.a": _auto_pick(cols, ["ta.a","ta_a","taAnswer","answer_ta","பதில்"]),
        "ta.e": _auto_pick(cols, ["ta.e","ta_e","taExplanation","explanation_ta","விளக்கம்"]),
    }

def _mk_ta(row, m):
    q,o,a,e = (_clean(row.get(m.get("ta.q",""),"")),
               _clean(row.get(m.get("ta.o",""),"")),
               _clean(row.get(m.get("ta.a",""),"")),
               _clean(row.get(m.get("ta.e",""),"")))
    parts = ["<div class='qc-label'>தமிழ் மூலப் பதிப்பு</div>"]
    if q: parts.append(f"<p><b>கேள்வி :</b> {q}</p>")
    if o: parts.append(f"<p><b>விருப்பங்கள் (A–D) :</b> {o}</p>")
    if a: parts.append(f"<p><b>பதில் :</b> {a}</p>")
    if e: parts.append(f"<p><b>விளக்கம் :</b> {e}</p>")
    if len(parts)==1: parts.append("<p><i>(தமிழ் பத்திகள் இல்லை)</i></p>")
    return "".join(parts)

def _mk_en(row, m):
    q,o,a,e = (_clean(row.get(m.get("en.q",""),"")),
               _clean(row.get(m.get("en.o",""),"")),
               _clean(row.get(m.get("en.a",""),"")),
               _clean(row.get(m.get("en.e",""),"")))
    parts = ["<div class='qc-label'>English Version</div>"]
    if q: parts.append(f"<p><b>Q :</b> {q}</p>")
    if o: parts.append(f"<p><b>Options (A–D) :</b> {o}</p>")
    if a: parts.append(f"<p><b>Answer :</b> {a}</p>")
    if e: parts.append(f"<p><b>Explanation :</b> {e}</p>")
    if len(parts)==1: parts.append("<p><i>(English columns missing)</i></p>")
    return "".join(parts)

# ===== top: minimal uploader (kept simple so teachers can still load a file) =====
up = st.file_uploader("Upload Excel/CSV, then click Load", type=["xlsx","xls","csv"])
if st.button("Load"):
    if up is None:
        st.warning("Choose a file first.")
    else:
        try:
            st.session_state["qc_df"] = _read_any(up)
            # if admin previously saved mapping, keep it; else guess now
            st.session_state.setdefault("mapping", _guess_mapping(st.session_state["qc_df"]))
            st.success("Loaded from file.")
        except Exception as e:
            st.error(f"Could not read the file: {e}")

df = st.session_state.get("qc_df")
if df is None or df.empty:
    st.stop()

mapping = st.session_state.get("mapping") or _guess_mapping(df)
row = df.iloc[0]

# ===== THE FROZEN TEACHER VIEW =====
st.markdown("<div class='qc-title'>SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி</div>", unsafe_allow_html=True)
st.text_area(" ", key="sme_edit_ta", height=int(0.36*800/1), label_visibility="collapsed",
             placeholder="Editable Tamil (SME)")

st.markdown("<hr class='qc-hr top'/>", unsafe_allow_html=True)
st.markdown(f"<div class='qc-ref'>{_mk_ta(row, mapping)}</div>", unsafe_allow_html=True)

st.markdown("<hr class='qc-hr mid'/>", unsafe_allow_html=True)
st.markdown(f"<div class='qc-ref'>{_mk_en(row, mapping)}</div>", unsafe_allow_html=True)
