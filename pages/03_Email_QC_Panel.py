# pages/03_Email_QC_Panel.py
# SME QC Panel — single page, compact iPad layout:
# Header (5%) · Originals (EN, TA) · Edit console (TA question, options A–D, answer, explanation)

import io, os, re
import pandas as pd
import streamlit as st

# ---- modular helpers ----
from lib import apply_theme, read_bilingual, export_qc, auto_guess_map, ensure_work

# ---------- Page + CSS ----------
st.set_page_config(page_title="SME QC Panel", page_icon="📝", layout="wide")

# minimal chrome + hide sidebar, tighten paddings
st.markdown("""
<style>
/* remove default top padding & make content full width */
.main .block-container { padding-top: 0.6rem; padding-bottom: 0.6rem; max-width: 1200px; }
section[data-testid="stSidebar"] { display: none !important; }  /* hide left app menu */
header[data-testid="stHeader"] { height: 0; visibility: hidden; } /* hide Streamlit header bar */
.small { font-size:0.85rem; opacity:.8 }
.tag { display:inline-block; padding:.25rem .55rem; border-radius:.5rem; background:#eef1f6; border:1px solid #d7dbe4; font-weight:600; }
.hdr { display:flex; gap:.75rem; align-items:center; justify-content:space-between; border-bottom:1px solid #e6e6e6; padding:.4rem 0 .6rem 0; }
.hstack { display:flex; gap:.5rem; align-items:center; }
.panel { border:1px solid #d7dbe4; border-radius:.6rem; padding:.6rem .8rem; margin:.4rem 0; }
.panel.en { background:#edf4ff; }
.panel.ta { background:#eaf7ea; }
.panel.edit { background:#fff7ea; border-color:#f1d79b; }
.label { font-weight:700; margin-bottom:.35rem; }
.mono { white-space:pre-wrap; word-break:break-word; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
.scroll { max-height: 28vh; overflow:auto; }
.scroll-half { max-height: 22vh; overflow:auto; }
.rowgap { display:grid; grid-template-columns: 1fr 1fr; gap:.6rem; }
.tip { font-size:.85rem; opacity:.85; }
.btnrow { display:flex; gap:.6rem; align-items:center; }
</style>
""", unsafe_allow_html=True)

# ---------- Session ----------
ss = st.session_state
if "night" not in ss: ss.night = False
if "qc_src" not in ss: ss.qc_src = pd.DataFrame()
if "qc_map" not in ss: ss.qc_map = {}
if "qc_work" not in ss: ss.qc_work = pd.DataFrame()
if "qc_idx" not in ss: ss.qc_idx = 0
if "uploaded_name" not in ss: ss.uploaded_name = None

apply_theme(ss.night, hide_sidebar=True)

