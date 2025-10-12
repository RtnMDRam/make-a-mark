# lib/top_strip.py
from __future__ import annotations

import io
import datetime as dt
from typing import Optional

import pandas as pd
import streamlit as st


# ---------- CSS (runs once) ----------
def _css_once() -> None:
    if st.session_state.get("_top_css_done"):
        return
    st.session_state["_top_css_done"] = True

    st.markdown(
        """
        <style>
        /* Hide Streamlit chrome the SMEs don't need */
        [data-testid="stSidebar"]{display:none !important;}
        header, footer, .stAppToolbar, [data-testid="baseButton-secondary"], 
        a[href*="manage"] {visibility:hidden !important; height:0 !important;}

        /* Tighten up the overall paddings */
        .block-container{padding-top:8px !important; padding-bottom:8px !important;}

        /* Pills (date / time) */
        .pill{background:#1f2937; color:#fff; border-radius:10px; 
              padding:8px 12px; display:inline-block; line-height:1.1;}
        .pill small{opacity:.75; font-size:.8rem;}

        /* Row of action buttons */
        .top-actions .stButton>button{height:40px; border-radius:8px;}

        /* Upload strip tweaks */
        .label{font-size:.9rem; color:#666; margin:2px 0 4px;}
        .load-btn .stButton>button{height:40px; min-width:74px;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _pill(text: str, right: bool = False) -> None:
    align = "right" if right else "left"
    st.markdown(
        f'<div style="text-align:{align}"><span class="pill">{text}</span></div>',
        unsafe_allow_html=True,
    )


# ---------- Helpers ----------
def _read_from_upload(file) -> Optional[pd.DataFrame]:
    if not file:
        return None
    name = (file.name or "").lower()
    try:
        if name.endswith(".csv"):
            return pd.read_csv(file)
        if name.endswith(".xlsx") or name.endswith(".xls"):
            return pd.read_excel(file)
        # Fall back: try CSV
        file.seek(0)
        return pd.read_csv(file)
    except Exception:
        return None


# ---------- Main renderer ----------
def render_top_strip() -> bool:
    """
    Renders the compact top strip (date/time, actions, link+uploader).
    If a file/link is successfully loaded, publishes:
        st.session_state.qc_df  : pandas.DataFrame
        st.session_state.qc_idx : int (defaults to 0)
    Returns True if qc_df is available in session.
    """
    _css_once()

    # --- Date / time pills ---
    now = dt.datetime.now()

    # Tamil month (simple mapping by Gregorian month; OK for display)
    tamil_month_map = {
        1: "தை", 2: "மாசி", 3: "பங்குனி", 4: "சித்திரை",
        5: "வைகாசி", 6: "ஆனி", 7: "ஆடி", 8: "ஆவணி",
        9: "புரட்டாசி", 10: "ஐப்பசி", 11: "கார்த்திகை", 12: "மார்கழி",
    }
    t_month = tamil_month_map.get(now.month, "")
    tamil_date = f"{t_month} {now.day} I {now.year} Oct {now.day}"

    left, mid, right = st.columns([1, 2, 1])
    with left:
        _pill(f"**{tamil_date}**")
    with right:
        _pill(f"**{now:%H:%M}**<br><small>24-hr</small>", right=True)

    # --- Title (kept modest) ---
    st.markdown("### பாட பொருள் நிபுணர் பலகை / SME Panel")

    # --- Actions row ---
    subL, subM, subR, subD = st.columns([1.1, 1.1, 1.1, 1.2])
    with subL:
        st.button("💾 Save", key="btn_save", use_container_width=True)
    with subM:
        st.button("✅ Mark Complete", key="btn_complete", use_container_width=True)
    with subR:
        st.button("📁 Save & Next", key="btn_next", use_container_width=True)
    with subD:
        st.button("⬇️ Download QC", key="btn_dl", use_container_width=True)

    # --- Link + file upload strip (compact) ---
    st.write("")  # tiny spacer
    colL, colMid, colR = st.columns([3, 0.6, 3])

    with colL:
        st.markdown('<div class="label">Paste the CSV/XLSX link sent by admin (or upload). Quick & compact.</div>',
                    unsafe_allow_html=True)
        link = st.text_input("Paste the CSV/XLSX link", key="top_link", label_visibility="collapsed")

    with colMid:
        st.markdown('<div class="label">&nbsp;</div>', unsafe_allow_html=True)
        load_clicked = st.button("Load", key="btn_load", use_container_width=True)

    with colR:
        st.markdown('<div class="label">Upload the file here (Limit 200 MB per file)</div>',
                    unsafe_allow_html=True)
        up = st.file_uploader("Drag and drop file here", type=["csv", "xlsx", "xls"],
                              label_visibility="collapsed")

    # --- Load handler (only warn when neither provided) ---
    ready = "qc_df" in st.session_state and isinstance(st.session_state.qc_df, pd.DataFrame)

    if load_clicked:
        df: Optional[pd.DataFrame] = None

        # (A) link handling – optional (skip if empty)
        if link and link.strip():
            try:
                if link.lower().endswith(".csv"):
                    df = pd.read_csv(link)
                elif link.lower().endswith((".xlsx", ".xls")):
                    df = pd.read_excel(link)
            except Exception as _:
                st.warning("Could not load from link. Try upload instead.", icon="⚠️")

        # (B) uploaded file takes priority if present
        if up is not None:
            df = _read_from_upload(up)

        if df is None:
            st.error("Empty link or unreadable file. Please paste a valid link or upload a CSV/XLSX.", icon="🧭")
        else:
            st.session_state.qc_df = df
            st.session_state.qc_idx = 0
            st.success("Loaded from file.", icon="✅")
            ready = True

    return ready
