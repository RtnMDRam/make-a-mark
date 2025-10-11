# pages/03_Email_QC_Panel.py
# SME QC Panel — compact, iPad-first layout

import re
import pandas as pd
import streamlit as st

from lib import (
    apply_theme, read_bilingual, export_qc,
    auto_guess_map, ensure_work
)

st.set_page_config(page_title="SME QC Panel", page_icon="📝", layout="wide")

# ============ CSS (tight layout, hide Streamlit chrome we don't need) ============
st.markdown("""
<style>
/* remove extra top white gap & icon row spacing */
section.main > div { padding-top: 0.25rem !important; }
.block-container { padding-top: 0.6rem !important; max-width: 1200px; }
/* reduce expander padding */
.st-emotion-cache-1avcm0n, .st-emotion-cache-1h9usn1 { padding: 0.4rem 0.6rem !important; }
/* compact headings inside blue/green/yellow boxes */
.box { border: 2px solid var(--box); border-radius: 12px; padding: .5rem .9rem; margin: .45rem 0 .6rem; background: var(--bg); }
.box h4 { margin: 0 0 .35rem 0; font-size: .95rem; font-weight: 700; display: inline-block; padding: .15rem .45rem; border-radius: .4rem; background: #fff6; }
.box .mono { white-space: pre-wrap; line-height: 1.35; font-size: 0.98rem; }
.box.en { --box:#89b3ff; --bg:#eaf2ff; }
.box.ta { --box:#85cf9b; --bg:#edf9f1; }
.box.live { --box:#e7c34f; --bg:#fff7da; }
.badge { display:inline-block; padding:.15rem .5rem; border-radius:.5rem; font-size:.80rem; background:#eef; border:1px solid #cfe; margin-left:.5rem;}
.idtag{display:inline-block;padding:.15rem .55rem;border-radius:.6rem;background:#f0f4ff;border:1px solid #c6d3ff;font-weight:700}
.small{font-size:.85rem; opacity:.8}
.inline-row { display:flex; gap:.6rem; flex-wrap:wrap; }
.opt { flex:1 1 calc(50% - .6rem); }
.stTextInput > div > div input, .stTextArea textarea { font-size:1rem; }
button[kind="secondary"] { margin-right:.4rem }
</style>
""", unsafe_allow_html=True)

# ============ Session ============
ss = st.session_state
if "night" not in ss: ss.night = False
if "qc_src" not in ss: ss.qc_src = pd.DataFrame()
if "qc_map" not in ss: ss.qc_map = {}
if "qc_work" not in ss: ss.qc_work = pd.DataFrame()
if "qc_idx" not in ss: ss.qc_idx = 0
if "uploaded_name" not in ss: ss.uploaded_name = None

# Theme (kept simple; menu can be hidden via apply_theme param)
apply_theme(night=ss.night, hide_sidebar=False)

# ============ Helpers ============
REQ_KEYS = ["ID","Q_EN","OPT_EN","ANS_EN","EXP_EN","Q_TA","OPT_TA","ANS_TA","EXP_TA"]
QC_COL_KEY = "QC_TA"   # column for SME verified text (single combined field)

def _validate_map(df: pd.DataFrame, m: dict) -> tuple[bool, list]:
    missing = []
    for k in (REQ_KEYS + [QC_COL_KEY]):
        col = m.get(k)
        if col and col not in df.columns:
            missing.append([k, col])
    return (len(missing) == 0, missing)

def _txt(x) -> str:
    if pd.isna(x): return ""
    # normalize Excel newlines
    return str(x).replace("\r\n","\n").strip()

def _split_opts(s: str) -> list[str]:
    # Accept "A) ... | B) ..." or "1) ..." etc; fallback on pipes
    t = _txt(s)
    if not t: return ["","","",""]
    # split by pipe first
    parts = [p.strip() for p in t.split("|") if p.strip()]
    if len(parts) >= 4:
        return parts[:4]
    # try to split by A) B) C) D)
    m = re.split(r"(?:^|\\n)\\s*[A-D]\\)\\s*", t)
    parts = [p.strip() for p in m if p.strip()]
    while len(parts) < 4: parts.append("")
    return parts[:4]

