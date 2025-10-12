# lib/top_strip.py
import io
import re
import pandas as pd
import streamlit as st

REQ_COLS_CANON = [
    "ID",
    "Question (English)", "Options (English)", "Answer (English)", "Explanation (English)",
    "Question (Tamil)",   "Options (Tamil)",   "Answer (Tamil)",   "Explanation (Tamil)",
]

# map many possible headers -> canonical headers
COL_ALIASES = {
    "ID": ["ID","Id","id","_id","_ID","Number","Row ID","Row"],
    "Question (English)": ["Question (English)","Q_EN","Question_English","English Question","EN_Q"],
    "Options (English)" : ["Options (English)","OPT_EN","Options_English","EN_Options","Options (A–D)","Options (A-D)"],
    "Answer (English)"  : ["Answer (English)","ANS_EN","Answer_English","EN_Answer","Answer"],
    "Explanation (English)": ["Explanation (English)","EXP_EN","Explanation_English","EN_Explanation","Explanation"],
    "Question (Tamil)"  : ["Question (Tamil)","Q_TA","Question_Tamil","TA_Q","Tamil Question"],
    "Options (Tamil)"   : ["Options (Tamil)","OPT_TA","Options_Tamil","TA_Options"],
    "Answer (Tamil)"    : ["Answer (Tamil)","ANS_TA","Answer_Tamil","TA_Answer"],
    "Explanation (Tamil)": ["Explanation (Tamil)","EXP_TA","Explanation_Tamil","TA_Explanation"],
}

def _pick(name, cols_lower):
    for alias in COL_ALIASES[name]:
        al = alias.lower()
        if al in cols_lower: return cols_lower[al]
    return None

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols_lower = {c.lower(): c for c in df.columns}
    out_cols = {}
    missing = []
    for k in REQ_COLS_CANON:
        src = _pick(k, cols_lower)
        if src is None:
            # allow QC_TA optional (older sheets)
            if k == "Explanation (Tamil)": 
                out_cols[k] = ""
                continue
            missing.append(k)
        else:
            out_cols[k] = src
    if missing:
        raise RuntimeError(f"Missing required columns: {', '.join(missing)}")
    out = pd.DataFrame({k: df[v] if v != "" else "" for k,v in out_cols.items()})
    return out.reset_index(drop=True)

def _clean_drive(url:str)->str:
    url=url.strip()
    if "drive.google.com" not in url: return url
    m=re.search(r"/file/d/([^/]+)/", url)
    if m: return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    m=re.search(r"[?&]id=([^&]+)", url)
    if m: return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    return url

def _read_any(src):
    # src can be URL string or a file-like
    if isinstance(src, str):
        url = _clean_drive(src)
        try:
            return pd.read_csv(url)
        except Exception:
            return pd.read_excel(url)
    # uploaded file
    try:
        return pd.read_csv(src)
    except Exception:
        src.seek(0)
        return pd.read_excel(src)

def _publish(df: pd.DataFrame):
    ss = st.session_state
    df = normalize_columns(df)
    ss.qc_src  = df.copy()
    ss.qc_work = df.copy()
    ss.qc_idx  = 0

def render_top_strip():
    ss = st.session_state
    with st.container():
        c1,c2,c3,c4 = st.columns([1.2,1.2,1.2,1.2])
        with c1:
            st.button("💾 Save", key="btn_save_top")
        with c2:
            st.button("✅ Mark Complete", key="btn_done_top")
        with c3:
            st.button("📄 Save & Next", key="btn_next_top")
        with c4:
            st.download_button("📥 Download QC", data=b"", file_name="qc_verified.xlsx", key="btn_dl_top", disabled=True)

        st.caption("Paste the CSV/XLSX link sent by admin (or upload). Quick & compact.")

        lcol, rcol = st.columns([1,1])
        with lcol:
            link = st.text_input(" ", key="qc_link_in", label_visibility="collapsed", placeholder="Paste the CSV/XLSX link")
        with rcol:
            up = st.file_uploader("Upload the file here (Limit 200 MB per file)", type=["csv","xlsx"])

        l2, r2 = st.columns([0.2, 1.8])
        with l2:
            if st.button("Load", key="btn_load"):
                try:
                    if link.strip():
                        df = _read_any(link.strip())
                    elif up is not None:
                        # keep a copy in memory for excel reader
                        buf = io.BytesIO(up.getbuffer())
                        buf.seek(0)
                        df = _read_any(buf)
                        ss._last_upload_name = up.name
                    else:
                        st.warning("Empty link.", icon="⚠️")
                        st.stop()
                    _publish(df)
                    st.success("Loaded from file.", icon="✅")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not load: {e}", icon="🛑")
        with r2:
            if up is not None:
                st.write(f"📄 {up.name}")
