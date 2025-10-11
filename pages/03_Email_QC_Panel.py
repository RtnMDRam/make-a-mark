# pages/03_Email_QC_Panel.py
# Single-page, compact SME QC panel (English ↔ Tamil)
# - Tight header (5% strip): title, ID/progress, prev/next, Excel
# - 3 stacked panels (no wasted gaps):
#     1) English Version (read-only)
#     2) Tamil Original (read-only)
#     3) SME Edit Console (question, A–D split in two rows, answer, explanation)
# - Yellow: live preview (mirrors edit fields)
# - Red: last saved QC text

import re
import pandas as pd
import streamlit as st

from lib import (
    apply_theme, read_bilingual, export_qc,
    auto_guess_map, ensure_work
)

# ---------- page ----------
st.set_page_config(page_title="SME QC Panel", page_icon="📝", layout="wide")

# ---------- CSS: ultra-compact layout ----------
st.markdown("""
<style>
/* tighten global spacing */
section.main > div {padding-top: 0.35rem;}
.block {padding: 10px 12px; margin: 6px 0 10px 0; border-radius: 10px; border: 1.5px solid var(--secondary-background-color);}
.block.en {background: rgba(66,133,244,.08); border-color: rgba(66,133,244,.35);}
.block.ta {background: rgba(52,168,83,.10); border-color: rgba(52,168,83,.35);}
.block.qc {background: rgba(244,180,0,.10); border-color: rgba(244,180,0,.35);}
.block.saved {background: rgba(234,67,53,.08); border-color: rgba(234,67,53,.35);}
.block h5 {margin: 0 0 6px 0; font-size: 0.95rem;}
.rowline {margin: 4px 0;}
.smallcap {opacity:.7; font-size:.85rem; margin-bottom:4px}
.stTextArea textarea {line-height: 1.45;}
.stTextInput > div > div > input {height: 38px;}
label {margin-bottom: 2px !important;}
/* compact element gaps */
.element-container {margin-bottom: 8px;}
/* header bar */
.topbar {display:flex; align-items:center; gap:.6rem; margin: 4px 0 6px 0;}
.topbar .grow {flex: 1;}
.idtag {font-weight:600; padding:4px 8px; border-radius: 6px; background:var(--secondary-background-color);}
.progresswrap {display:flex; align-items:center; gap:.6rem;}
.tip {font-size:.85rem; opacity:.75; margin-top:.35rem}
</style>
""", unsafe_allow_html=True)

# ---------- session ----------
ss = st.session_state
if "night" not in ss:         ss.night = False
if "qc_src" not in ss:        ss.qc_src = pd.DataFrame()
if "qc_map" not in ss:        ss.qc_map = {}
if "qc_work" not in ss:       ss.qc_work = pd.DataFrame()
if "qc_idx" not in ss:        ss.qc_idx = 0
if "uploaded_name" not in ss: ss.uploaded_name = None
if "show_loader" not in ss:   ss.show_loader = True  # reopen to change file

apply_theme(ss.night, hide_sidebar=True)  # sidebar hidden for full width

# ---------- helpers ----------
def _txt(s) -> str:
    s = "" if s is None else str(s)
    return s.replace("\r\n", "\n").replace("\r", "\n").strip()

_opt_pat = re.compile(r"\b[ABCD]\)?[)\.:]|[①②③④]|\|\s*[ABCD]\)?", re.IGNORECASE)

def split_options(text: str):
    """Return dict {'A','B','C','D'} from a combined options string.
       Extremely tolerant; falls back to best-effort split by | . """
    t = _txt(text)
    # Common separators used in your sheets
    parts = re.split(r"\s*\|\s*|\s*[;]\s*|\s*[।]\s*\|\s*|\s*⑴|⑵|⑶|⑷", t)
    parts = [p for p in parts if p.strip()]
    if len(parts) >= 4:
        return dict(zip(list("ABCD"), [p.strip(" .:)") for p in parts[:4]]))
    # Look for “A) … B) … C) … D) …”
    chunks = re.split(r"(?:^| )A\)[\s:]*| B\)[\s:]*| C\)[\s:]*| D\)[\s:]*", t)
    chunks = [c for c in chunks if c and c.strip()]
    if len(chunks) >= 4:
        return dict(zip(list("ABCD"), [c.strip() for c in chunks[:4]]))
    # last fallback: fill safely
    fill = {"A":"", "B":"", "C":"", "D":""}
    for i, k in enumerate("ABCD"):
        if i < len(parts): fill[k] = parts[i].strip()
    return fill

def join_options(ABCD: dict) -> str:
    return f"A) {ABCD.get('A','').strip()} | B) {ABCD.get('B','').strip()} | C) {ABCD.get('C','').strip()} | D) {ABCD.get('D','').strip()}"

def compose_qc_ta(q, abcd, ans, exp):
    q = _txt(q); ans = _txt(ans); exp = _txt(exp)
    return f"கேள்வி: {q}\nவிருப்பங்கள் (A–D): {join_options(abcd)}\nபதில்: {ans}\nவிளக்கம்:\n{exp}"

