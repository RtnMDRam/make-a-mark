# pages/03_Email_QC_Panel.py
import streamlit as st
import pandas as pd
import re
from io import BytesIO, StringIO

# ---------------- STYLES ----------------
CSS = """
<style>
:root{
  --ref-vh:20;        /* Tamil + English each 20vh -> total ~40vh */
  --sep-top:#63d063;  /* green line between SME edit and Tamil ref */
  --sep-mid:#4f92ff;  /* blue line between Tamil ref and English ref */
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
  font-size:16px;
  line-height:1.36;
  color:#eaeaea;
  padding:4px 8px;
  text-align:justify;
}
.qc-ref p{margin:4px 0;}
.qc-label{font-size:12px;opacity:0.85;margin-bottom:4px;}
.qc-help{font-size:13px;opacity:.85;}
</style>
"""

st.set_page_config(page_title="SME QC Panel", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def _clean(s):
    if s is None: return ""
    s = str(s).replace("\\r", " ").replace("\\n", " ")
    s = re.sub(r"\s+", " ", s)
    s = s.replace("**","")  # strip accidental markdown bold markers
    return s.strip()

def _pick(row, keys):
    for k in keys:
        if k in row and str(row[k]).strip() not in ("", "nan", "None"):
            return _clean(row[k])
    return ""

def _tamil_html(row):
    q = _pick(row, ["ta.q","ta_q","taQuestion","question_ta"])
    o = _pick(row, ["ta.o","ta_o","taOptions","options_ta"])
    a = _pick(row, ["ta.a","ta_a","taAnswer","answer_ta"])
    e = _pick(row, ["ta.e","ta_e","taExplanation","explanation_ta"])
    html = ["<div class='qc-label'>தமிழ் மூலப் பதிப்பு</div>"]
    if q: html.append(f"<p><b>கேள்வி :</b> {q}</p>")
    if o: html.append(f"<p><b>விருப்பங்கள் (A–D) :</b> {o}</p>")
    if a: html.append(f"<p><b>பதில் :</b> {a}</p>")
    if e: html.append(f"<p><b>விளக்கம் :</b> {e}</p>")
    if len(html)==1: html.append("<p><i>(தமிழ் பத்திகள் இல்லை)</i></p>")
    return "".join(html)

def _english_html(row):
    q = _pick(row, ["en.q","en_q","question","Question","question_en"])
    o = _pick(row, ["en.o","en_o","options","Options","questionOptions"])
    a = _pick(row, ["en.a","en_a","answer","Answer","answers"])
    e = _pick(row, ["en.e","en_e","explanation","Explanation","explanations"])
    html = ["<div class='qc-label'>English Version</div>"]
    if q: html.append(f"<p><b>Q :</b> {q}</p>")
    if o: html.append(f"<p><b>Options (A–D) :</b> {o}</p>")
    if a: html.append(f"<p><b>Answer :</b> {a}</p>")
    if e: html.append(f"<p><b>Explanation :</b> {e}</p>")
    if len(html)==1: html.append("<p><i>(English columns missing)</i></p>")
    return "".join(html)

def _read_any(file):
    name = (file.name or "").lower()
    data = file.read()
    # reset pointer so pandas can read again if needed
    bio = BytesIO(data)
    if name.endswith(".xlsx") or name.endswith(".xls"):
        # engine auto works on Streamlit Cloud; fallback is openpyxl
        return pd.read_excel(bio)
    # try CSV (utf-8); if it fails, fallback to latin-1
    try:
        return pd.read_csv(StringIO(data.decode("utf-8")))
    except Exception:
        return pd.read_csv(StringIO(data.decode("latin-1")))

# ---------------- TOP CONTROLS (ALWAYS VISIBLE) ----------------
st.subheader("Email QC Panel")
c1, c2 = st.columns([3,1])
with c1:
    file = st.file_uploader("Upload the Excel/CSV here", type=["xlsx","xls","csv"])
with c2:
    load_clicked = st.button("Load", use_container_width=True)

if load_clicked:
    if file is None:
        st.warning("Please choose a file first.")
    else:
        try:
            df = _read_any(file)
            st.session_state["qc_df"] = df
            st.success("Loaded from file.")
        except Exception as e:
            st.error(f"Could not read the file: {e}")

# ---------------- LAYOUT ----------------
st.markdown("<div class='qc-title'>SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி</div>", unsafe_allow_html=True)
st.markdown("<div class='qc-edit'></div>", unsafe_allow_html=True)

df = st.session_state.get("qc_df")

if df is None or len(df)==0:
    st.info("Please upload a file and press **Load**.")
else:
    row = df.iloc[0].to_dict()
    # separator line & Tamil reference
    st.markdown("<hr class='qc-hr top'/>", unsafe_allow_html=True)
    st.markdown(f"<div class='qc-ref'>{_tamil_html(row)}</div>", unsafe_allow_html=True)
    # separator line & English reference
    st.markdown("<hr class='qc-hr mid'/>", unsafe_allow_html=True)
    st.markdown(f"<div class='qc-ref'>{_english_html(row)}</div>", unsafe_allow_html=True)

    with st.expander("Debug Columns"):
        st.write(list(df.columns))
        st.markdown(
            "<div class='qc-help'>If Tamil is blank, check the exact header names here. "
            "Accepted Tamil headers include ta.q / ta.o / ta.a / ta.e. "
            "English headers include en.q / en.o / en.a / en.e or question / options / answers / explanation.</div>",
            unsafe_allow_html=True
        )
