# pages/03_Email_QC_Panel.py
import io, re, pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SME QC Panel",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- kill sidebar + extra chrome, keep paddings tight
st.markdown("""
<style>
[data-testid="stSidebar"] {display:none !important;}
header, footer, [data-testid="collapsedControl"] {visibility:hidden;height:0;}
.block-container {padding-top:8px !important; padding-bottom:8px !important;}
/* make action row compact */
.topstrip .stButton>button{padding:6px 14px; height:38px;}
.topstrip .pill{background:#222832;color:#fff;border-radius:8px;padding:10px 14px;}
.topstrip .rightpill{justify-self:end;}
/* keep uploader row single-line on iPad */
.uprow [data-testid="stHorizontalBlock"]{gap:10px}
.manage-app{display:none !important;} /* hides Streamlit Cloud "Manage app" FAB */
</style>
""", unsafe_allow_html=True)

# ---------------- utilities ----------------
def _clean_drive(url:str)->str:
    """accepts drive links and converts to direct download"""
    if "drive.google.com" not in url:
        return url.strip()
    m = re.search(r"/file/d/([^/]+)/", url)
    if m: return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    m = re.search(r"[?&]id=([^&]+)", url)
    if m: return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    return url.strip()

def _read_any(source)->pd.DataFrame:
    """source can be file-like (UploadedFile) or url str"""
    if hasattr(source, "read"):  # uploaded file
        name = (getattr(source, "name", "") or "").lower()
        if name.endswith(".csv"):
            return pd.read_csv(source)
        return pd.read_excel(source)
    if isinstance(source, str):
        u = _clean_drive(source)
        # try csv then xlsx
        try: return pd.read_csv(u)
        except Exception: return pd.read_excel(u)
    raise RuntimeError("Unsupported source")

# ---------------- TOP STRIP ----------------
def top_strip():
    ss = st.session_state
    st.markdown('<div class="topstrip">', unsafe_allow_html=True)

    h1, h2, h3 = st.columns([2,6,2], vertical_alignment="center")
    with h1:
        st.markdown('<div class="pill">**12 Oct 2025**<br><span style="opacity:.8;">Oct 12</span></div>', unsafe_allow_html=True)
    with h2:
        st.markdown('<div class="pill" style="text-align:center;">'
                    'பாட பொருள் நிபுணர் பலகை / SME Panel<br>'
                    f'<span style="opacity:.8;">ID: {ss.get("cur_id","—")}</span>'
                    '</div>', unsafe_allow_html=True)
    with h3:
        st.markdown('<div class="pill rightpill" style="text-align:right;">'
                    '<span id="clock24">09:58</span><br><span style="opacity:.8;">24-hr</span>'
                    '</div>', unsafe_allow_html=True)

    a1,a2,a3,a4 = st.columns([1.5,1.8,1.8,2.0], vertical_alignment="center")
    with a1: st.button("💾 Save", key="btn_save", use_container_width=True)
    with a2: st.button("✅ Mark Complete", key="btn_complete", use_container_width=True)
    with a3: st.button("🗂️ Save & Next", key="btn_next", use_container_width=True)
    with a4: st.button("📥 Download QC", key="btn_dl", use_container_width=True, disabled=("qc_work" not in ss))

    st.write("")  # tiny spacer

    # input row (link + file + Load)
    upL, loadC, upR = st.columns([6,1,6], vertical_alignment="center")
    with upL:
        link = st.text_input("Paste the CSV/XLSX link sent by admin (or upload). Quick & compact.",
                             key="link_in", label_visibility="visible", placeholder="Paste the CSV/XLSX link")
    with loadC:
        # normal width -> no “vertical letters”
        load_clicked = st.button("Load", key="btn_load", use_container_width=True)
    with upR:
        st.file_uploader("Upload the file here (Limit 200 MB per file)",
                         type=["csv","xlsx"], key="file_in")

    st.markdown('</div>', unsafe_allow_html=True)

    # logic: allow EITHER link OR file.
    msg = None
    if load_clicked:
        src = None
        if st.session_state.get("file_in") is not None:
            src = st.session_state["file_in"]
        elif (link or "").strip():
            src = link.strip()
        else:
            msg = ("warn", "Please provide a link or choose a file.")
        if src is not None:
            try:
                df = _read_any(src)
                # normalize minimal expected columns if present
                ss.qc_src = df.copy()
                ss.qc_work = df.copy()
                ss.qc_idx = 0
                ss.cur_id = str(df.iloc[0].get("_id", "—")) if not df.empty else "—"
                msg = ("ok", "Loaded from file.")
            except Exception as e:
                msg = ("err", f"Could not open. {e}")

    if msg:
        level, text = msg
        if level=="ok": st.success(text)
        elif level=="warn": st.warning(text)
        else: st.error(text)

# --------- PAGE BODY ----------
top_strip()

ss = st.session_state
if "qc_work" not in ss or ss.qc_work is None or len(ss.qc_work)==0:
    st.info("Paste a link or upload a file at the top strip to begin.")
    st.stop()

# From here render your existing English/Tamil reference + SME editor
# (unchanged logic you already had)
from lib.qc_state import render_reference_and_editor  # your own helper
render_reference_and_editor()
