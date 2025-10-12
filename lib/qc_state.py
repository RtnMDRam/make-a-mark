# lib/qc_state.py
import streamlit as st

# ========= CSS (layout, sizes, separators, typography) =========
_QC_CSS = """
<style>
:root{
  /* Each reference pane = 20% viewport height (total 40%) */
  --ref-vh: 20;
  --sep-h: 1px;
  --sep-top: #63d063;   /* between SME & Tamil */
  --sep-mid: #4f92ff;   /* between Tamil & English */
}

/* tighten page padding a bit */
.block-container{padding-top:10px !important; padding-bottom:10px !important;}

/* section headings (small, compact) */
.qc-title{
  font-size:13px !important;
  font-weight:700 !important;
  margin:0 0 6px 0 !important;
  color:var(--text-color, #d8d8d8) !important;
}

/* big SME editor box (empty surface, no border) */
.qc-edit{
  height:36vh;            /* you can tweak this if you want */
  border-radius:10px;
  background:rgba(255,255,255,.04); /* subtle dark surface in dark theme */
  margin:0 0 8px 0 !important;
}

/* thin separators (single line) */
.qc-hr{height:var(--sep-h) !important; border:0 !important; margin:6px 0 !important;}
.qc-hr.top{background:var(--sep-top) !important;}
.qc-hr.mid{background:var(--sep-mid) !important;}

/* non-editable reference blocks */
.qc-ref{
  height:calc(var(--ref-vh) * 1vh) !important;
  overflow:auto !important;
  white-space:normal !important;
  word-break:break-word !important;
  font-size:14px !important;        /* larger text */
  line-height:1.25 !important;      /* tighter but readable */
  padding:4px 0 !important;
  margin:0 !important;
}
.qc-ref p, .qc-ref ul, .qc-ref ol{margin:4px 0 !important;}
.qc-ref ul, .qc-ref ol{padding-left:18px !important; margin-left:18px !important;}
.qc-ref strong{font-weight:600 !important;}
.qc-label{font-size:12px; opacity:.8; margin:0 0 4px 0;}
</style>
"""

# ========= helpers =========
def _get_df():
    return st.session_state.get("qc_df")

def _first(row, keys, default=""):
    for k in keys:
        if k in row and str(row[k]).strip() not in ("", "nan", "None"):
            return str(row[k]).strip()
    return default

def _english_block(row):
    q = _first(row, ["en.q","Question","question","question_en","enQ"])
    o = _first(row, ["en.o","Options","questionOptions","options","enOptions"])
    a = _first(row, ["en.a","Answer","answers","answer","enAnswer"])
    e = _first(row, ["en.e","Explanation","explanation","enExplanation"])
    md = []
    if q: md.append(f"**Q :** {q}")
    if o: md.append(f"**Options (A–D) :** {o}")
    if a: md.append(f"**Answer :** {a}")
    if e: md.append(f"**Explanation :** {e}")
    return "<div class='qc-label'>English Version</div>" + "<br/>".join(md) if md else "<div class='qc-label'>English Version</div>"

def _tamil_block(row):
    q = _first(row, ["ta.q","question_ta","taQ"])
    o = _first(row, ["ta.o","options_ta","taOptions"])
    a = _first(row, ["ta.a","answer_ta","taAnswer"])
    e = _first(row, ["ta.e","explanation_ta","taExplanation"])
    md = []
    if q: md.append(f"**கேள்வி :** {q}")
    if o: md.append(f"**விருப்பங்கள் (A–D) :** {o}")
    if a: md.append(f"**பதில் :** {a}")
    if e: md.append(f"**விளக்கம் :** {e}")
    return "<div class='qc-label'>தமிழ் மூலப் பதிப்பு</div>" + "<br/>".join(md) if md else "<div class='qc-label'>தமிழ் மூலப் பதிப்பு</div>"

# ========= main renderer (keeps layout order fixed) =========
def render_reference_and_editor():
    """
    FINAL ORDER (fixed, panels TOUCH with thin single lines):
      1) TOP   : SME Edit (Tamil)        — big dark surface (no border)
      2) LINE  : thin green divider
      3) MIDDLE: Tamil reference (20vh)  — non-editable
      4) LINE  : thin blue divider
      5) BOTTOM: English reference (20vh) — non-editable
    """
    st.markdown(_QC_CSS, unsafe_allow_html=True)

    # SME editor title + surface (empty, you’ll wire real inputs later)
    st.markdown("<div class='qc-title'>SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி</div>", unsafe_allow_html=True)
    st.markdown("<div class='qc-edit'></div>", unsafe_allow_html=True)

    # Prepare content from the first row (or empty)
    df = _get_df()
    if df is not None and len(df) > 0:
        row = df.iloc[0].to_dict()
        ta_md = _tamil_block(row)
        en_md = _english_block(row)
    else:
        ta_md = "<div class='qc-label'>தமிழ் மூலப் பதிப்பு</div>"
        en_md = "<div class='qc-label'>English Version</div>"

    # Tamil reference
    st.markdown("<hr class='qc-hr top'/>", unsafe_allow_html=True)
    st.markdown(f"<div class='qc-ref'>{ta_md}</div>", unsafe_allow_html=True)

    # English reference
    st.markdown("<hr class='qc-hr mid'/>", unsafe_allow_html=True)
    st.markdown(f"<div class='qc-ref'>{en_md}</div>", unsafe_allow_html=True)
