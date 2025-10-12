# pages/03_Email_QC_Panel.py
import streamlit as st
from lib.top_strip import render_top_strip
from lib.qc_state import render_layout_only

st.set_page_config(page_title="SME QC Panel", layout="wide")

def main():
    render_top_strip()  # top buttons + link/file

    if st.session_state.get("qc_df", None) is not None:
        render_layout_only()   # Editor (top) → Tamil → English
    else:
        st.info("Paste a link or upload a file at the top strip, then press **Load**.")

if __name__ == "__main__":
    main()
