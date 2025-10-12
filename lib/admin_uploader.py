# lib/admin_uploader.py
# Compact admin loader strip (10% height): Browse | Paste link | Load
from __future__ import annotations
import io, re
import pandas as pd
import streamlit as st

REQ_COLS = [
    "ID",
    "Question (English)", "Options (English)", "Answer (English)", "Explanation (English)",
    "Question (Tamil)",   "Options (Tamil)",   "Answer (Tamil)",   "Explanation (Tamil)",
    "QC_TA",
]

def _clean_drive(url: str) -> str:
    if "drive.google.com" not in url:
        return url.strip()
    # File page → direct download
    m = re.search(r"/file/d/([^/]+)/", url)
    if m:
        return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    # Sharing link (id=)
    m = re.search(r"[?&]id=([^&]+)", url)
    if m:
        return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    return url.strip()

def _read_from_link(url: str) -> pd.DataFrame:
    url = _clean_drive(url)
    # try CSV then XLSX
    try:
        return pd.read_csv(url)
    except Exception:
        pass
    return pd.read_excel(url)

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols_lower = {c.lower(): c for c in df.columns}
    def pick(*names):
        for n in names:
            if n in df.columns: return n
            ln = n.lower()
            if ln in cols_lower: return cols_lower[ln]
        return None

    col_map = {
        "ID"                   : pick("ID","Id","id"),
        "Question (English)"   : pick("Question (English)","Q_EN","Question_English","English Question"),
        "Options (English)"    : pick("Options (English)","OPT_EN","Options_English"),
        "Answer (English)"     : pick("Answer (English)","ANS_EN","Answer_English"),
        "Explanation (English)": pick("Explanation (English)","EXP_EN","Explanation_English"),
        "Question (Tamil)"     : pick("Question (Tamil)","Q_TA","Tamil Question","Question_Tamil"),
        "Options (Tamil)"      : pick("Options (Tamil)","OPT_TA","Options_Tamil"),
        "Answer (Tamil)"       : pick("Answer (Tamil)","ANS_TA","Answer_Tamil"),
        "Explanation (Tamil)"  : pick("Explanation (Tamil)","EXP_TA","Explanation_Tamil"),
        "QC_TA"                : pick("QC_TA","QC Verified (Tamil)","QC_Tamil"),
    }
    out = pd.DataFrame()
    for k, src in col_map.items():
        if src is None:
            # Allow QC_TA to be absent; create empty column for it
            if k == "QC_TA":
                out[k] = ""
                continue
            raise RuntimeError(f"Missing columns in the file: {k}")
        out[k] = df[src]
    return out.reset_index(drop=True)

def _apply_subset(df: pd.DataFrame) -> pd.DataFrame:
    """Allow deep links like ?ids=153380 or ?rows=11-25"""
    qp = st.query_params
    ids  = qp.get("ids", [])
    rows = qp.get("rows", [])
    if ids:
        id_list = re.split(r"[, \s]+", ids[0].strip())
        id_list = [x for x in id_list if x != ""]
        return df[df["ID"].astype(str).isin(id_list)].reset_index(drop=True)
    if rows:
        m = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", rows[0])
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            a, b = min(a,b), max(a,b)
            return df.iloc[a-1:b].reset_index(drop=True)
    return df

def render_admin_loader() -> None:
    """Top strip UI. Writes ss.qc_src / ss.qc_work / ss.qc_idx if loaded."""
    ss = st.session_state

    # ---------- ultra-compact CSS for the strip ----------
    st.markdown("""
    <style>
    .admwrap .row{display:grid;grid-template-columns:1.2fr 1fr auto;gap:8px;align-items:center}
    .admwrap .uploader, .admwrap .linkin {margin:0 !important;}
    .admwrap .seg{background:#eaf2ff;border:1px solid #cfe0ff;border-radius:10px;padding:8px 10px;}
    .admwrap .loadbtn button{height:40px;padding:0 18px;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="admwrap seg">', unsafe_allow_html=True)
    st.caption("Paste the CSV/XLSX link sent by Admin, or upload the file.")
    st.markdown('<div class="row">', unsafe_allow_html=True)

    # Left: file uploader
    upl = st.file_uploader("Upload file (CSV/XLSX)", type=["csv","xlsx"], label_visibility="collapsed", key="adm_upl")

    # Middle: link input
    link = st.text_input("…or paste link (CSV/XLSX/Drive)", value=ss.get("adm_link",""), label_visibility="collapsed", key="adm_link")

    # Right: Load button
    load_click = st.button("Load", key="adm_load")

    st.markdown('</div></div>', unsafe_allow_html=True)

    if load_click:
        try:
            if upl is not None:
                if upl.name.lower().endswith(".csv"):
                    df = pd.read_csv(upl)
                else:
                    df = pd.read_excel(upl)
            else:
                if not link.strip():
                    raise RuntimeError("Upload a file or paste a link.")
                df = _read_from_link(link)

            df = _normalize_columns(df)
            df = _apply_subset(df)
            if "QC_TA" not in df.columns:
                df["QC_TA"] = ""  # safety

            # Publish to session for the page to consume
            ss.qc_src  = df.copy()
            ss.qc_work = df.copy()
            ss.qc_idx  = 0
            st.toast("Loaded ✅", icon="✅")
            st.rerun()
        except Exception as e:
            st.error(str(e))
