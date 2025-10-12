# lib/qc_state.py
import streamlit as st

# ---------- CSS: single separator line + fixed heights ----------
_LAYOUT_CSS = """
<style>
[data-testid="stSidebar"]{display:none !important;}
.block-container{padding-top:10px;padding-bottom:10px;}

/* PANELS (no box border; we draw ONE top line via ::before) */
.panel{
  position:relative;
  background:#ffffff;
  padding:14px 16px 14px 16px;
  margin:0;                      /* panels touch */
  overflow:auto;                 /* scroll inside if content exceeds height */
}

/* single separator line */
.panel::before{
  content:"";
  display:block;
  height:0;
  border-top:1.6px solid #64748b;  /* visible, single line */
  margin:0 0 12px 0;
}

/* color per section (only the single line) */
.panel.ed::before{ border-color:#475569; }  /* top, editable Tamil */
.panel.ta::before{ border-color:#16a34a; }  /* middle, Tamil reference */
.panel.en::before{ border-color:#2563eb; }  /* bottom, English reference */

/* fixed heights using viewport units (approx: 40% / 25% / 25%) */
.panel.ed{  min-height:40vh; }
.panel.ta{  min-height:25vh; }
.panel.en{  min-height:25vh; }

/* headings & labels */
.panel h4{ margin:0 0 10px 0; font-size:18px; font-weight:700; color:#111827; }
.row{ display:grid; grid-template-columns:auto 1fr; gap:8px; align-items:start; }
.label{ font-weight:600; color:#334155; }
.sep{ opacity:.8; }

/* compact inputs */
.stTextArea textarea, .stTextInput input{ font-size:16px; }

/* remove any accidental lines/dividers */
hr, .stDivider, [data-testid="stDivider"], .ta-bar, .en-bar, .ed-bar{
  display:none !important; height:0 !important; margin:0 !important; padding:0 !important; border:0 !important;
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

# ---- PANELS ----
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
  """Locked order: Editor (top) → Tamil reference (middle) → English reference (bottom)."""
  st.markdown(_LAYOUT_CSS, unsafe_allow_html=True)
  _editor_tamil()
  _reference_tamil()
  _reference_english()
