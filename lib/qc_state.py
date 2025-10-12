# lib/qc_state.py
import streamlit as st

# --- Compact CSS: add outer borders and keep cards tight ----------------------
_LAYOUT_CSS = """
<style>
/* hide Streamlit left sidebar */
[data-testid="stSidebar"]{display:none !important;}
.block-container{padding-top:12px;padding-bottom:12px;}

/* CARD look: thin border, light background, rounded corners */
.card{
  border:1px solid #d7dde5;
  background:#f8fafc;
  border-radius:10px;
  padding:16px 18px;
  margin:0;
}
/* very small gap between stacked cards (keep tight) */
.card + .card{ margin-top:8px; }

/* per-card tints (keep subtle) */
.ed-card{ background:#f4f6f9; }   /* editable */
.ta-card{ background:#eaf7ea; }   /* Tamil reference */
.en-card{ background:#eaf1ff; }   /* English reference */

/* headings inside cards */
.card h4{ margin:0 0 10px 0; font-size:18px; }

/* reference rows: label on left, value on right, single line */
.row{
  display:grid;
  grid-template-columns:auto 1fr;
  gap:8px;
  align-items:start;
  margin:2px 0;
}
.label{ font-weight:600; color:#334155; }
.sep{ opacity:.6; }

/* editable inputs fill width */
.stTextArea textarea, .stTextInput input{ font-size:16px; }
</style>
"""

# --- small helpers -------------------------------------------------------------
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

# --- EDITOR (Tamil, on top) ----------------------------------------------------
def _editor_tamil():
  st.markdown('<div class="card ed-card">', unsafe_allow_html=True)
  # Title as you requested
  st.markdown('<h4>SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி</h4>', unsafe_allow_html=True)

  st.text_area("கேள்வி", value="", height=80, label_visibility="collapsed", key="ed_q_ta")
  st.text_input("விருப்பங்கள் (A–D)", value="", label_visibility="visible", key="ed_opts_ta")
  st.text_input("பதில்", value="", label_visibility="visible", key="ed_ans_ta")
  st.text_area("விளக்கம்", value="", height=120, label_visibility="visible", key="ed_ex_ta")

  st.markdown('</div>', unsafe_allow_html=True)

# --- READ-ONLY TAMIL (middle) --------------------------------------------------
def _reference_tamil():
  st.markdown('<div class="card ta-card">', unsafe_allow_html=True)
  st.markdown('<h4>தமிழ் மூலப் பதிப்பு</h4>', unsafe_allow_html=True)
  _line("கேள்வி")
  _line("விருப்பங்கள் (A–D)")
  _line("பதில்")
  _line("விளக்கம்")
  st.markdown('</div>', unsafe_allow_html=True)

# --- READ-ONLY ENGLISH (bottom) -----------------------------------------------
def _reference_english():
  st.markdown('<div class="card en-card">', unsafe_allow_html=True)
  st.markdown('<h4>English Version</h4>', unsafe_allow_html=True)
  _line("Q")
  _line("Options (A–D)")
  _line("Answer")
  _line("Explanation")
  st.markdown('</div>', unsafe_allow_html=True)

# --- PUBLIC: render only the layout (order locked, tight spacing) -------------
def render_layout_only():
  """Freeze the order: Editor (top) → Tamil (middle) → English (bottom)."""
  st.markdown(_LAYOUT_CSS, unsafe_allow_html=True)
  _editor_tamil()        # TOP (editable Tamil)
  _reference_tamil()     # MIDDLE (read-only Tamil)
  _reference_english()   # BOTTOM (read-only English)