def _safe_row(row, m, key):
    col = m.get(key)
    return _txt(row[col]) if col in row.index else ""

def _compose_qc_text(q, a, b, c, d, ans, exp):
    seg = []
    if q:  seg.append(q)
    if any([a,b,c,d]):
        seg.append(f"விருப்பங்கள் (A–D): A) {a} | B) {b} | C) {c} | D) {d}")
    if ans: seg.append(f"பதில்: {ans}")
    if exp: seg.append(f"விளக்கம்: {exp}")
    return "\n".join(seg)

# ============ Uploader & mapping ============
with st.expander("📥 Load bilingual file (.csv/.xlsx) & map columns", expanded=ss.qc_src.empty):
    up = st.file_uploader("Upload bilingual file", type=["csv","xlsx"])
    if up:
        src = read_bilingual(up)
        if src.empty:
            st.error("File appears empty.")
        else:
            ss.uploaded_name = up.name.rsplit(".",1)[0]
            ss.qc_src = src
            guess = auto_guess_map(src)
            # Make sure we always have a QC column name (create if absent on ensure_work)
            guess.setdefault(QC_COL_KEY, "QC_TA")
            st.success(f"Loaded {len(src)} rows.")
            # Keep current map if set; else apply guess
            if not ss.qc_map:
                ss.qc_map = guess

# Require data
if ss.qc_src.empty and ss.qc_work.empty:
    st.stop()

# Create working df (preserve headers & order)
if ss.qc_work.empty:
    ss.qc_work = ensure_work(ss.qc_src, ss.qc_map)

# Validate map against the current file
ok, miss = _validate_map(ss.qc_src, ss.qc_map)
if not ok:
    st.error("Some mapped column names are not present in the uploaded file.\n\nFix these mapping entries:")
    st.json(miss)
    st.stop()

# ============ Top bar (compact) ============
top = st.container()
with top:
    c1,c2,c3,c4 = st.columns([2,2,4,2])
    with c1:
        st.subheader("📝 SME QC Panel")
        st.caption("English ⇄ Tamil · Row {}/{}".format(ss.qc_idx+1, len(ss.qc_work)))
    with c2:
        rid = _safe_row(ss.qc_work.iloc[ss.qc_idx], ss.qc_map, "ID")
        st.markdown(f"<div class='idtag'>ID: {rid or '—'}</div>", unsafe_allow_html=True)
    with c3:
        st.progress((ss.qc_idx+1)/len(ss.qc_work))
    with c4:
        bprev, bnext = st.columns(2)
        with bprev:
            if st.button("◀︎ Prev", use_container_width=True, disabled=ss.qc_idx<=0):
                ss.qc_idx = max(0, ss.qc_idx-1); st.rerun()
        with bnext:
            if st.button("Next ▶︎", use_container_width=True, disabled=ss.qc_idx>=len(ss.qc_work)-1):
                ss.qc_idx = min(len(ss.qc_work)-1, ss.qc_idx+1); st.rerun()

# ============ Current row material ============
row = ss.qc_work.iloc[ss.qc_idx]
M = ss.qc_map

en_q   = _safe_row(row, M, "Q_EN")
en_op  = _safe_row(row, M, "OPT_EN")
en_ans = _safe_row(row, M, "ANS_EN")
en_exp = _safe_row(row, M, "EXP_EN")

ta_q   = _safe_row(row, M, "Q_TA")
ta_op  = _safe_row(row, M, "OPT_TA")
ta_ans = _safe_row(row, M, "ANS_TA")
ta_exp = _safe_row(row, M, "EXP_TA")

qc_col = M.get(QC_COL_KEY, "QC_TA")
if qc_col not in ss.qc_work.columns:
    ss.qc_work[qc_col] = ""

# ============ English panel ============
en_box = f"**Q:** {en_q}\n\n**Options (A–D):** {en_op}\n\n**Answer:** {en_ans}\n\n**Explanation:** {en_exp}"
st.markdown(f"<div class='box en'><h4>English Version / ஆங்கிலம்</h4><div class='mono'>{en_box}</div></div>", unsafe_allow_html=True)