# ---------- Upload + map (one-time) ----------
with st.expander("📥 Load bilingual file (.csv/.xlsx) & map columns", expanded=ss.qc_src.empty):
    up = st.file_uploader("Upload bilingual file", type=["csv","xlsx"])
    if up:
        src = read_bilingual(up)
        if src.empty:
            st.error("File appears empty.")
        else:
            ss.uploaded_name = up.name.rsplit(".",1)[0]
            ss.qc_src = src
            auto = auto_guess_map(src)
            st.write("**Map required columns** (kept exactly in export):")
            cols = list(src.columns)

            sel = {}
            c1, c2 = st.columns(2)
            with c1:
                sel["ID"]     = st.selectbox("ID", cols, index=cols.index(auto["ID"]) if auto["ID"] in cols else 0)
                sel["Q_EN"]   = st.selectbox("Question (English)",  cols, index=cols.index(auto["Q_EN"]) if auto["Q_EN"] in cols else 0)
                sel["OPT_EN"] = st.selectbox("Options (English)",   cols, index=cols.index(auto["OPT_EN"]) if auto["OPT_EN"] in cols else 0)
                sel["ANS_EN"] = st.selectbox("Answer (English)",    cols, index=cols.index(auto["ANS_EN"]) if auto["ANS_EN"] in cols else 0)
                sel["EXP_EN"] = st.selectbox("Explanation (English)", cols, index=cols.index(auto["EXP_EN"]) if auto["EXP_EN"] in cols else 0)
            with c2:
                sel["Q_TA"]   = st.selectbox("Question (Tamil)",  cols, index=cols.index(auto["Q_TA"]) if auto["Q_TA"] in cols else 0)
                sel["OPT_TA"] = st.selectbox("Options (Tamil)",   cols, index=cols.index(auto["OPT_TA"]) if auto["OPT_TA"] in cols else 0)
                sel["ANS_TA"] = st.selectbox("Answer (Tamil)",    cols, index=cols.index(auto["ANS_TA"]) if auto["ANS_TA"] in cols else 0)
                sel["EXP_TA"] = st.selectbox("Explanation (Tamil)", cols, index=cols.index(auto["EXP_TA"]) if auto["EXP_TA"] in cols else 0)
                # QC output column (create if missing)
                qc_choices = cols + ["<create new column ‘QC_TA’>"]
                qc_pick = st.selectbox("QC Verified (Tamil) → save into", qc_choices,
                                       index=(qc_choices.index("QC_TA") if "QC_TA" in cols else len(qc_choices)-1))
                if qc_pick == "<create new column ‘QC_TA’>":
                    sel["QC_TA"] = "QC_TA"
                else:
                    sel["QC_TA"] = qc_pick

            if st.button("✅ Confirm mapping & start QC"):
                ss.qc_map = sel
                ss.qc_work = ensure_work(ss.qc_src, ss.qc_map)
                if sel["QC_TA"] not in ss.qc_work.columns:
                    ss.qc_work[sel["QC_TA"]] = ""
                ss.qc_idx = 0
                st.success(f"Loaded {len(ss.qc_work)} rows. Headers preserved in exports.")
                st.rerun()

if ss.qc_work.empty:
    st.stop()

# convenience
M = ss.qc_map
row = ss.qc_work.iloc[ss.qc_idx]

def _as_text(x) -> str:
    return "" if pd.isna(x) else str(x)

def _split_opts(s: str):
    """Split options on | or newline. Returns list of 4 strings (padded)."""
    raw = [t.strip() for t in re.split(r"\||\n", _as_text(s)) if t.strip()!=""]
    while len(raw) < 4:
        raw.append("")
    return raw[:4]

