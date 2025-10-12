# pages/03_Email_QC_Panel.py
import streamlit as st
from lib.top_strip import render_top_strip
from lib.qc_state import render_boxes_only   # ✅ Correct import name

st.set_page_config(page_title="SME QC Panel", layout="wide")

def main():
    # Top strip: date/time + buttons + file/link inputs
    render_top_strip()

    # After Load, show just 3 empty boxes (no content)
    if st.session_state.get("qc_df") is not None:
        render_boxes_only()
    else:
        st.info("Paste a link or upload a file at the top strip, then press **Load**.")

if __name__ == "__main__":
    main()