# ============ Tamil Original panel ============
ta_box = f"**கேள்வி:** {ta_q}\n\n**விருப்பங்கள் (A–D):** {ta_op}\n\n**பதில்:** {ta_ans}\n\n**விளக்கம்:** {ta_exp}"
st.markdown(f"<div class='box ta'><h4>Tamil Original / தமிழ் மூலப் பதிப்பு</h4><div class='mono'>{ta_box}</div></div>", unsafe_allow_html=True)

# ============ SME Edit Console ============
st.markdown(f"<div class='box live'><h4>SME Edit Console / ஆசிரியர் திருத்தம்</h4></div>", unsafe_allow_html=True)

# Initialize per-row edit keys once (pre-fill from Tamil original)
row_key = f"r{ss.qc_idx}"
defaults_done_key = f"init_{row_key}"
if not ss.get(defaults_done_key):
    A,B,C,D = _split_opts(ta_op)
    ss[f"q_{row_key}"]   = ta_q
    ss[f"a_{row_key}"]   = A
    ss[f"b_{row_key}"]   = B
    ss[f"c_{row_key}"]   = C
    ss[f"d_{row_key}"]   = D
    ss[f"ans_{row_key}"] = ta_ans
    ss[f"exp_{row_key}"] = ta_exp
    ss[defaults_done_key] = True

q_val   = st.text_area("கேள்வி / Question (TA)", value=ss[f"q_{row_key}"], key=f"q_{row_key}", height=110)
colAB = st.container()
with colAB:
    A,B = st.columns(2)
    with A:
        ss[f"a_{row_key}"] = st.text_input("A", value=ss[f"a_{row_key}"], key=f"a_{row_key}")
        ss[f"c_{row_key}"] = st.text_input("C", value=ss[f"c_{row_key}"], key=f"c_{row_key}")
    with B:
        ss[f"b_{row_key}"] = st.text_input("B", value=ss[f"b_{row_key}"], key=f"b_{row_key}")
        ss[f"d_{row_key}"] = st.text_input("D", value=ss[f"d_{row_key}"], key=f"d_{row_key}")

ans_val = st.text_input("பதில் / Answer (TA)", value=ss[f"ans_{row_key}"], key=f"ans_{row_key}")
exp_val = st.text_area("விளக்கம் / Explanation (TA)", value=ss[f"exp_{row_key}"], key=f"exp_{row_key}", height=150)

# Live preview
live_txt = _compose_qc_text(
    q_val, ss[f"a_{row_key}"], ss[f"b_{row_key}"],
    ss[f"c_{row_key}"], ss[f"d_{row_key}"], ans_val, exp_val
)
st.markdown(f"<div class='box live'><h4>Live Preview / நேரடி முன்னோட்டம்</h4><div class='mono'>{live_txt}</div></div>", unsafe_allow_html=True)

# Actions
b1,b2,b3 = st.columns([1.2,1.2,3])
with b1:
    if st.button("💾 Save this row", use_container_width=True):
        ss.qc_work.at[ss.qc_idx, qc_col] = live_txt
        st.success("Saved to QC column (red panel text updated on next load).")
with b2:
    if st.button("💾 Save & Next ▶️", use_container_width=True, disabled=ss.qc_idx>=len(ss.qc_work)-1):
        ss.qc_work.at[ss.qc_idx, qc_col] = live_txt
        ss.qc_idx = min(len(ss.qc_work)-1, ss.qc_idx+1)
        st.rerun()

# ============ Export ============
st.subheader("⬇️ Export")
xlsx_bytes, csv_bytes = export_qc(ss.qc_src, ss.qc_work, ss.qc_map)
base = (ss.uploaded_name or "qc_file").replace(".","_")
if xlsx_bytes and csv_bytes:
    st.download_button("Download QC Excel (.xlsx)", data=xlsx_bytes,
        file_name=f"{base}_qc_verified.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.download_button("Download QC CSV (.csv)", data=csv_bytes,
        file_name=f"{base}_qc_verified.csv", mime="text/csv")
