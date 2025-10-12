# lib/qc_state.py
import streamlit as st

# --- Compact CSS: WHITE cards + COLORED OUTER BORDERS + tight vertical gaps ---
_LAYOUT_CSS = """
<style>
/* Hide default left sidebar */
[data-testid="stSidebar"]{display:none !important;}
.block-container{padding-top:10px;padding-bottom:10px;}

/* Generic card: white background, rounded, clear outer border */
.card{
  background:#ffffff !important;
  border:2px solid #cbd5e1;   /* default slate */
  border-radius:12px;
  padding:14px 16px;
  margin:0;
}

/* Small gap between stacked cards (keep tight) */
.card + .card{ margin-top:10px; }

/* Specific border colors per panel (as you outlined) */
.ed-card{ border-color:#475569; }   /* Editable Tamil = dark slate/grey */
.ta-card{ border-color:#16a34a; }   /* Tamil reference = green */
.en-card{ border-color:#3b82f6; }   /* English reference = blue */

/* Headings inside cards */
.card h4{ margin:0 0 10px 0; font-size:18px; font-weight:700; color:#111827; }

/* Reference rows: label on left, value on right */
.row{
  display:grid;
  grid-template-columns:auto 1fr;
  gap:8px;
  align-items:start;
  margin:2px 0;
}
.label{ font-weight:600; color:#334155; }
.sep{ opacity:.75; }

/* Inputs readable and compact */
.stTextArea textarea, .stTextInput input{ font-size:16px; }

/* REMOVE any tinted header bars from earlier styles */
.ta-bar, .en-bar{ display:none !important; }
</style>
"""

# ---------- helpers ----------
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

# ---------- TOP: Editable Tamil ----------
def _editor_tamil():
  st.markdown('<div class="card ed-card">', unsafe_allow_html=True)
  st.markdown('<h4>SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி</h4>', unsafe_allow_html=True)

  st.text_area("கேள்வி", value="", height=80, label_visibility="collapsed", key="ed_q_ta")
  st.text_input("விருப்பங்கள் (A–D)", value="", label_visibility="visible", key="ed_opts_ta")
  st.text_input("பதில்", value="", label_visibility="visible", key="ed_ans_ta")
  st.text_area("விளக்கம்", value="", height=120, label_visibility="visible", key="ed_ex_ta")

  st.markdown('</div>', unsafe_allow_html=True)

# ---------- MIDDLE: Tamil (read-only) ----------
def _reference_tamil():
  st.markdown('<div class="card ta-card">', unsafe_allow_html=True)
  st.markdown('<h4>தமிழ் மூலப் பதிப்பு</h4>', unsafe_allow_html=True)
  _line("கேள்வி")
  _line("விருப்பங்கள் (A–D)")
  _line("பதில்")
  _line("விளக்கம்")
  st.markdown('</div>', unsafe_allow_html=True)

# ---------- BOTTOM: English (read-only) ----------
def _reference_english():
  st.markdown('<div class="card en-card">', unsafe_allow_html=True)
  st.markdown('<h4>English Version</h4>', unsafe_allow_html=True)
  _line("Q")
  _line("Options (A–D)")
  _line("Answer")
  _line("Explanation")
  st.markdown('</div>', unsafe_allow_html=True)

# ---------- public: render layout only ----------
def render_layout_only():
  """Locked order: Editor (top) → Tamil (middle) → English (bottom)."""
  st.markdown(_LAYOUT_CSS, unsafe_allow_html=True)
  _editor_tamil()
  _reference_tamil()
  _reference_english()
