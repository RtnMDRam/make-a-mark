# lib/top_strip.py
from __future__ import annotations
import datetime as dt
import io
import pandas as pd
import streamlit as st

# ---------------- CSS (Palm-leaf look, compact spacing, hide sidebar & floater)
_PALM_CSS = """
<style>
/* Hide Streamlit left sidebar and the floating Manage button */
section[data-testid="stSidebar"] { display:none !important; }
button[kind="header"] + div { display:none !important; }  /* “Manage app” floater */

/* Gentle palm-leaf background */
main blockquote, .stApp { background: #F7F1E1; }
.stMarkdown, .stButton>button, .stTextInput>div>div>input,
.stFileUploader, .stTextArea textarea { font-size: 16px; }

/* Pills (date/time) */
.pill{
  display:inline-block; padding:10px 14px; border-radius:12px;
  background:#23262d; color:#fff; font-weight:600; line-height:1.15;
  box-shadow: 0 1px 0 rgba(0,0,0,.15);
}
.pill small{ display:block; opacity:.7; font-weight:500; }

/* Top buttons row */
.toprow .stButton>button{
  height:40px; padding:0 16px; border-radius:10px; font-weight:600;
}

/* Two column loader */
.two-col > div:nth-child(1){ padding-right:10px; }
.load-btn .stButton>button{ height:40px; min-width:68px; }

/* Section titles small, traditional */
h3.sme-title{ margin:0 0 2px 0; font-size:20px; letter-spacing:.2px; }
</style>
"""

# ---------------- Tamil month helper (approximate, for UI)
_TM_MONTHS = [
    ("சித்திரை", (4,14)), ("வைகாசி", (5,15)), ("ஆனி", (6,15)), ("ஆடி", (7,16)),
    ("ஆவணி", (8,16)), ("புரட்டாசி", (9,17)), ("ஐப்பசி", (10,17)), ("கார்த்திகை", (11,16)),
    ("மார்கழி", (12,16)), ("தை", (1,14)), ("மாசி", (2,13)), ("பங்குனி", (3,14)),
]
def _tamil_month_day(g: dt.date) -> tuple[str,int]:
    # rough UI mapping: choose latest month whose start <= date
    candidates = []
    for name,(m,d) in _TM_MONTHS:
        start = dt.date(g.year if m>=4 else g.year+1 if g.month>=4 else g.year, m, d)
        candidates.append((start, name))
    # pick the month whose start is <= g and maximum
    start = max([s for s,_ in candidates if s<=g], default=dt.date(g.year,9,17))
    name = [n for s,n in candidates if s==start][0]
    day = (g - start).days + 1
    return name, day

# ---------------- internal: read file or link
def _read_any(file_bytes: bytes, filename: str) -> pd.DataFrame:
    ext = (filename or "").lower()
    if ext.endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes))
    # default to Excel
    return pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")

# ---------------- public: render the strip. Publishes qc_df & qc_idx when loaded.
def render_top_strip() -> bool:
    """
    Returns True when a dataset is ready in session (qc_df & qc_idx).
    Publishes:
        st.session_state.qc_df  : pandas.DataFrame
        st.session_state.qc_idx : int
    """
    st.markdown(_PALM_CSS, unsafe_allow_html=True)

    now = dt.datetime.now()
    ta_month, ta_day = _tamil_month_day(now.date())

    left, mid, right = st.columns([1, 2, 1], gap="small")
    with left:
        st.markdown(
            f'<span class="pill">{ta_month} {ta_day} I {now:%Y %b %d}</span>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f'<span class="pill">{now:%H:%M}<small>24-hr</small></span>',
            unsafe_allow_html=True,
        )

    st.markdown('<h3 class="sme-title">பாட பொருள் நிபுணர் பலகை / SME Panel</h3>', unsafe_allow_html=True)

    subL, subM, subR, subD = st.columns([1.1,1.1,1.1,1.2], gap="small")
    with subL: st.button("💾 Save", key="btn_save", use_container_width=True)
    with subM: st.button("✅ Mark Complete", key="btn_complete", use_container_width=True)
    with subR: st.button("📄 Save & Next", key="btn_next", use_container_width=True)
    with subD: st.button("⬇️ Download QC", key="btn_dl", use_container_width=True)

    st.write("")  # tiny spacer

    # --- Loader row (link + file + Load)
    lcol, bcol, fcol = st.columns([1.1, .16, 1.1], gap="small")
    with lcol:
        st.caption("Paste the CSV/XLSX link sent by admin (or upload). Quick & compact.")
        link = st.text_input("Paste the CSV/XLSX link", key="qc_link", label_visibility="collapsed")
    with bcol:
        st.caption(" ")  # align
        do_load = st.button("Load", key="btn_load", use_container_width=True)
    with fcol:
        st.caption("Upload the file here (Limit 200 MB per file)")
        upload = st.file_uploader("Drag and drop file here",
                                  type=["csv","xlsx","xls"], label_visibility="collapsed")

    # --- If Load pressed, resolve source & publish session state
    loaded = False
    if do_load:
        try:
            if upload is not None:
                data = upload.read()
                df = _read_any(data, upload.name)
                loaded = True
            elif link.strip():
                # Streamlit Cloud doesn’t allow direct fetch without requests; SMEs will usually upload.
                st.warning("Please use the Upload box for now (link fetch is disabled in this build).")
                df = None
            else:
                st.error("Empty link. Paste a link or upload a file.")
                df = None

            if loaded and df is not None and not df.empty:
                ss = st.session_state
                ss.qc_df = df.copy()
                ss.qc_idx = 0
                st.success("Loaded from file.")
        except Exception as e:
            st.error(f"Could not load the file: {e}")

    # Return readiness
    ss = st.session_state
    return bool(getattr(ss, "qc_df", None) is not None and len(getattr(ss, "qc_df", [])) > 0)
