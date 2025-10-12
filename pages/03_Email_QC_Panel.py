# pages/03_Email_QC_Panel.py
import streamlit as st
from lib.top_strip import render_top_strip
from lib.qc_state import render_reference_and_editor

st.set_page_config(page_title="SME QC Panel", layout="wide")

def main():
    render_top_strip()
    if st.session_state.get("qc_df") is not None:
        render_reference_and_editor()
    else:
        st.info("Paste a link or upload a file at the top strip, then press **Load**.")

if __name__ == "__main__":
    main()
