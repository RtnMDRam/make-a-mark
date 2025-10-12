# lib/qc_state.py
import streamlit as st

# --- CSS for compact three-box layout ---
_LAYOUT_CSS = """
<style>
/* hide sidebar + tighten top/bottom padding */
[data-testid="stSidebar"]{display:none !important;}
.block-container{padding-top:8px; padding-bottom:8px;}

/* stack boxes with no vertical gap */
.stack{display:grid; grid-template-rows:auto auto auto; row-gap:0;}

/* common box style */
.card{
  margin:0;
  padding:10px 14px;
  border:2px solid #c0c7d0;
  border-radius:8px;
  background:#fff;
}

/* colors for each panel */
.ed-card{border-color:#1f4fbf;}
.ta-card{border-color:#199c4b;}
.en-card{border-color:#316dca;}

/* heights: 40 / 25 / 25 ratio */
.ed-card{min-height:40vh;}
.ta-card{min-height:25vh;}
.en-card{min-height:25vh;}

/* reduce font size inside boxes */
.card h4{
  font-size:16px;
  font-weight:600;
  margin:0 0 4px 0;
}
.card p, .card div, .card span {
  font-size:14px !important;
  line-height:1.4em;
}
</style>
"""

def render_boxes_only():
    """Show three clean bordered boxes with small text."""
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
