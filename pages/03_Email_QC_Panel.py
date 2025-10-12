# pages/03_Email_QC_Panel.py
import streamlit as st
from lib.top_strip import render_top_strip
from lib.editor_panel import render_references_and_editor

st.set_page_config(page_title="SME QC Panel", page_icon="📜", layout="wide", initial_sidebar_state="collapsed")

# --- global CSS: palm-leaf theme + remove chrome & gaps ---------------------
st.markdown("""
<style>
/* Hide sidebar & Streamlit extra chrome (toolbar, separator, status) */
[data-testid="stSidebar"]{display:none;}
header, footer, .stAppToolbar, [data-testid="collapsedControl"],
div[role="separator"], div[data-testid="stStatusWidget"] {visibility:hidden;height:0;margin:0;padding:0;}
/* Page gutters low; no bottom slack */
main .block-container{padding:8px 14px 8px;}
/* Palm-leaf background */
html, body, .stApp {background:#efe7d2;}
/* Cards */
.box{border:1px solid #d8cfb1;border-radius:12px;padding:10px 14px;margin:8px 0;background:#fffaf0;}
.box.en{background:#e8effb;border-color:#b8c9ee;}
.box.ta{background:#eaf6e9;border-color:#b8e0b5;}
/* Inputs tighter, uniform */
input, textarea{font-size:16px;}
label{font-size:14px;}
/* Subheader small (not huge) */
.sme-sub{font-weight:700;font-size:18px;margin:4px 0 6px;}
/* Option rows compact */
.optrow > div{margin-bottom:6px;}
/* Tiny rule */
.hr{height:6px;background:#212529;border-radius:12px;margin:4px 0 8px;}
/* Buttons look classic */
.btn > button{width:100%; border-radius:10px;}
/* Hide scroll gap bottom */
.block-container div:has(> .spacer-bottom){margin-bottom:0 !important;}
</style>
""", unsafe_allow_html=True)

# ---------------- top strip (toolbar + loader) ----------------
render_top_strip()

# If there is work in session, show references + edit
ss = st.session_state
if ss.get("qc_work") is not None and not ss.qc_work.empty:
    render_references_and_editor()
else:
    # Gentle hint only when nothing loaded
    st.info("Paste the CSV/XLSX link or upload a file above, then press **Load**.")
