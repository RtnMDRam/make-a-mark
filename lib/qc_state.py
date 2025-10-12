# pages/03_Email_QC_Panel.py
import re
import streamlit as st
from lib.top_strip import render_top_strip   # keep your existing top bar

# ========== CSS ==========
CSS = """
<style>
:root{
  --ref-vh: 20;        /* each reference block height (% of viewport) */
  --sep-top:#63d063;   /* green line between SME -> Tamil */
  --sep-mid:#4f92ff;   /* blue line between Tamil -> English */
}

.block-container{padding-top:10px !important; padding-bottom:10px !important;}

.qc-title{
  font-size:14px !important; font-weight:700 !important; margin:0 0 6px 0 !important;
  color:#e5e5e5 !important;
}

/* SME editor placeholder (top) */
.qc-edit{
  height:36vh; border-radius:10px; margin:0 0 8px 0 !important;
  background:rgba(255,255,255,0.04);
}

/* thin separators */
.qc-hr{height:1px !important; border:0 !important; margin:6px 0 !important;}
.qc-hr.top{background:var(--sep-top)!important;}
.qc-hr.mid{background:var(--sep-mid)!important;}

/* reference display boxes */
.qc-ref{
  height:calc(var(--ref-vh) * 1vh) !important;
  overflow:auto !important;
  white-space:normal !important;
  word-break:break-word !important;
  font-size:16px !important;            /* readable */
  line-height:1.3 !important;
  color:#eaeaea !important;
  padding:2px 6px !important;
  margin:0 !important;
  text-align:justify !important;
}
.qc-ref p{margin:4px 0 !important;}
.qc-label{font-size:12px; opacity:0.8; margin:0 0 4px 2px;}
</style>
"""

# ========== helpers ==========
def clean_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s).replace("\\r", " ").replace("\\n", " ")
    s = re.sub(r"\s+", " ", s)
    # in case the source has Markdown **, remove it so we don’t see literal stars
    s = s.replace("**", "")
    return s.strip()

def pick(row: dict, keys) -> str:
    for k in keys:
        if k in row and str(row[k]).strip() not in ("", "nan", "None"):
            return clean_text(row[k])
    return ""

def english_html(row: dict) -> str:
    q = pick(row, ["en.q","en_q","question","Question","question_en"])
    o = pick(row, ["en.o","en_o","options","Options","questionOptions"])
    a = pick(row, ["en.a","en_a","answer","Answer","answers"])
    e = pick(row, ["en.e","en_e","explanation","Explanation","explanations"])
    parts = ["<div class='qc-label'>English Version</div>"]
    if q: parts.append(f"<p><b>Q :</b> {q}</p>")
    if o: parts.append(f"<p><b>Options (A–D) :</b> {o}</p>")
    if a: parts.append(f"<p><b>Answer :</b> {a}</p>")
    if e: parts.append(f"<p><b>Explanation :</b> {e}</p>")
    if len(parts) == 1: parts.append("<p><i>(No English columns found in this row)</i></p>")
    return "".join(parts)

def tamil_html(row: dict) -> str:
    q = pick(row, ["ta.q","ta_q","taQuestion","question_ta"])
    o = pick(row, ["ta.o","ta_o","options_ta","taOptions"])
    a = pick(row, ["ta.a","ta_a","answer_ta","taAnswer"])
    e = pick(row, ["ta.e","ta_e","explanation_ta","taExplanation"])
    parts = ["<div class='qc-label'>தமிழ் மூலப் பதிப்பு</div>"]
    if q: parts.append(f"<p><b>கேள்வி :</b> {q}</p>")
    if o: parts.append(f"<p><b>விருப்பங்கள் (A–D) :</b> {o}</p>")
    if a: parts.append(f"<p><b>பதில் :</b> {a}</p>")
    if e: parts.append(f"<p><b>விளக்கம் :</b> {e}</p>")
    if len(parts) == 1: parts.append("<p><i>(தமிழ் பத்திகள் இந்த வரிசையில் இல்லை)</i></p>")
    return "".join(parts)

# ========== page ==========
st.set_page_config(page_title="SME QC Panel", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

def main():
    # top bar + load
    render_top_strip()

    df = st.session_state.get("qc_df")
    st.markdown("<div class='qc-title'>SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி</div>", unsafe_allow_html=True)
    st.markdown("<div class='qc-edit'></div>", unsafe_allow_html=True)

    # If nothing loaded yet
    if df is None or len(df) == 0:
        st.info("Paste a link or upload a file at the top strip, then press **Load**.")
        return

    # use the first row for preview (same as before)
    row = df.iloc[0].to_dict()

    # Tamil block
    st.markdown("<hr class='qc-hr top'/>", unsafe_allow_html=True)
    st.markdown(f"<div class='qc-ref'>{tamil_html(row)}</div>", unsafe_allow_html=True)

    # English block
    st.markdown("<hr class='qc-hr mid'/>", unsafe_allow_html=True)
    st.markdown(f"<div class='qc-ref'>{english_html(row)}</div>", unsafe_allow_html=True)

    # ---- tiny debug: shows columns detected (to verify why text might be missing)
    with st.expander("Debug: Detected columns", expanded=False):
        st.write(list(df.columns))
        st.json({k: row.get(k, "") for k in row.keys()})

if __name__ == "__main__":
    main()
