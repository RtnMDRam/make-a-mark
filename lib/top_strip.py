# lib/top_strip.py
import io, re
from datetime import datetime
import pandas as pd
import streamlit as st

# ---------- helpers ----------
REQ_COLS = [
    "ID",
    "Question (English)", "Options (English)", "Answer (English)", "Explanation (English)",
    "Question (Tamil)",   "Options (Tamil)",   "Answer (Tamil)",   "Explanation (Tamil)",
]

def _clean_drive(url:str)->str:
    if not url: return url
    if "drive.google.com" not in url: return url
    m = re.search(r"/file/d/([^/]+)/", url)
    if m: return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    m = re.search(r"[?&]id=([^&]+)", url)
    if m: return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    return url

def _read_from_link(link:str)->pd.DataFrame:
    url = _clean_drive(link.strip())
    # try CSV first
    try:
        return pd.read_csv(url)
    except Exception:
        pass
    # then XLSX
    return pd.read_excel(url)

def _normalize_columns(df:pd.DataFrame)->pd.DataFrame:
    cols_lower = {c.lower():c for c in df.columns}
    def pick(*names):
        for n in names:
            if n in df.columns: return n
            ln = n.lower()
            if ln in cols_lower: return cols_lower[ln]
        return None
    col_map = {
        "ID"                    : pick("ID","Id","id"),
        "Question (English)"    : pick("Question (English)","Q_EN","Question_English","English Question"),
        "Options (English)"     : pick("Options (English)","OPT_EN","Options_English"),
        "Answer (English)"      : pick("Answer (English)","ANS_EN","Answer_English"),
        "Explanation (English)" : pick("Explanation (English)","EXP_EN","Explanation_English"),
        "Question (Tamil)"      : pick("Question (Tamil)","Q_TA","Question_Tamil","Tamil Question"),
        "Options (Tamil)"       : pick("Options (Tamil)","OPT_TA","Options_Tamil"),
        "Answer (Tamil)"        : pick("Answer (Tamil)","ANS_TA","Answer_Tamil"),
        "Explanation (Tamil)"   : pick("Explanation (Tamil)","EXP_TA","Explanation_Tamil"),
    }
    out = pd.DataFrame()
    for k, src in col_map.items():
        if src is None:
            raise RuntimeError(f"Missing column in file: {k}")
        out[k] = df[src]
    return out.reset_index(drop=True)

def _apply_subset(df:pd.DataFrame)->pd.DataFrame:
    # deep-link support: ?ids=1,3 or ?rows=11-25
    try:
        qp = st.query_params
    except Exception:
        qp = {}
    ids = qp.get("ids", [])
    rows = qp.get("rows", [])
    if ids:
        id_list = re.split(r"[,\s]+", ids[0].strip())
        id_list = [x for x in id_list if x!=""]
        return df[df["ID"].astype(str).isin(id_list)].reset_index(drop=True)
    if rows:
        m = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", rows[0])
        if m:
            a,b = int(m.group(1)), int(m.group(2))
            a,b = min(a,b), max(a,b)
            return df.iloc[a-1:b].reset_index(drop=True)
    return df

# ---------- UI: top strip ----------
def render_top_strip():
    ss = st.session_state

    # top rule
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    # date / title / time row
    c1,c2,c3 = st.columns([1.2,2.4,1.2])
    with c1:
        today = datetime.now()
        st.markdown(f"**{today.strftime('%d %b %Y')}**", help="Date")
    with c2:
        # small, centered Tamil + English label
        st.markdown("<div style='text-align:center;font-weight:700'>பாட பொருள் நிபுணர் பலகை / SME Panel</div>", unsafe_allow_html=True)
        rid = ss.get("qc_rid","—")
        st.caption(f"ID: {rid}")
    with c3:
        st.markdown(f"<div style='text-align:right'>{today.strftime('%H:%M')}</div>", unsafe_allow_html=True)

    # actions row (top buttons)
    b1,b2,b3 = st.columns([1,1,1])
    with b1:
        if st.button("💾 Save", use_container_width=True):
            _save_current()
    with b2:
        if st.button("✅ Mark Complete", use_container_width=True):
            _save_current(mark_complete=True)
    with b3:
        if st.button("📄 Save & Next", use_container_width=True):
            _save_current()
            if "qc_idx" in ss and ss.qc_idx < len(ss.qc_work)-1:
                ss.qc_idx += 1
                st.rerun()

    # compact loader block
    st.caption("Paste the CSV/XLSX link sent by admin (or upload). Quick & compact.")
    l, r = st.columns([6,1])
    with l:
        link_val = st.text_input("Paste the CSV/XLSX link", key="link_in", label_visibility="collapsed")
    with r:
        if st.button("Load", use_container_width=True):
            _load_from_link_or_upload()

    # uploader (secondary)
    up1 = st.file_uploader("Upload the file here (Limit 200 MB per file)", type=["csv","xlsx"])
    if up1 is not None:
        ss._last_upload = up1

    # If nothing loaded yet, stop here so SMEs only see the top strip
    if ss.get("qc_work") is None or ss.qc_work.empty:
        st.stop()

# ---------- persistence helpers ----------
def _load_from_link_or_upload():
    ss = st.session_state
    df = None
    try:
        if ss.get("link_in","").strip():
            df = _read_from_link(ss.link_in)
        elif ss.get("_last_upload") is not None:
            up = ss._last_upload
            if str(up.name).lower().endswith(".csv"):
                df = pd.read_csv(up)
            else:
                df = pd.read_excel(up)
        else:
            raise RuntimeError("Upload a file or paste a link, then press Load.")
        df = _normalize_columns(df)
        df = _apply_subset(df)
        ss.qc_src = df.copy()
        ss.qc_work = df.copy()
        ss.qc_idx = 0
        ss.qc_rid = str(ss.qc_work.iloc[0]["ID"])
        st.rerun()
    except Exception as e:
        st.error(str(e))

def _save_current(mark_complete=False):
    ss = st.session_state
    if "qc_work" not in ss or ss.qc_work is None or ss.qc_work.empty:
        return
    i = ss.qc_idx
    # Pull current editor values from session (keys were set by editor panel)
    def g(k, fallback):
        return ss.get(k, fallback)
    row = ss.qc_work.iloc[i]
    rid = str(row["ID"])
    # update Tamil editable fields
    ss.qc_work.at[i,"Question (Tamil)"]    = g(f"q_ta_{rid}", row["Question (Tamil)"])
    ss.qc_work.at[i,"Options (Tamil)"]     = " | ".join([
        g(f"a_ta_{rid}",""), g(f"b_ta_{rid}",""), g(f"c_ta_{rid}",""), g(f"d_ta_{rid}","")
    ])
    ss.qc_work.at[i,"Answer (Tamil)"]      = g(f"ans_ta_{rid}", row["Answer (Tamil)"])
    ss.qc_work.at[i,"Explanation (Tamil)"] = g(f"exp_ta_{rid}", row["Explanation (Tamil)"])
    ss.qc_rid = rid

    if mark_complete:
        buf = io.BytesIO()
        ss.qc_work.to_excel(buf, index=False)
        buf.seek(0)
        st.download_button("⬇️ Download QC File", data=buf, file_name="qc_verified.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
