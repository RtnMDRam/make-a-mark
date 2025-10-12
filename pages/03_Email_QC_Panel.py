# pages/03_Email_QC_Panel.py
import streamlit as st

st.set_page_config(page_title="SME QC Panel", layout="wide")

# Optional: hide sidebar (so teachers get full width)
st.markdown(
    """
    <style>
      [data-testid="stSidebar"]{display:none;}
      .block-container{padding-top:0.8rem; padding-bottom:2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

from lib.top_strip import render_top_strip            # top buttons + link/file
from lib.qc_state import render_reference_and_editor  # editor + reference panels

def main():
    # 1) Top strip: date/time + Save / Complete / Next + Download + link/file inputs
    ready = render_top_strip()

    # 2) After Load (qc_df present), show editor + references in your preferred order
    if st.session_state.get("qc_df", None) is not None:
        render_reference_and_editor()   # Editor (top) -> Tamil (middle) -> English (bottom)
    else:
        st.info("Paste a link or upload a file at the top strip, then press **Load**.")

if __name__ == "__main__":
    main()
