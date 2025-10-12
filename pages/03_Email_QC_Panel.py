# pages/03_Email_QC_Panel.py
import streamlit as st
from lib.top_strip import render_top_strip
from lib.qc_state import render_reference_and_editor

st.set_page_config(page_title="SME QC Panel", layout="wide")

ready = render_top_strip()

st.markdown("---")

if ready:
    render_reference_and_editor(editor_first=True)
else:
    st.info("Paste a link or upload a file, then press **Load**.")
