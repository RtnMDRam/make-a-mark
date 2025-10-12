import datetime as dt
import pandas as pd
import streamlit as st
from io import BytesIO

def _css_once():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"]{ display: none !important; }
        .block-container{ padding-top:12px; padding-bottom:12px; }
        h1, h2, h3 { margin: .2rem 0 .6rem 0; }
        .sme-title { font-size: 22px; font-weight: 700; }
        .stButton>button { height: 40px; padding: 0 14px; }
        .pill { background:#1f2937;color:#fff;padding:8px 14px;border-radius:10px;
                font-variant-numeric: tabular-nums; line-height:1.1; display:inline-block; }
        .label{font-size:13px;color:#666;margin:0 0 4px 2px;}
        .load-btn .stButton>button{min-width:72px;}
        .en-card{background:#e9f0ff30;border-radius:10px;padding:14px 16px;border:1px solid #dde8ff;}
        .ta-card{background:#e9ffe930;border-radius:10px;padding:14px 16px;border:1px solid #d7f7cf;}
        .badge{background:#eef2ff;border-radius:14px;padding:4px 8px;display:inline-block;
               font-size:13px;color:#334155;margin-bottom:6px;}
        .field-label{font-weight:600;}
        </style>
        """,
        unsafe_allow_html=True,
    )

def _pill(text, right=False):
    st.markdown(
        f"<div style='text-align:{'right' if right else 'left'}'><span class='pill'>{text}</span></div>",
        unsafe_allow_html=True,
    )

def _tamil_md_text():
    return st.session_state.get("t_month_day", "புரட்டாசி 26")

def render_top_strip():
    _css_once()
    now = dt.datetime.now()

    left, _, right = st.columns([1,2,1])
    with left:
        _pill(f"{_tamil_md_text()} | {now:%Y %b %d}")
    with right:
        _pill(f"{now:%H:%M}", right=True)

    st.markdown("<div class='sme-title'>பாட பொருள் நிபுணர் பலகை / SME Panel</div>", unsafe_allow_html=True)

    a1, a2, a3, a4 = st.columns([1.1,1.1,1.1,1.2])
    with a1: st.button("💾 Save", key="btn_save", use_container_width=True)
    with a2: st.button("✅ Mark Complete", key="btn_complete", use_container_width=True)
    with a3: st.button("📁 Save & Next", key="btn_next", use_container_width=True)
    with a4: st.button("⬇️ Download QC", key="btn_dl", use_container_width=True)

    st.write("")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("<div class='label'>Paste the CSV/XLSX link sent by admin (or upload). Quick & compact.</div>", unsafe_allow_html=True)
        link = st.text_input("Paste the CSV/XLSX link", key="qc_link", label_visibility="collapsed")
        st.session_state.setdefault("qc_link", link)
    with c2:
        st.markdown("<div class='label'>Upload the file here (Limit 200 MB per file)</div>", unsafe_allow_html=True)
        file = st.file_uploader("Drag and drop file here", type=["csv","xlsx","xls"], label_visibility="collapsed")

    st.write("")
    _, load_col, _ = st.columns([1.5, .25, 1.5])
    with load_col:
        pressed = st.button("Load", key="btn_load", use_container_width=True)

    if pressed:
        try:
            if file is not None:
                if str(file.name).lower().endswith(".csv"):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(BytesIO(file.read()))
                df.columns = [str(c).strip() for c in df.columns]
                st.session_state.qc_df = df
                st.session_state.qc_idx = 0
                st.success("Loaded from file.")
                return True
            elif link.strip():
                st.warning("Link loading not wired yet. Please upload the file for now.")
            else:
                st.error("No data found. Please upload a CSV/XLSX.")
        except Exception as e:
            st.error(f"Could not load file: {e}")

    st.info("Paste a link or upload a file, then press **Load**.")
    return "qc_df" in st.session_state and not st.session_state.qc_df.empty
