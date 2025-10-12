# lib/qc_state.py
import streamlit as st

# --- compact CSS: remove gaps, keep cards touching ---
_LAYOUT_CSS = """
<style>
[data-testid="stSidebar"]{display:none !important;}
.block-container{padding-top:12px;padding-bottom:12px;}
.card{border-radius:12px; padding:16px 18px; margin:0;}               /* no vertical gaps */
.card + .card{margin-top:6px;}                                        /* hairline only */
.ta-card{background:#eaf7e7;}     /* light green */
.en-card{background:#eaf1ff;}     /* light blue */
.ed-card{background:#fff6d6;}     /* light yellow */
.card h4{margin:0 0 10px 0; font-size:16px;}
.row{display:grid; grid-template-columns:1fr; gap:8px;}
.label{font-weight:600;}
.sep{opacity:.65;}
/* tighten reference lines */
.pair{display:grid; grid-template-columns:auto 1fr; gap:8px; align-items:start;}
</style>
"""

def _line(label, value="—"):
    st.markdown(
        f"""<div class="pair">
              <div class="label">{label}</div>
              <div class="sep">: {value}</div>
            </div>""",
        unsafe_allow_html=True,
    )

def _editor_tamil():
    st.markdown('<div class="card ed-card">', unsafe_allow_html=True)
    st.markdown('<h4>SME Edit Console / ஆசிரியர் திருத்தம் (Tamil)</h4>', unsafe_allow_html=True)
    st.text_area("கேள்வி", value="", height=80, label_visibility="collapsed", key="ed_q_ta")
    st.text_input("விருப்பங்கள் (A–D)", value="", label_visibility="visible", key="ed_opts_ta")
    st.text_input("பதில்", value="", label_visibility="visible", key="ed_ans_ta")
    st.text_area("விளக்கம்", value="", height=120, label_visibility="visible", key="ed_ex_ta")
    st.markdown('</div>', unsafe_allow_html=True)

def _reference_tamil():
    st.markdown('<div class="card ta-card">', unsafe_allow_html=True)
    st.markdown('<h4>தமிழ் மூலப் பதிப்பு</h4>', unsafe_allow_html=True)
    _line("கேள்வி")
    _line("விருப்பங்கள் (A–D)")
    _line("பதில்")
    _line("விளக்கம்")
    st.markdown('</div>', unsafe_allow_html=True)

def _reference_english():
    st.markdown('<div class="card en-card">', unsafe_allow_html=True)
    st.markdown('<h4>English Version</h4>', unsafe_allow_html=True)
    _line("Q")
    _line("Options (A–D)")
    _line("Answer")
    _line("Explanation")
    st.markdown('</div>', unsafe_allow_html=True)

def render_layout_only():
    """Freeze the order: Editor (top) -> Tamil reference (middle) -> English reference (bottom)."""
    st.markdown(_LAYOUT_CSS, unsafe_allow_html=True)

    # Cards TOUCH each other (no space). Order is locked:
    _editor_tamil()       # TOP (editable Tamil)
    _reference_tamil()    # MIDDLE (non-editable Tamil)
    _reference_english()  # BOTTOM (non-editable English)
