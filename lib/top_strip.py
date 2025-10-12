# lib/top_strip.py
# Compact top strip for SME Panel (iPad-friendly)
# - Row 1: Date  |  Title  |  Time
# - Row 2: Save, Mark Complete, Save & Next, Download QC
# - Row 3: Link + Load  and  File Uploader (very compact)
#
# Exposes: render_top_strip()
# Side effects:
#   - sets st.session_state.qc_src, .qc_work (copy), .qc_idx = 0 (when loading)
#   - calls on_save(), on_mark_complete(), on_next() if provided

from __future__ import annotations
import io
import re
from typing import Callable, Optional

import pandas as pd
import streamlit as st


# ---------- helpers ----------
def _read_any(file_or_bytes) -> pd.DataFrame:
    """Read CSV or Excel from an uploaded file or bytes buffer."""
    # Try CSV first; fall back to Excel
    try:
        return pd.read_csv(file_or_bytes)
    except Exception:
        file_or_bytes.seek(0)
    try:
        return pd.read_excel(file_or_bytes)
    except Exception as e:
        raise RuntimeError(f"Could not open file. Expecting CSV/XLSX. Details: {e}")


def _read_from_link(url: str) -> pd.DataFrame:
    """Accepts public CSV/XLSX/Drive links and returns a DataFrame."""
    u = (url or "").strip()
    if not u:
        raise RuntimeError("Empty link.")
    # Convert public Drive share -> direct download
    if "drive.google.com" in u:
        m = re.search(r"/file/d/([^/]+)/", u)
        if m:
            u = f"https://drive.google.com/uc?export=download&id={m.group(1)}"
        else:
            m = re.search(r"[?&]id=([^&]+)", u)
            if m:
                u = f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    # Try CSV then Excel by URL
    try:
        return pd.read_csv(u)
    except Exception:
        pass
    try:
        return pd.read_excel(u)
    except Exception as e:
        raise RuntimeError(f"Could not open link. Expecting CSV/XLSX. Details: {e}")


def _to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return buf.getvalue()


# ---------- UI ----------
def render_top_strip(
    title_ta: str = "பாட பொருள் நிபுணர் பலகை / SME Panel",
    on_save: Optional[Callable[[], None]] = None,
    on_mark_complete: Optional[Callable[[], None]] = None,
    on_next: Optional[Callable[[], None]] = None,
):
    ss = st.session_state

    # Tiny CSS for tight layout + iPad look
    st.markdown(
        """
<style>
/* palm-leaf background tone comes from page theme; keep strip compact */
.strip-wrap {margin: 0 0 6px 0;}
.strip-hr    {height:8px;background:#1c1f24;border-radius:6px;margin:6px 0 8px 0;}
/* row gaps & button sizing */
.strip-row .stButton>button{padding:8px 12px; border-radius:8px;}
.strip-row {margin-bottom:6px;}
/* compact inputs */
.strip-input .stTextInput>div>div {padding:6px 10px;}
/* uploader compact */
.strip-upload [data-testid="stFileUploaderDropzone"]{padding:10px;}
/* small captions */
.strip-cap{font-size:12px;color:#666;margin-top:2px;}
/* date/time cells */
.datebox, .timebox{background:#262a30;color:#fff;border-radius:8px;padding:6px 10px;}
.datebox small, .timebox small{opacity:.9;}
.titlebox{font-weight:700;text-align:center;}
</style>
        """,
        unsafe_allow_html=True,
    )

    # ---------- Row 0: dark rule ----------
    st.markdown('<div class="strip-wrap"><div class="strip-hr"></div>', unsafe_allow_html=True)

    # ---------- Row 1: Date | Title | Time ----------
    cL, cM, cR = st.columns([1.1, 2.2, 1.0])
    with cL:
        st.markdown(
            f'<div class="datebox"><div>{pd.Timestamp.now().strftime("%d %b %Y")}'
            f'</div><small>Oct {pd.Timestamp.now().day}</small></div>',
            unsafe_allow_html=True,
        )
    with cM:
        st.markdown(f'<div class="titlebox">{title_ta}</div>', unsafe_allow_html=True)
        rid = ss.get("qc_work", pd.DataFrame()).iloc[ss.get("qc_idx", 0):ss.get("qc_idx", 1)]
        try:
            rid_val = str(rid["ID"].values[0])
        except Exception:
            rid_val = "—"
        st.caption(f"ID: {rid_val}")
    with cR:
        st.markdown(
            f'<div class="timebox"><div>{pd.Timestamp.now().strftime("%H:%M")}</div>'
            f'<small>24-hr</small></div>',
            unsafe_allow_html=True,
        )

    # ---------- Row 2: Actions (Save | Mark Complete | Save & Next | Download QC) ----------
    a1, a2, a3, a4 = st.columns([1, 1, 1, 1])
    with a1:
        if st.button("💾 Save", use_container_width=True):
            if on_save:
                on_save()
    with a2:
        if st.button("✅ Mark Complete", use_container_width=True):
            if on_mark_complete:
                on_mark_complete()
    with a3:
        if st.button("📄 Save & Next", use_container_width=True):
            if on_next:
                on_next()
    with a4:
        qcw = ss.get("qc_work", pd.DataFrame())
        disabled = qcw.empty
        if not disabled:
            excel_bytes = _to_excel_bytes(qcw)
        else:
            excel_bytes = b""
        st.download_button(
            "⬇️ Download QC",
            data=excel_bytes,
            file_name="qc_verified.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            disabled=disabled,
            use_container_width=True,
        )

    # ---------- Row 3: Link + Load (left)  |  Uploader (right) ----------
    st.markdown('<div class="strip-row">', unsafe_allow_html=True)
    lL, lR = st.columns([1.6, 1.0])

    with lL:
        st.caption("Paste the CSV/XLSX link sent by admin (or upload). Quick & compact.")
        col_link, col_load = st.columns([5, 1])
        with col_link:
            link_in = st.text_input("Paste link", key="qc_link_in", label_visibility="collapsed", placeholder="Paste the CSV/XLSX link", help=None)
        with col_load:
            if st.button("Load", use_container_width=True):
                try:
                    df = _read_from_link(link_in)
                    # standardize expected columns into qc_work; keep qc_src as original
                    ss.qc_src = df.copy()
                    ss.qc_work = df.copy()
                    ss.qc_idx = 0
                    st.toast("Loaded from link.", icon="✅")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with lR:
        st.caption("Upload the file here (Limit 200 MB per file)")
        up = st.file_uploader("Upload", type=["csv", "xlsx"], label_visibility="collapsed")
        if up is not None:
            try:
                dfu = _read_any(up)
                ss.qc_src = dfu.copy()
                ss.qc_work = dfu.copy()
                ss.qc_idx = 0
                st.toast("Loaded from file.", icon="✅")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    st.markdown("</div></div>", unsafe_allow_html=True)  # close strip-wrap
