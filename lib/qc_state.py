# lib/qc_state.py
import streamlit as st
import re

# ========= CSS STYLES =========
_QC_CSS = """
<style>
:root{
  --ref-vh: 20;        /* each reference area 20% viewport height */
  --sep-top: #63d063;  /* green line: SME→Tamil */
  --sep-mid: #4f92ff;  /* blue line: Tamil→English */
}

/* Layout and typography */
.block-container {padding-top:10px !important; padding-bottom:10px !important;}

.qc-title {
  font-size:14px !important; font-weight:700 !important;
  margin:0 0 6px 0 !important; color:#e5e5e5 !important;
}

.qc-edit {
  height:36vh; border-radius:10px;
  background:rgba(255,255,255,0.04);
  margin:0 0 8px 0 !important;
}

/* divider lines */
.qc-hr {height:1px !important; border:0 !important; margin:6px 0 !important;}
.qc-hr.top {background:var(--sep-top) !important;}
.qc-hr.mid {background:var(--sep-mid) !important;}

/* reference (Tamil & English display blocks) */
.qc-ref {
  height:calc(var(--ref-vh) * 1vh) !important;
  overflow:auto !important;
  white-space:normal !important;
  word-break:break-word !important;
  font-size:15px !important;
  line-height:1.3 !important;
  color:#eaeaea !important;
  padding:2px 6px !important;
  margin:0 !important;
  text-align:justify !important;
}
.qc-ref p {margin:4px 0 !important;}
.qc-label {font-size:12px; opacity:0.8; margin:0 0 4px 2px;}
</style>
"""

# ========= HELPER FUNCTIONS =========
def _get_df():
    return st.session_state.get("qc_df")

def _clean_text(s):
    if not s:
        return ""
    s = str(s).replace("\\r", " ").replace("\\n", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def _val(row, keys):
    """Return first non-empty value from candidate keys."""
    for k in keys:
        if k in row and str(row[k]).strip() not in ("", "nan", "None"):
            return _clean_text(row[k])
    return ""

def _english_html(row):
    q = _val(row, ["en.q", "en_q", "question", "Question", "question_en"])
    o = _val(row, ["en.o", "en_o", "options", "Options", "questionOptions"])
    a = _val(row, ["en.a", "en_a", "answer", "Answer", "answers"])
    e = _val(row, ["en.e", "en_e", "explanation", "Explanation", "explanations"])
    html = ["<div class='qc-label'>English Version</div>"]
    if q: html.append(f"<p><b>Q :</b> {q}</p>")
    if o: html.append(f"<p><b>Options (A–D) :</b> {o}</p>")
    if a: html.append(f"<p><b>Answer :</b> {a}</p>")
    if e: html.append(f"<p><b>Explanation :</b> {e}</p>")
    return "".join(html)

def _tamil_html(row):
    q = _val(row, ["ta.q", "ta_q", "taQuestion", "question_ta"])
    o = _val(row, ["ta.o", "ta_o", "options_ta", "taOptions"])
    a = _val(row, ["ta.a", "ta_a", "answer_ta", "taAnswer"])
    e = _val(row, ["ta.e", "ta_e", "explanation_ta", "taExplanation"])
    html = ["<div class='qc-label'>தமிழ் மூலப் பதிப்பு</div>"]
    if q: html.append(f"<p><b>கேள்வி :</b> {q}</p>")
    if o: html.append(f"<p><b>விருப்பங்கள் (A–D) :</b> {o}</p>")
    if a: html.append(f"<p><b>பதில் :</b> {a}</p>")
    if e: html.append(f"<p><b>விளக்கம் :</b> {e}</p>")
    return "".join(html)

# ========= MAIN RENDERER =========
def render_reference_and_editor():
    """
    Layout order:
      1. SME editor (top)
      2. Green line
      3. Tamil reference (20vh)
      4. Blue line
      5. English reference (20vh)
    """
    st.markdown(_QC_CSS, unsafe_allow_html=True)
    st.markdown("<div class='qc-title'>SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி</div>", unsafe_allow_html=True)
    st.markdown("<div class='qc-edit'></div>", unsafe_allow_html=True)

    row = {}
    df = _get_df()
    if df is not None and len(df) > 0:
        row = df.iloc[0].to_dict()

    # Tamil non-editable block
    st.markdown("<hr class='qc-hr top'/>", unsafe_allow_html=True)
    st.markdown(f"<div class='qc-ref'>{_tamil_html(row)}</div>", unsafe_allow_html=True)

    # English non-editable block
    st.markdown("<hr class='qc-hr mid'/>", unsafe_allow_html=True)
    st.markdown(f"<div class='qc-ref'>{_english_html(row)}</div>", unsafe_allow_html=True)
