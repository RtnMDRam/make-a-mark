# pages/03_Email_QC_Panel.py
import streamlit as st
import pandas as pd
import re
from io import BytesIO, StringIO

st.set_page_config(page_title="SME QC Panel", layout="wide")

# ---------- Styles ----------
st.markdown("""
<style>
:root{
  --ref-vh:20;              /* each reference box = 20vh (Tamil 20 + English 20 ~ 40% total) */
  --sep-top:#63d063;        /* green line between SME edit and Tamil ref */
  --sep-mid:#4f92ff;        /* blue line between Tamil ref and English ref */
}
.block-container{padding-top:10px !important; padding-bottom:10px !important;}
.qc-title{font-size:14px;font-weight:700;margin:0 0 6px 0;color:#e5e5e5;}
.qc-edit{height:36vh;border-radius:10px;background:rgba(255,255,255,0.04);margin-bottom:8px;}
.qc-hr{height:1px;border:0;margin:6px 0;}
.qc-hr.top{background:var(--sep-top);}
.qc-hr.mid{background:var(--sep-mid);}
.qc-ref{
  height:calc(var(--ref-vh)*1vh);
  overflow:auto;
  line-height:1.35;
  color:#eaeaea;
  padding:4px 8px;
  text-align:justify;
}
.qc-ref p{margin:4px 0;}
.qc-label{font-size:12px;opacity:.85;margin:0 0 4px 0;}
.qc-help{font-size:13px;opacity:.85;}
.badge{display:inline-block;background:#1f6feb;color:#fff;border-radius:999px;padding:2px 8px;font-size:12px;}
</style>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
def _clean_val(s:str) -> str:
    if s is None: return ""
    s = str(s)
    # remove **, stray CR/LF artifacts, collapse whitespace
    s = s.replace("**", " ").replace("\\r", " ").replace("\\n", " ").replace("\r", " ").replace("\n", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def _read_any(uploaded):
    name = (uploaded.name or "").lower()
    data = uploaded.read()
    bio = BytesIO(data)
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(bio)
    # CSV paths
    try:
        return pd.read_csv(StringIO(data.decode("utf-8")))
    except Exception:
        return pd.read_csv(StringIO(data.decode("latin-1")))

def _auto_pick(cols, candidates):
    """Return the first existing column from 'candidates'."""
    low = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in low:
            return low[cand.lower()]
    return None

def _get_text(row, colname):
    if not colname: return ""
    if colname not in row: return ""
    return _clean_val(row[colname])

def _mk_ta_html(row, m):
    q = _get_text(row, m.get("ta.q"))
    o = _get_text(row, m.get("ta.o"))
    a = _get_text(row, m.get("ta.a"))
    e = _get_text(row, m.get("ta.e"))
    parts = ["<div class='qc-label'>தமிழ் மூலப் பதிப்பு</div>"]
    if q: parts.append(f"<p><b>கேள்வி :</b> {q}</p>")
    if o: parts.append(f"<p><b>விருப்பங்கள் (A–D) :</b> {o}</p>")
    if a: parts.append(f"<p><b>பதில் :</b> {a}</p>")
    if e: parts.append(f"<p><b>விளக்கம் :</b> {e}</p>")
    if len(parts) == 1:
        parts.append("<p><i>(தமிழ் பத்திகள் இல்லை)</i></p>")
    return "".join(parts)

def _mk_en_html(row, m):
    q = _get_text(row, m.get("en.q"))
    o = _get_text(row, m.get("en.o"))
    a = _get_text(row, m.get("en.a"))
    e = _get_text(row, m.get("en.e"))
    parts = ["<div class='qc-label'>English Version</div>"]
    if q: parts.append(f"<p><b>Q :</b> {q}</p>")
    if o: parts.append(f"<p><b>Options (A–D) :</b> {o}</p>")
    if a: parts.append(f"<p><b>Answer :</b> {a}</p>")
    if e: parts.append(f"<p><b>Explanation :</b> {e}</p>")
    if len(parts) == 1:
        parts.append("<p><i>(English columns missing)</i></p>")
    return "".join(parts)

# ---------- Top controls (always visible) ----------
st.subheader("Email QC Panel")

lc, rc = st.columns([3,1])
with lc:
    up = st.file_uploader("Upload Excel/CSV", type=["xlsx","xls","csv"])
with rc:
    btn = st.button("Load", use_container_width=True)

if btn:
    if up is None:
        st.warning("Please choose a file first.")
    else:
        try:
            st.session_state["qc_df"] = _read_any(up)
            st.success("Loaded from file.")
        except Exception as e:
            st.error(f"Could not read the file: {e}")

df = st.session_state.get("qc_df")

# SME edit placeholder + line above Tamil
st.markdown("<div class='qc-title'>SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி</div>", unsafe_allow_html=True)
st.markdown("<div class='qc-edit'></div>", unsafe_allow_html=True)
st.markdown("<hr class='qc-hr top'/>", unsafe_allow_html=True)

if df is None or df.empty:
    st.info("Please upload a file and press **Load**.")
    st.stop()

# ---------- Column Mapper (auto guess + override) ----------
cols = list(df.columns)

# robust guesses (both compact and long headers)
guesses = {
    "en.q": _auto_pick(cols, ["en.q","en_q","question","Question","question_en","Q"]),
    "en.o": _auto_pick(cols, ["en.o","en_o","options","Options","questionOptions"]),
    "en.a": _auto_pick(cols, ["en.a","en_a","answer","Answer","answers"]),
    "en.e": _auto_pick(cols, ["en.e","en_e","explanation","Explanation","explanations"]),
    "ta.q": _auto_pick(cols, ["ta.q","ta_q","taQuestion","question_ta","கேள்வி"]),
    "ta.o": _auto_pick(cols, ["ta.o","ta_o","taOptions","options_ta","விருப்பங்கள்"]),
    "ta.a": _auto_pick(cols, ["ta.a","ta_a","taAnswer","answer_ta","பதில்"]),
    "ta.e": _auto_pick(cols, ["ta.e","ta_e","taExplanation","explanation_ta","விளக்கம்"]),
}

with st.expander("Column Mapper (auto-guessed)"):
    cl, cr = st.columns(2)
    with cl:
        st.caption("English")
        en_q = st.selectbox("en.q (Question)", [None] + cols, index=( [None]+cols ).index(guesses["en.q"]) if guesses["en.q"] in cols else 0)
        en_o = st.selectbox("en.o (Options)",  [None] + cols, index=( [None]+cols ).index(guesses["en.o"]) if guesses["en.o"] in cols else 0)
        en_a = st.selectbox("en.a (Answer)",   [None] + cols, index=( [None]+cols ).index(guesses["en.a"]) if guesses["en.a"] in cols else 0)
        en_e = st.selectbox("en.e (Explanation)", [None] + cols, index=( [None]+cols ).index(guesses["en.e"]) if guesses["en.e"] in cols else 0)
    with cr:
        st.caption("Tamil")
        ta_q = st.selectbox("ta.q (கேள்வி)",      [None] + cols, index=( [None]+cols ).index(guesses["ta.q"]) if guesses["ta.q"] in cols else 0)
        ta_o = st.selectbox("ta.o (விருப்பங்கள்)", [None] + cols, index=( [None]+cols ).index(guesses["ta.o"]) if guesses["ta.o"] in cols else 0)
        ta_a = st.selectbox("ta.a (பதில்)",        [None] + cols, index=( [None]+cols ).index(guesses["ta.a"]) if guesses["ta.a"] in cols else 0)
        ta_e = st.selectbox("ta.e (விளக்கம்)",     [None] + cols, index=( [None]+cols ).index(guesses["ta.e"]) if guesses["ta.e"] in cols else 0)
    st.caption("Tip: If Tamil shows '(தமிழ் பத்திகள் இல்லை)', set Tamil fields to the correct headers above.")

mapping = {"en.q": en_q, "en.o": en_o, "en.a": en_a, "en.e": en_e,
           "ta.q": ta_q, "ta.o": ta_o, "ta.a": ta_a, "ta.e": ta_e}

# ---------- Read row 0 and render with user-selected mapping ----------
row = df.iloc[0]

# Font size control (fits iPad nicely)
fs = st.slider("Reference text size", min_value=13, max_value=20, value=16, step=1)
st.markdown(
    f"<style>.qc-ref{{font-size:{fs}px;}}</style>",
    unsafe_allow_html=True
)

# Tamil reference
st.markdown(f"<div class='qc-ref'>{_mk_ta_html(row, mapping)}</div>", unsafe_allow_html=True)

# separator + English reference
st.markdown("<hr class='qc-hr mid'/>", unsafe_allow_html=True)
st.markdown(f"<div class='qc-ref'>{_mk_en_html(row, mapping)}</div>", unsafe_allow_html=True)

with st.expander("Debug Columns"):
    st.write(list(df.columns))
    st.markdown(
        "<div class='qc-help'>If a field is empty, pick the correct column in the Column Mapper above.</div>",
        unsafe_allow_html=True
    )
