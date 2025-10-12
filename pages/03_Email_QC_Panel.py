# pages/03_Email_QC_Panel.py
import streamlit as st

st.set_page_config(page_title="SME QC Panel", page_icon="📜", layout="wide")

# --- Global compaction + hide floating badge --------------------------
st.markdown("""
<style>
main .block-container{padding:8px 10px 6px;}
.element-container{margin-bottom:6px}
hr, div[role="separator"]{display:none !important;height:0 !important;margin:0 !important;}
.viewerBadge_container__1QSob, button[title="Manage app"]{display:none !important;}
</style>
""", unsafe_allow_html=True)

# --- Wire the two sections --------------------------------------------
from lib.top_strip import render_top_strip
from lib.editor_panel import render_editor

# 1) Top strip: returns True when a DataFrame is available in session
has_data = render_top_strip()

# 2) If no data yet, stop here so SMEs only see the top strip
if not has_data:
    st.stop()

# 3) Main editor below (English/Tamil cards + compact SME console)
render_editor()
