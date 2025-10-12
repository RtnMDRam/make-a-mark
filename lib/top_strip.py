# lib/top_strip.py
from __future__ import annotations
import io, datetime as dt
import pandas as pd
import streamlit as st

def _pill(text: str, right=False):
    with st.container():
        st.markdown(
            f"""
            <div class="pill {'right' if right else ''}">{text}</div>
            """,
            unsafe_allow_html=True,
        )

def _css_once():
    if st.session_state.get("_top_css_done"): 
        return
    st.session_state["_top_css_done"] = True
    st.markdown("""
    <style>
      /* Hide sidebar & bottom floating button */
      section[data-testid="stSidebar"], [data-testid="stToolbar"] {display:none !important;}
      .stApp [data-testid="stStatusWidget"] {display:none !important;}
      .stApp {padding-top: 6px;}
      /* Pills for date/time */
      .pill{
        display:inline-block;padding:8px 14px;border-radius:10px;
        background:#222;color:#fff;font-weight:600;letter-spacing:.2px;
      }
      .pill.right{float:right}
      /* Row spacing smaller */
      .block-container{padding-top:10px;padding-bottom:10px;}
      .element-container{margin-bottom:8px;}
      .tight > div{margin-bottom:6px !important;}
      /* Buttons tighter */
      .stButton>button{padding:6px 14px;border-radius:8px;}
      .two-col>div{padding-right:8px;}
      .label{font-size:13px;color:#666;margin-bottom:4px;}
      /* push "Load" small and vertical center */
      .load-btn .stButton>button{height:40px; min-width:66px;}
    </style>
    """, unsafe_allow_html=True)

def render_top_strip():
    """
    Returns True when a dataset is ready in session (qc_df & qc_idx).
    Publishes:
      st.session_state.qc_df : pandas.DataFrame
      st.session_state.qc_idx: int
    """
    _css_once()
    now = dt.datetime.now()
    left, mid, right = st.columns([1,2,1])
    with left:
    _pill(f"**{now:%d %b %Y}**\n{now:%a}")  # shows date + day (e.g., Sun)
with right:
    _pill(f"**{now:%H:%M}**\n24-hr", right=True)

    st.markdown("### பாட பொருள் நிபுணர் பலகை / SME Panel")
    subL, subM, subR, subD = st.columns([1.1,1,1,1.2])
    with subL: st.button("💾 Save", key="btn_save", use_container_width=True)
    with subM: st.button("✅ Mark Complete", key="btn_complete", use_container_width=True)
    with subR: st.button("📄 Save & Next", key="btn_next", use_container_width=True)
    with subD: st.button("⬇️ Download QC", key="btn_dl", use_container_width=True)

    st.write("")  # tiny spacer
    lcol, mcol, rcol = st.columns([1.4,0.23,1.4])

    with lcol:
        st.caption("Paste the CSV/XLSX link sent by admin (or upload). Quick & compact.")
        link = st.text_input("Paste the CSV/XLSX link", key="qc_link", label_visibility="collapsed")

    with rcol:
        st.caption("Upload the file here (Limit 200 MB per file)")
        file = st.file_uploader("Drag and drop file here", type=["csv","xlsx"],
                                label_visibility="collapsed", accept_multiple_files=False)

    with mcol:
        st.caption("&nbsp;")
        if st.button("Load", key="btn_load", use_container_width=True):
            try:
                if file is not None:
                    buf = io.BytesIO(file.read())
                    df = _read_any(buf, filename=file.name)
                    _set_df(df)
                    st.success("Loaded from file.")
                elif link.strip():
                    # if you later fetch from Drive/URL, place that here
                    st.warning("Link loader not wired yet. Upload the file for now.")
                else:
                    st.error("Empty link.")
            except Exception as e:
                st.error(f"Load failed: {e}")

    return "qc_df" in st.session_state and not st.session_state.qc_df.empty

def _read_any(buf_or_bytes, filename=""):
    """CSV or XLSX reader, returns DataFrame."""
    name = (filename or "").lower()
    if name.endswith(".csv"):
        return pd.read_csv(buf_or_bytes)
    # default: xlsx
    return pd.read_excel(buf_or_bytes)

def _set_df(df: pd.DataFrame):
    st.session_state.qc_df = df.reset_index(drop=True)
    st.session_state.qc_idx = 0
