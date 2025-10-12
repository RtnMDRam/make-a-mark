# lib/qc_state.py
import streamlit as st

# ---------- CSS: single-line borders, zero gaps, no bars ----------
_LAYOUT_CSS = """
<style>
/* app paddings */
[data-testid="stSidebar"]{display:none !important;}
.block-container{padding-top:10px;padding-bottom:10px;}

/* generic card */
.card{
  background:#ffffff !important;
  border:1px solid #cbd5e1;      /* single thin line */
  border-radius:10px;
  padding:14px 16px;
  margin:0;                      /* no outer margin */
}

/* make cards TOUCH (no vertical gap) */
.card + .card{ margin-top:0 !important; }

/* individual border colors (line only) */
.ed-card{ border-color:#475569; }  /* editable (grey-blue) */
.ta-card{ border-color:#16a34a; }  /* Tamil (green) */
.en-card{ border-color:#3b82f6; }  /* English (blue) */

/* headings */
.card h4{ margin:0 0 10px 0; font-size:18px; font-weight:700; color:#111827; }

/* reference rows */
.row{ display:grid; grid-template-columns:auto 1fr; gap:8px; align-items:start; }
.label{ font-weight:600; color:#334155; }
.sep{ opacity:.75; }

/* inputs look clean & compact */
.stTextArea textarea, .stTextInput input{ font-size:16px; }

/* STRONG kill switches: remove any colored bars/dividers that might exist */
.ta-bar, .en-bar, .ed-bar,
hr, .stDivider, [data-testid="stDivider"], .stMarkdown div:empty{
  height:0 !important; margin:0 !important; padding:0 !important;
  border:0 !important; background:transparent !important; display:none !important;
}
</style>
"""

# ---------- small helpers ----------
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

# ---------- panels ----------
def _editor_tamil():
  st.markdown('<div class="card ed-card">', unsafe_allow_html=True)
  st.markdown('<h4>SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி</h4>', unsafe_allow_html=True)
  st.text_area("கேள்வி", value="", height=80, label_visibility="collapsed", key="ed_q_ta")
  st.text_input("விருப்பங்கள் (A–D)", value="", label_visibility="visible", key="ed_opts_ta")
  st.text_input("பதில்", value="", label_visibility="visible", key="ed_ans_ta")
  st.text_area("விளக்கம்", value="", height=120, label_visibility="visible", key="ed_ex_ta")
  st.markdown('</div>', unsafe_allow_html=True)

def _reference_tamil():
  st.markdown('<div class="card ta-card">', unsafe_allow_html=True)
  st.markdown('<h4>தமிழ் மூலப் பதிப்பு</h4>', unsafe_allow_html=True)
  _line("கேள்வி"); _line("விருப்பங்கள் (A–D)"); _line("பதில்"); _line("விளக்கம்")
  st.markdown('</div>', unsafe_allow_html=True)

def _reference_english():
  st.markdown('<div class="card en-card">', unsafe_allow_html=True)
  st.markdown('<h4>English Version</h4>', unsafe_allow_html=True)
  _line("Q"); _line("Options (A–D)"); _line("Answer"); _line("Explanation")
  st.markdown('</div>', unsafe_allow_html=True)

# ---------- public entry for the page ----------
def render_layout_only():
  """Locked order: Editor (top) → Tamil (middle) → English (bottom)."""
  st.markdown(_LAYOUT_CSS, unsafe_allow_html=True)
  _editor_tamil()
  _reference_tamil()
  _reference_english()