# ---------- HEADER (5%) ----------
with st.container():
    st.markdown("<div class='hdr'>", unsafe_allow_html=True)
    left, mid, right = st.columns([2.2,5,3])
    with left:
        st.markdown("<span class='tag'>📝 SME QC Panel</span>", unsafe_allow_html=True)
        st.caption("English ↔ Tamil · single-page QC")
    with mid:
        progress = (ss.qc_idx+1)/len(ss.qc_work)
        st.progress(progress)
        st.caption(f"ID: {_as_text(row[M['ID']])} · Row {ss.qc_idx+1} / {len(ss.qc_work)}")
    with right:
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("◀︎ Prev", use_container_width=True, disabled=ss.qc_idx<=0):
                ss.qc_idx = max(0, ss.qc_idx-1); st.rerun()
        with c2:
            if st.button("Next ▶︎", use_container_width=True, disabled=ss.qc_idx>=len(ss.qc_work)-1):
                ss.qc_idx = min(len(ss.qc_work)-1, ss.qc_idx+1); st.rerun()
        with c3:
            # quick export (enabled once we’ve saved at least once)
            xbytes, cbytes = export_qc(ss.qc_src, ss.qc_work, ss.qc_map)
            base = (ss.uploaded_name or "qc_file").replace(".","_")
            st.download_button("⬇️ Excel", data=xbytes,
                file_name=f"{base}_qc_verified.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                disabled=(xbytes is None), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- ORIGINALS ZONE (compact, 50% total: EN ~25%, TA ~25%) ----------
en_q  = _as_text(row[M["Q_EN"]])
en_op = _as_text(row[M["OPT_EN"]])
en_ans= _as_text(row[M["ANS_EN"]])
en_ex = _as_text(row[M["EXP_EN"]])

ta_q0  = _as_text(row[M["Q_TA"]])
ta_op0 = _as_text(row[M["OPT_TA"]])
ta_ans0= _as_text(row[M["ANS_TA"]])
ta_ex0 = _as_text(row[M["EXP_TA"]])

en_block = f"{en_q}\n\nOptions (A–D):\n{en_op}\n\nAnswer: {en_ans}\n\nExplanation:\n{en_ex}"
ta_block = f"{ta_q0}\n\nவிருப்பங்கள் (A–D):\n{ta_op0}\n\nபதில்: {ta_ans0}\n\nவிளக்கம்:\n{ta_ex0}"

st.markdown("<div class='panel en'><div class='label'>English Version / ஆங்கில பதிப்பு</div>"
            f"<div class='mono scroll'>{en_block}</div></div>", unsafe_allow_html=True)
st.markdown("<div class='panel ta'><div class='label'>Tamil Original / தமிழ் மூலப் பதிப்பு</div>"
            f"<div class='mono scroll'>{ta_block}</div></div>", unsafe_allow_html=True)

# ---------- EDIT CONSOLE (50%) ----------
# Prefill from Tamil original on first visit of a row
row_key = f"prefill_done_{ss.qc_idx}"
if row_key not in ss:
    ss[row_key] = True
    ss.edit_q  = ta_q0
    A,B,C,D = _split_opts(ta_op0)
    ss.edit_A, ss.edit_B, ss.edit_C, ss.edit_D = A,B,C,D
    ss.edit_ans = ta_ans0 if ta_ans0 else A  # default to A if empty
    ss.edit_ex  = ta_ex0

st.markdown("<div class='panel edit'><div class='label'>SME Edit Console / ஆசிரியர் திருத்தம்</div>", unsafe_allow_html=True)

# Question
ss.edit_q = st.text_area("கேள்வி / Key value (TA)", value=ss.get("edit_q",""), height=90)

# Options: A,B on top; C,D bottom
colwrap1, colwrap2 = st.columns(1)
with colwrap1:
    ab1, ab2 = st.columns(2)
    with ab1:
        ss.edit_A = st.text_input("விருப்பம் A", value=ss.get("edit_A",""))
    with ab2:
        ss.edit_B = st.text_input("விருப்பம் B", value=ss.get("edit_B",""))
with colwrap2:
    cd1, cd2 = st.columns(2)
    with cd1:
        ss.edit_C = st.text_input("விருப்பம் C", value=ss.get("edit_C",""))
    with cd2:
        ss.edit_D = st.text_input("விருப்பம் D", value=ss.get("edit_D",""))

# Answer + Explanation
ss.edit_ans = st.text_input("பதில் (A/B/C/D அல்லது உரை)", value=ss.get("edit_ans",""))
ss.edit_ex  = st.text_area("விளக்கம்", value=ss.get("edit_ex",""), height=140)

# Compose QC text to save back
def compose_qc_text(q, A,B,C,D, ans, ex):
    opts_line = f"A) {A} | B) {B} | C) {C} | D) {D}".strip()
    return f"{q}\n\nவிருப்பங்கள் (A–D):\n{opts_line}\n\nபதில்: {ans}\n\nவிளக்கம்:\n{ex}".strip()

qc_text_live = compose_qc_text(ss.edit_q, ss.edit_A, ss.edit_B, ss.edit_C, ss.edit_D, ss.edit_ans, ss.edit_ex)

# Buttons
b1, b2, b3 = st.columns([1.2,1.4,2.5])
with b1:
    if st.button("💾 Save this row", use_container_width=True):
        ss.qc_work.at[ss.qc_idx, M["QC_TA"]] = qc_text_live
        st.success("Saved to QC column.")
with b2:
    if st.button("💾 Save & Next ▶︎", use_container_width=True):
        ss.qc_work.at[ss.qc_idx, M["QC_TA"]] = qc_text_live
        if ss.qc_idx < len(ss.qc_work)-1:
            ss.qc_idx += 1
        st.success("Saved. Moving to next row…")
        st.rerun()
with b3:
    st.markdown("<div class='tip'>Tip: Fill A–D separately; ‘Save & Next’ writes to QC column and advances.</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------- END ----------
