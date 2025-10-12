# lib/qc_state.py
import streamlit as st

# — CSS for three tight boxes only (no inner widgets) —
_LAYOUT_CSS = """
<style>
/* hide sidebar, tighten page */
[data-testid="stSidebar"]{display:none !important;}
.block-container{padding-top:8px; padding-bottom:8px;}

/* remove default gaps between our cards */
.stack{display:grid; grid-template-rows:auto auto auto; row-gap:0;}

/* generic card */
.card{
  margin:0;                 /* no outer gap */
  padding:12px;             /* small inner padding */
  border:2px solid #d0d7de; /* single clear outline */
  border-radius:8px;
  background:#fff;
}

/* color accents per section (only border color) */
.ed-card{border-color:#1f4fbf;}  /* SME editable (blue) */
.ta-card{border-color:#199c4b;}  /* Tamil ref (green)  */
.en-card{border-color:#316dca;}  /* English ref (blue) */

/* titles */
.card h4{
  margin:0 0 6px 0;
  font-size:20px; font-weight:700;
}

/* heights: ~40% / 25% / 25% of viewport */
.ed-card{min-height:40vh;}
.ta-card{min-height:25vh;}
.en-card{min-height:25vh;}
</style>
"""

def render_boxes_only():
    """Show only three touching boxes with titles; no content."""
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