# ---------- load/map ----------
with st.expander("📥 Load bilingual file (.csv/.xlsx) & map columns", expanded=ss.show_loader):
    up = st.file_uploader("Upload bilingual file", type=["csv","xlsx"], label_visibility="collapsed")
    if up is not None:
        src = read_bilingual(up)
        if src.empty:
            st.error("File appears empty.")
        else:
            ss.uploaded_name = up.name.rsplit(".",1)[0]
            ss.qc_src = src
            auto = auto_guess_map(src)
            cols = list(src.columns)

            c1, c2 = st.columns(2)
            with c1:
                id_col   = st.selectbox("ID", cols, index=cols.index(auto["ID"]) if auto["ID"] in cols else 0)
                en_q     = st.selectbox("Question (English)", cols, index=cols.index(auto["Q_EN"]) if auto["Q_EN"] in cols else 0)
                en_opt   = st.selectbox("Options (English)",  cols, index=cols.index(auto["OPT_EN"]) if auto["OPT_EN"] in cols else 0)
                en_ans   = st.selectbox("Answer (English)",   cols, index=cols.index(auto["ANS_EN"]) if auto["ANS_EN"] in cols else 0)
                en_exp   = st.selectbox("Explanation (English)", cols, index=cols.index(auto["EXP_EN"]) if auto["EXP_EN"] in cols else 0)
            with c2:
                ta_q     = st.selectbox("Question (Tamil)", cols, index=cols.index(auto["Q_TA"]) if auto["Q_TA"] in cols else 0)
                ta_opt   = st.selectbox("Options (Tamil)",  cols, index=cols.index(auto["OPT_TA"]) if auto["OPT_TA"] in cols else 0)
                ta_ans   = st.selectbox("Answer (Tamil)",   cols, index=cols.index(auto["ANS_TA"]) if auto["ANS_TA"] in cols else 0)
                ta_exp   = st.selectbox("Explanation (Tamil)", cols, index=cols.index(auto["EXP_TA"]) if auto["EXP_TA"] in cols else 0)

            if st.button("✅ Confirm mapping & start QC"):
                ss.qc_map = {
                    "ID": id_col,
                    "Q_EN": en_q, "OPT_EN": en_opt, "ANS_EN": en_ans, "EXP_EN": en_exp,
                    "Q_TA": ta_q, "OPT_TA": ta_opt, "ANS_TA": ta_ans, "EXP_TA": ta_exp,
                    # We store last-saved QC (Tamil) in a safe extra column created by ensure_work
                    # (it already preserves headers/order).
                }
                ss.qc_work = ensure_work(ss.qc_src, ss.qc_map)
                ss.qc_idx = 0
                ss.show_loader = False
                st.success(f"Loaded {len(ss.qc_work)} rows. Headers preserved on export.")
                st.rerun()

if ss.qc_work.empty:
    st.stop()

# shorthand
m = ss.qc_map
row = ss.qc_work.iloc[ss.qc_idx]

# ---------- top bar (≈5%) ----------
st.markdown(
    "<div class='topbar'>"
    "<div class='idtag'>🆔 ID: {}</div>"
    "<div class='grow progresswrap'>".format(row[m["ID"]]) +
    "</div></div>", unsafe_allow_html=True
)
st.progress((ss.qc_idx + 1) / len(ss.qc_work))
left, mid, right = st.columns([1,6,2])
with left:
    if st.button("◀️ Prev", use_container_width=True, disabled=ss.qc_idx<=0):
        ss.qc_idx = max(0, ss.qc_idx-1); st.rerun()
with mid:
    st.caption(f"English ↔ Tamil · single-page QC · Row {ss.qc_idx+1} / {len(ss.qc_work)}")
    if ss.show_loader:
        st.info("Upload/mapping open above. Close the expander after confirming.")
with right:
    if st.button("Next ▶️", use_container_width=True, disabled=ss.qc_idx>=len(ss.qc_work)-1):
        ss.qc_idx = min(len(ss.qc_work)-1, ss.qc_idx+1); st.rerun()

# ---------- read-only English / Tamil ----------
en_q  = _txt(row[m["Q_EN"]]);   en_op = _txt(row[m["OPT_EN"]]); en_ans = _txt(row[m["ANS_EN"]]); en_exp = _txt(row[m["EXP_EN"]])
ta_q0 = _txt(row[m["Q_TA"]]);   ta_op0= _txt(row[m["OPT_TA"]]); ta_ans0= _txt(row[m["ANS_TA"]]); ta_exp0= _txt(row[m["EXP_TA"]])

st.markdown(f"""
<div class='block en'>
  <h5>English Version / ஆங்கிலம்</h5>
  <div class='rowline'><span class='smallcap'>Question</span><br>{en_q}</div>
  <div class='rowline'><span class='smallcap'>Options (A–D)</span><br>{en_op}</div>
  <div class='rowline'><span class='smallcap'>Answer</span><br>{en_ans}</div>
  <div class='rowline'><span class='smallcap'>Explanation</span><br>{en_exp}</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class='block ta'>
  <h5>Tamil Original / தமிழ் மூலப் பதிப்பு</h5>
  <div class='rowline'><span class='smallcap'>கேள்வி</span><br>{ta_q0}</div>
  <div class='rowline'><span class='smallcap'>விருப்பங்கள் (A–D)</span><br>{ta_op0}</div>
  <div class='rowline'><span class='smallcap'>பதில்</span><br>{ta_ans0}</div>
  <div class='rowline'><span class='smallcap'>விளக்கம்</span><br>{ta_exp0}</div>
</div>
""", unsafe_allow_html=True)

# ---------- SME edit console (50%) ----------
# seed edit fields from the Tamil Original on first visit to this row
row_key = f"r{ss.qc_idx}"
if f"edit_init_{row_key}" not in ss:
    ss[f"q_{row_key}"]   = ta_q0
    opts0 = split_options(ta_op0)
    ss[f"oa_{
