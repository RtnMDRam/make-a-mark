# lib/qc_state.py
import streamlit as st

# ---------- CSS: proper visible box outlines, no vertical gap ----------
_LAYOUT_CSS = """
<style>
[data-testid="stSidebar"] {display:none !important;}
.block-container {padding-top:10px;padding-bottom:10px;}

/* PANEL BOXES */
.panel {
  background: #ffffff !important;
  border: 2px solid #1f2937 !important; /* dark grey visible outline */
  border-radius: 6px;
  padding: 16px 18px;
  margin: 0;
  overflow: auto;
  box-shadow: 0px 0px 4px rgba(0,0,0,0.05);
}

/* Touching panels (no gap) */
.panel + .panel {
  margin-top: 0 !important;
  border-top: none !important; /* remove double borders when stacked */
}

/* Section colors for clarity */
.panel.ed {border-color: #334155 !important;}  /* SME editable Tamil */
.panel.ta {border-color: #15803d !important;}  /* Tamil reference */
.panel.en {border-color: #1d4ed8 !important;}  /* English reference */

/* Fixed height layout: 40%, 25%, 25% */
.panel.ed {min-height: 40vh;}
.panel.ta {min-height: 25vh;}
.panel.en {min-height: 25vh;}

/* Headings */
.panel h4 {
  margin: 0 0 12px 0;
  font-size: 18px;
  font-weight: 700;
  color: #111827;
}

/* Label rows */
.row {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px;
  align-items: start;
}
.label {font-weight: 600; color: #334155;}
.sep {opacity: 0.8;}

/* Compact text inputs */
.stTextArea textarea, .stTextInput input {
  font-size: 16px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
}

/* Remove extra spacing between panels */
hr, .stDivider, [data-testid="stDivider"] {
  display: none !important;
  height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}
</style>
"""

def _line(label, value="—"):
    st.markdown(
        f"""
        <div class="row">
            <div class="label">{label}</div>
            <div class="sep">: {value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def _editor_tamil():
    st.markdown('<div class="panel ed">', unsafe_allow_html=True)
    st.markdown('<h4>SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி</h4>', unsafe_allow_html=True)
    st.text_area("கேள்வி", value="", height=80, label_visibility="collapsed", key="ed_q_ta")
    st.text_input("விருப்பங்கள் (A–D)", value="", label_visibility="visible", key="ed_opts_ta")
    st.text_input("பதில்", value="", label_visibility="visible", key="ed_ans_ta")
    st.text_area("விளக்கம்", value="", height=120, label_visibility="visible", key="ed_ex_ta")
    st.markdown('</div>', unsafe_allow_html=True)

def _reference_tamil():
    st.markdown('<div class="panel ta">', unsafe_allow_html=True)
    st.markdown('<h4>தமிழ் மூலப் பதிப்பு</h4>', unsafe_allow_html=True)
    _line("கேள்வி"); _line("விருப்பங்கள் (A–D)"); _line("பதில்"); _line("விளக்கம்")
    st.markdown('</div>', unsafe_allow_html=True)

def _reference_english():
    st.markdown('<div class="panel en">', unsafe_allow_html=True)
    st.markdown('<h4>English Version</h4>', unsafe_allow_html=True)
    _line("Q"); _line("Options (A–D)"); _line("Answer"); _line("Explanation")
    st.markdown('</div>', unsafe_allow_html=True)

def render_layout_only():
    """Fixed order: Editor (top) → Tamil reference (middle) → English reference (bottom)."""
    st.markdown(_LAYOUT_CSS, unsafe_allow_html=True)
    _editor_tamil()
    _reference_tamil()
    _reference_english()
