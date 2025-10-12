# pages/03_Email_QC_Panel.py
import streamlit as st
from lib.top_strip import render_top_strip
from lib.qc_state import render_boxes_only

st.set_page_config(page_title="SME QC Panel", layout="wide")

def main():
    # 1) Top strip (date/time + actions + link/uploader)
    render_top_strip()

    # 2) After Load, show layout-only boxes (no data yet)
    if st.session_state.get("qc_df") is not None:
        render_boxes_only()
    else:
        st.info("Paste a link or upload a file at the top strip, then press **Load**.")

if __name__ == "__main__":
    main()
