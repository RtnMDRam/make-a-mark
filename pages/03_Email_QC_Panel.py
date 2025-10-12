# pages/03_Email_QC_Panel.py
import streamlit as st
import pandas as pd
import re
from io import BytesIO, StringIO

st.set_page_config(page_title="SME QC Panel", layout="wide")

# ========== STYLE ==========
st.markdown("""
<style>
:root{ --ref-vh:20; }
.block-container{padding-top:10px !important; padding-bottom:10px !important;}
.qc-title{font-size:14px;font-weight:700;margin:0 0 6px 0;color:#e5e5e5;}
.qc-edit{height:36vh;border-radius:10px;background:rgba(255,255,255,0.04);margin-bottom:8px;}
.qc-hr{height:1px;border:0;margin:6px 0;}
.qc-hr.top{background:#63d063;}
.qc-hr.mid{background:#4f92ff;}
.qc-ref{
  height:calc(var(--ref-vh)*1vh);
  overflow:auto;
  line-height:1.35;
  color:#eaeaea;
  padding:4px 8px;
  text-align:justify;
  font-size:16px;         /* teacher default */
}
.qc-ref p{margin:4px 0;}
.qc-label{font-size:12px;opacity:.85;margin:0 0 4px 0;}
</style>
""", unsafe_allow_html=True)

# ========== HELPERS ==========
def _clean(s):
    if s is None: return ""
    s = str(s).replace("**"," ").replace("\\r"," ").replace("\\n"," ").replace("\r"," ").replace("\n"," ")
    return re.sub(r"\s+"," ",s).strip()

def _read_any(up):
    name = (up.name or "").lower()
    data = up.read()
    if name.endswith((".xlsx",".xls")):
        return pd.read_excel(BytesIO(data))
    try:
        return pd.read_csv(StringIO(data.decode("utf-8")))
    except Exception:
        return pd.read_csv(StringIO(data.decode("latin-1")))

def _auto_pick(cols, candidates):
    low = {c.lower(): c for c in cols}
    for c in candidates:
        if c.lower() in low: return low[c.lower()]
    return None

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

# ========== MODE ==========
params = st.experimental_get_query_params()
MODE = (params.get("mode",[None])[0] or "teacher").lower()   # "teacher" | "admin"

# ========== HEADER + UPLOAD (both modes) ==========
st.subheader("Email QC Panel")
lc, rc = st.columns([3,1])
with lc:
    up = st.file_uploader("Upload Excel/CSV", type=["xlsx","xls","csv"], label_visibility="collapsed")
with rc:
    load_btn = st.button("Load", use_container_width=True)

if load_btn:
    if up is None:
        st.warning("Please choose a file first.")
    else:
        try:
            st.session_state["qc_df"] = _read_any(up)
            st.session_state.setdefault("mapping", _guess_mapping(st.session_state["qc_df"]))
            st.success("Loaded from file.")
        except Exception as e:
            st.error(f"Could not read the file: {e}")

df = st.session_state.get("qc_df")
if df is None or df.empty:
    st.info("Please upload a file and press **Load**.")
    st.stop()

# persist mapping from admin
mapping = st.session_state.get("mapping") or _guess_mapping(df)
row = df.iloc[0]

# ========== ADMIN EXTRAS (one-time setup) ==========
if MODE == "admin":
    st.info("Admin Mode — set column mapping and reference font once; teachers see a clean page.")
    cols = list(df.columns)
    with st.expander("Column Mapping", expanded=True):
        cl, cr = st.columns(2)
        with cl:
            mapping["en.q"] = st.selectbox("en.q (Question)", [None]+cols, index=([None]+cols).index(mapping.get("en.q")) if mapping.get("en.q") in cols else 0)
            mapping["en.o"] = st.selectbox("en.o (Options)" , [None]+cols, index=([None]+cols).index(mapping.get("en.o")) if mapping.get("en.o") in cols else 0)
            mapping["en.a"] = st.selectbox("en.a (Answer)"  , [None]+cols, index=([None]+cols).index(mapping.get("en.a")) if mapping.get("en.a") in cols else 0)
            mapping["en.e"] = st.selectbox("en.e (Explanation)", [None]+cols, index=([None]+cols).index(mapping.get("en.e")) if mapping.get("en.e") in cols else 0)
        with cr:
            mapping["ta.q"] = st.selectbox("ta.q (கேள்வி)", [None]+cols, index=([None]+cols).index(mapping.get("ta.q")) if mapping.get("ta.q") in cols else 0)
            mapping["ta.o"] = st.selectbox("ta.o (விருப்பங்கள்)", [None]+cols, index=([None]+cols).index(mapping.get("ta.o")) if mapping.get("ta.o") in cols else 0)
            mapping["ta.a"] = st.selectbox("ta.a (பதில்)", [None]+cols, index=([None]+cols).index(mapping.get("ta.a")) if mapping.get("ta.a") in cols else 0)
            mapping["ta.e"] = st.selectbox("ta.e (விளக்கம்)", [None]+cols, index=([None]+cols).index(mapping.get("ta.e")) if mapping.get("ta.e") in cols else 0)
        st.session_state["mapping"] = mapping

    fs = st.slider("Reference text size (teacher view will use this)", 13, 20, value=16)
    st.markdown(f"<style>.qc-ref{{font-size:{fs}px;}}</style>", unsafe_allow_html=True)

# ========== TEACHER LAYOUT (minimal) ==========
st.markdown("<div class='qc-title'>SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி</div>", unsafe_allow_html=True)
# editable Tamil box (placeholder only — wire to your save logic)
st.text_area(" ", key="sme_edit_ta", height=int(0.36*st.session_state.get("viewport_h", 800)),
             label_visibility="collapsed", placeholder="Editable Tamil (SME)")

# line above Tamil ref
st.markdown("<hr class='qc-hr top'/>", unsafe_allow_html=True)
# Tamil reference
st.markdown(f"<div class='qc-ref'>{_mk_ta(row, mapping)}</div>", unsafe_allow_html=True)
# line above English ref
st.markdown("<hr class='qc-hr mid'/>", unsafe_allow_html=True)
# English reference
st.markdown(f"<div class='qc-ref'>{_mk_en(row, mapping)}</div>", unsafe_allow_html=True)
