# lib/qc_state.py
import streamlit as st
import re

# ========== CSS ==========
_QC_CSS = """
<style>
:root{
  --ref-vh: 20;            /* each reference = 20% viewport height (total 40%) */
  --sep-top: #63d063;      /* SME -> Tamil */
  --sep-mid: #4f92ff;      /* Tamil -> English */
}
.block-container{padding-top:10px !important; padding-bottom:10px !important;}

.qc-title{
  font-size:13px !important;
  font-weight:700 !important;
  margin:0 0 6px 0 !important;
  color:var(--text-color, #dcdcdc) !important;
}

.qc-edit{
  height:36vh;
  border-radius:10px;
  background:rgba(255,255,255,.04);
  margin:0 0 8px 0 !important;
}

.qc-hr{height:1px !important; border:0 !important; margin:6px 0 !important;}
.qc-hr.top{background:var(--sep-top) !important;}
.qc-hr.mid{background:var(--sep-mid) !important;}

.qc-ref{
  height:calc(var(--ref-vh) * 1vh) !important;
  overflow:auto !important;
  font-size:15px !important;     /* larger text so area is filled */
  line-height:1.28 !important;
  padding:2px 0 0 0 !important;
  margin:0 !important;
  white-space:normal !important;
  word-break:break-word !important;
}
.qc-ref p{margin:4px 0 !important;}
.qc-ref ul, .qc-ref ol{margin:4px 0 4px 18px !important; padding-left:18px !important;}
.qc-label{font-size:12px; opacity:.85; margin:0 0 4px 0;}
</style>
"""

# ========== helpers ==========
def _df():
    return st.session_state.get("qc_df")

def _val(row: dict, keys, default=""):
    """Return first non-empty value for any of the given keys."""
    for k in keys:
        if k in row:
            v = row[k]
            if v is None: 
                continue
            s = str(v).strip()
            if s and s.lower() not in ("nan", "none"):
                return s
    return default

def _clean_text(s: str) -> str:
    """Make text render cleanly inside HTML (remove escaped newlines etc.)."""
    s = s.replace("\\r", " ").replace("\\n", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _english_html(row):
    q = _clean_text(_val(row, ["en.q","en_q","enQ","Question","question","question_en","enQuestion"]))
    o = _clean_text(_val(row, ["en.o","en_o","Options","questionOptions","options","options_en","enOptions"]))
    a = _clean_text(_val(row, ["en.a","en_a","Answer","answers","answer","answer_en","enAnswer"]))
    e = _clean_text(_val(row, ["en.e","en_e","Explanation","explanation","explanation_en","enExplanation"]))
    parts = ["<div class='qc-label'>English Version</div>"]
    if q: parts.append(f"<p><b>Q :</b> {q}</p>")
    if o: parts.append(f"<p><b>Options (A–D) :</b> {o}</p>")
    if a: parts.append(f"<p><b>Answer :</b> {a}</p>")
    if e: parts.append(f"<p><b>Explanation :</b> {e}</p>")
    return "".join(parts)

def _tamil_html(row):
    q = _clean_text(_val(row, ["ta.q","ta_q","taQ","question_ta","taQuestion"]))
    o = _clean_text(_val(row, ["ta.o","ta_o","options_ta","taOptions"]))
    a = _clean_text(_val(row, ["ta.a","ta_a","answer_ta","taAnswer"]))
    e = _clean_text(_val(row, ["ta.e","ta_e","explanation_ta","taExplanation"]))
    parts = ["<div class='qc-label'>தமிழ் மூலப் பதிப்பு</div>"]
    if q: parts.append(f"<p><b>கேள்வி :</b> {q}</p>")
    if o: parts.append(f"<p><b>விருப்பங்கள் (A–D) :</b> {o}</p>")
    if a: parts.append(f"<p><b>பதில் :</b> {a}</p>")
    if e: parts.append(f"<p><b>விளக்கம் :</b> {e}</p>")
    return "".join(parts)

# ========== renderer ==========
def render_reference_and_editor():
    """
    Order (fixed):
      SME Editor (top) -> thin green line -> Tamil reference (20vh)
      -> thin blue line -> English reference (20vh)
    """
    st.markdown(_QC_CSS, unsafe_allow_html=True)

    # Title + SME surface
    st.markdown("<div class='qc-title'>SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி</div>", unsafe_allow_html=True)
    st.markdown("<div class='qc-edit'></div>", unsafe_allow_html=True)

    # Pick first row (or blanks)
    row = {}
    df = _df()
    if df is not None and len(df) > 0:
        row = df.iloc[0].to_dict()

    # Tamil reference
    st.markdown("<hr class='qc-hr top'/>", unsafe_allow_html=True)
    st.markdown(f"<div class='qc-ref'>{_tamil_html(row)}</div>", unsafe_allow_html=True)

    # English reference
    st.markdown("<hr class='qc-hr mid'/>", unsafe_allow_html=True)
    st.markdown(f"<div class='qc-ref'>{_english_html(row)}</div>", unsafe_allow_html=True)
