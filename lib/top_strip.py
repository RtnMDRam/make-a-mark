import datetime as dt
import pandas as pd
import streamlit as st
from io import BytesIO

# --- helpers -------------------------------------------------

def _css_once():
    st.markdown(
        """
        <style>
        /* hide Streamlit left sidebar */
        [data-testid="stSidebar"] { display: none !important; }
        /* tighten layout & shrink big headings */
        .block-container { padding-top: 12px; padding-bottom: 12px; }
        h1, h2, h3 { margin: 0.2rem 0 0.6rem 0; }
        .sme-title { font-size: 22px; font-weight: 700; }
        /* compact controls */
        .stButton>button { height: 40px; padding: 0 14px; }
        .pill { background:#1f2937; color:#fff; padding:8px 14px; border-radius:10px;
                font-variant-numeric: tabular-nums; line-height:1.1; display:inline-block; }
        .two-col{display:grid;grid-template-columns:1fr 1fr;gap:14px;align-items:end;}
        .two-col .label{font-size:13px;color:#666;margin:0 0 4px 2px;}
        .load-btn .stButton>button{min-width:72px;}
        </style>
        """,
        unsafe_allow_html=True,
    )

def _pill(text, right=False):
    align = "right" if right else "left"
    st.markdown(f"<div style='text-align:{align}'><span class='pill'>{text}</span></div>", unsafe_allow_html=True)

# Expose a simple key to override Tamil month-day text if you ever need:
def _tamil_md_text():
    # Default shown text; you can set st.session_state.t_month_day = "புரட்டாசி 26"
    return st.session_state.get("t_month_day", "புரட்டாசி 26")

# --- main renderer -------------------------------------------

def render_top_strip():
    """
    Top strip with date/time pills + actions + link/uploader.
    Publishes on successful load:
        st.session_state.qc_df : pandas.DataFrame
        st.session_state.qc_idx: int
    Returns True if data is ready.
    """
    _css_once()
    now = dt.datetime.now()

    # Pills row
    left, mid, right = st.columns([1, 2, 1])
    with left:
        # e.g. "புரட்டாசி 26 | 2025 Oct 12"
        left_txt = f"{_tamil_md_text()} | {now:%Y %b %d}"
        _pill(left_txt)
    with right:
        # 24-hour only
        _pill(f"{now:%H:%M}", right=True)

    # Title
    st.markdown("<div class='sme-title'>பாட பொருள் நிபுணர் பலகை / SME Panel</div>", unsafe_allow_html=True)

    # Actions row
    subL, subM, subR, subD = st.columns([1.1,1.1,1.1,1.2])
    with subL:
        st.button("💾 Save", key="btn_save", use_container_width=True)
    with subM:
        st.button("✅ Mark Complete", key="btn_complete", use_container_width=True)
    with subR:
        st.button("🗂️ Save & Next", key="btn_next", use_container_width=True)
    with subD:
        st.button("⬇️ Download QC", key="btn_dl", use_container_width=True)

    # Link + Uploader (compact)
    st.write("")  # tiny spacer
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("<div class='label'>Paste the CSV/XLSX link sent by admin (or upload). Quick & compact.</div>", unsafe_allow_html=True)
        link = st.text_input("Paste the CSV/XLSX link", key="qc_link", label_visibility="collapsed")
        st.session_state.setdefault("qc_link", link)
    with c2:
        st.markdown("<div class='label'>Upload the file here (Limit 200 MB per file)</div>", unsafe_allow_html=True)
        file = st.file_uploader("Drag and drop file here", type=["csv","xlsx","xls"], label_visibility="collapsed", key="qc_file")

    st.write("")  # tiny spacer
    _, load_col, _ = st.columns([1.5, .25, 1.5])
    with load_col:
        pressed = st.button("Load", key="btn_load", use_container_width=True)

    if pressed:
        try:
            df = None
            if file is not None:
                # Parse upload
                if file.name.lower().endswith(".csv"):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(BytesIO(file.read()))
            elif link.strip():
                # You can add your actual drive fetch here; for now show a gentle message
                st.warning("Link loading not wired yet. Please upload the file for now.")
            if df is not None:
                st.session_state.qc_df = df
                st.session_state.qc_idx = 0
                st.success("Loaded from file.")
                return True
            else:
                st.error("No data found. Please upload a CSV/XLSX.")
        except Exception as e:
            st.error(f"Could not load file: {e}")

    # No data yet
    st.info("Paste a link or upload a file, then press **Load**.")
    return "qc_df" in st.session_state and not st.session_state.qc_df.empty
