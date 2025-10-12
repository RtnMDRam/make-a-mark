# pages/03_Email_QC_Panel.py
import streamlit as st
from lib.top_strip import render_top_strip
from lib.qc_state import render_boxes_only   # ✅ correct function import

st.set_page_config(page_title="SME QC Panel", layout="wide")

def main():
    # 1. Top bar: date/time + Save/Next + upload field
    render_top_strip()

    # 2. Show only three boxes (no content yet)
    if st.session_state.get("qc_df") is not None:
        render_boxes_only()
    else:
        st.info("Paste a link or upload a file at the top strip, then press **Load**.")

if __name__ == "__main__":
    main()
