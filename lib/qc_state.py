# lib/qc_state.py
import streamlit as st

# --- layout css: add borders + remove big gaps + hide any old separators ----
_LAYOUT_CSS = """
<style>
/* hide Streamlit left sidebar */
[data-testid="stSidebar"]{display:none!important;}

/* tighten page paddings a bit */
.block-container{padding-top:10px; padding-bottom:12px;}

/* CARD look: border + compact padding, tiny vertical gap only */
.card{
  background:#ffffff;
  border:1px solid #d0d7de;          /* <— outer line */
  border-radius:10px;
  padding:14px 16px;
  margin:0;
}
/* Only a hairline gap between stacked cards */
.card + .card{ margin-top:6px; }

/* light tints (optional, very subtle) */
.ta-card{ background:#f5fbf5; }       /* Tamil reference (green tint) */
.en-card{ background:#f6f8ff; }       /* English reference (blue tint) */
.ed-card{ background:#fffaf0; }       /* Editable Tamil (warm tint) */

/* compact headings & labels */
.card h4{ margin:0 0 8px 0; font-size:18px; font-weight:700; }
.label{ font-weight:600; }

/* if a previous build injected a colored separator bar, hide it */
.sep{ display:none !important; }

/* Two-column helper (not used yet, but kept) */
.row{ display:grid; grid-template-columns:1fr; gap:8px; }
.pair{ display:grid; grid-template-columns:auto 1fr; gap:8px; align-items:start; }
</style>
"""

def _line(label, value="—"):
    st.markdown(
        f"""
        <div class="pair">
          <div class="label">{label}</div>
          <div>{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------ PANELS (layout only; no data wiring yet) -----------------

def _editor_tamil():
    st.markdown('<div class="card ed-card">', unsafe_allow_html=True)
    st.markdown('<h4>SME Edit Console / ஆசிரியர் திருத்தம் (Tamil)</h4>', unsafe_allow_html=True)
    st.text_area("கேள்வி", value="", height=80, label_visibility="collapsed", key="ed_q_ta")
    st.text_input("விருப்பங்கள் (A–D)", value="", label_visibility="visible", key="ed_opts_ta")
    st.text_input("பதில்", value="", label_visibility="visible", key="ed_ans_ta")
    st.text_area("விளக்கம்", value="", height=120, label_visibility="visible", key="ed_ex_ta")
    st.markdown("</div>", unsafe_allow_html=True)

def _reference_tamil():
    st.markdown('<div class="card ta-card">', unsafe_allow_html=True)
    st.markdown('<h4>தமிழ் மூலப் பதிப்பு</h4>', unsafe_allow_html=True)
    _line("கேள்வி")
    _line("விருப்பங்கள் (A–D)")
    _line("பதில்")
    _line("விளக்கம்")
    st.markdown("</div>", unsafe_allow_html=True)

def _reference_english():
    st.markdown('<div class="card en-card">', unsafe_allow_html=True)
    st.markdown('<h4>English Version</h4>', unsafe_allow_html=True)
    _line("Q")
    _line("Options (A–D)")
    _line("Answer")
    _line("Explanation")
    st.markdown("</div>", unsafe_allow_html=True)

def render_layout_only():
    """
    Freeze the order: EDITOR (top) → Tamil reference (middle) → English reference (bottom)
    Cards are bordered and almost touching (6px gap). No extra separators.
    """
    st.markdown(_LAYOUT_CSS, unsafe_allow_html=True)
    _editor_tamil()       # TOP   (editable Tamil)
    _reference_tamil()    # MIDDLE (non-editable Tamil)
    _reference_english()  # BOTTOM (non-editable English)
