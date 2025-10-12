# lib/qc_state.py
import streamlit as st

# --- CSS for compact three-box layout ---
_LAYOUT_CSS = """
<style>
/* Hide sidebar + tighten layout */
[data-testid="stSidebar"]{display:none !important;}
.block-container{padding-top:8px; padding-bottom:8px;}

/* Stack boxes with zero gap */
.stack{display:grid; grid-template-rows:auto auto auto; row-gap:0;}

/* Common box style */
.card{
  margin:0;
  padding:4px 10px 6px 10px;  /* 🔹 Less top padding for tight title */
  border:2px solid #c0c7d0;
  border-radius:8px;
  background:#fff;
}

/* Individual border colors */
.ed-card{border-color:#1f4fbf;}
.ta-card{border-color:#199c4b;}
.en-card{border-color:#316dca;}

/* Box height ratio */
.ed-card{min-height:40vh;}
.ta-card{min-height:25vh;}
.en-card{min-height:25vh;}

/* 🔹 Smaller, tighter titles */
.card h4{
  font-size:12px !important;     /* Reduced text size */
  font-weight:600;
  margin:0;                      /* Remove default spacing */
  padding-top:2px;               /* Bring text near top border */
  padding-bottom:2px;
}

/* 🔹 Smaller text inside the boxes */
.card p, .card div, .card span {
  font-size:12px !important;
  line-height:1.3em;
  margin:0;
  padding:0;
}
</style>
"""

def render_boxes_only():
    """Render three bordered panels — compact, minimal spacing."""
    st.markdown(_LAYOUT_CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="stack">
          <div class="card ed-card">
            <h4>SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி</h4>
          </div>
          <div class="card ta-card">
            <h4>தமிழ் மூலப் பதிப்பு</h4>
          </div>
          <div class="card en-card">
            <h4>English Version</h4>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
