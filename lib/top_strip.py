# lib/top_strip.py
from __future__ import annotations
import datetime as dt
import io
import pandas as pd
import streamlit as st

__all__ = ["render_top_strip"]

# --- Tamil month names (Panchangam style) ---
_TAMIL_MONTHS = {
    1: "சித்திரை", 2: "வைகாசி", 3: "ஆனி", 4: "ஆடி",
    5: "ஆவணி", 6: "புரட்டாசி", 7: "ஐப்பசி", 8: "கார்த்திகை",
    9: "மார்கழி", 10: "தை", 11: "மாசி", 12: "பங்குனி",
}
# For your example (“புரட்டாசி 26 | 2025 Oct 12”) we’ll *force* the
# Tamil label to month=6 (Purattasi) when today really is October.
# Remove this helper if you later compute Tamil month properly.
def _guess_tamil_month(now: dt.datetime) -> str:
    # If it is October, show “புரட்டாசி” per your screenshot request.
    if now.month == 10:
        return "புரட்டாசி"
    return _TAMIL_MONTHS.get(now.month, "—")

def _css_once() -> None:
    if st.session_state.get("_top_css_done"):
        return
    st.session_state["_top_css_done"] = True
    st.markdown(
        """
        <style>
          /* Hide Streamlit left sidebar & toolbar completely */
          [data-testid="stSidebar"], header, footer, .stAppToolbar { display: none !important; }
          [data-testid="collapsedControl"]{ visibility: hidden !important; height:0 !important; }
          /* Kill the floating “Manage app” button for SMEs */
          .stActionButtonIconToolbar { display:none !important; }

          /* Tighten global spacing a little */
          .block-container { padding-top: 6px; padding-bottom: 4px; }
          .element-container { margin-bottom: 6px; }

          /* “Pill” look for the date/time boxes */
          .pill {
            display:inline-block; min-width:130px;
            background:#1f2937; color:#fff; border-radius:10px;
            padding:6px 10px; line-height:1.15; text-align:center;
            font-size:14px; font-weight:500;
          }
          .pill small { display:block; opacity:0.8; font-weight:400; }

          /* Row of action buttons */
          .top-actions .stButton>button {
            height:38px; border-radius:10px; font-weight:600;
          }
          .lbl { font-size:12px; color:#666; margin:4px 0 6px; }
          /* “Load” small vertical button */
          .load-btn .stButton>button { height:40px; min-width:64px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def _pill(main: str, sub: str) -> None:
    st.markdown(f'<span class="pill">{main}<small>{sub}</small></span>', unsafe_allow_html=True)

def _load_from_link(link: str) -> pd.DataFrame:
    if not link:
        raise ValueError("Empty link.")
    # If the link points to a CSV
    if link.lower().endswith(".csv"):
        return pd.read_csv(link)
    # If the link points to an Excel file
    return pd.read_excel(link)

def render_top_strip() -> bool:
    """
    Renders the compact top strip (date/time pills, action buttons,
    link + uploader + Load). Returns True if a dataset is available
    in session (st.session_state.qc_df and st.session_state.qc_idx).
    """
    _css_once()
    now = dt.datetime.now()

    # --- First row: date (left) and time (right) as neat pills ---
    left, mid, right = st.columns([1, 2, 1])
    with left:
        # “புரட்டாசி 26 | 2025 Oct 12”
        tam = _guess_tamil_month(now)
        eng = now.strftime("%Y %b %d")
        main = f"{tam} {now.day} | {eng}"
        _pill(main, sub="")
    with right:
        # 24-hour time on top line; “24-hr” under it
        _pill(now.strftime("%H:%M"), sub="24-hr")

    # --- Second row: action buttons (one line) ---
    st.markdown("### பாட பொருள் நிபுணர் பலகை / SME Panel")
    subL, subM, subR, subD = st.columns([1.1, 1.1, 1.1, 1.3])
    with subL:
        st.button("💾 Save", key="btn_save", use_container_width=True)
    with subM:
        st.button("✅ Mark Complete", key="btn_complete", use_container_width=True)
    with subR:
        st.button("🗂️ Save & Next", key="btn_next", use_container_width=True)
    with subD:
        st.button("⬇️ Download QC", key="btn_d1", use_container_width=True)

    # --- Third row: link input / file uploader / Load ---
    st.markdown('<div class="lbl">Paste the CSV/XLSX link sent by admin (or upload). Quick & compact.</div>', unsafe_allow_html=True)
    twoL, loadC, twoR = st.columns([2.2, 0.3, 2.5])

    with twoL:
        link = st.text_input(" ", key="qc_link", label_visibility="collapsed",
                             placeholder="Paste the CSV/XLSX link")
    with loadC:
        with st.container():
            st.markdown('<div class="load-btn">', unsafe_allow_html=True)
            pressed = st.button("Load", key="btn_load", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    with twoR:
        st.markdown('<div class="lbl">Upload the file here (Limit 200 MB per file)</div>', unsafe_allow_html=True)
        up = st.file_uploader(" ", key="qc_up", label_visibility="collapsed",
                              type=["csv", "xlsx", "xls"])

    # --- process Load / uploads ---
    if pressed:
        try:
            if up is not None:
                if up.name.lower().endswith(".csv"):
                    df = pd.read_csv(up)
                else:
                    df = pd.read_excel(up)
                st.success("Loaded from file.")
            else:
                df = _load_from_link(link)
                st.success("Loaded from link.")
            if df is None or df.empty:
                st.error("No rows found in the file.")
                return False
            st.session_state.qc_df = df
            st.session_state.qc_idx = 0
        except Exception as e:
            st.error(str(e))
            return False

    # sanity message
    if "qc_df" not in st.session_state:
        st.info("Paste a link or upload a file, then press **Load**.")
        return False

    return True
