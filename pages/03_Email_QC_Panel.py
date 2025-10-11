# pages/03_Email_QC_Panel.py
# Single-page SME QC Panel (compact iPad layout)

import io, os, re
import pandas as pd
import streamlit as st

# ----- modular helpers from lib/ -----
from lib import apply_theme, read_bilingual, export_qc, auto_guess_map, ensure_work

st.set_page_config(page_title="SME QC Panel", page_icon="📝", layout="wide")

# ================= Session =================
ss = st.session_state
if "night" not in ss: ss.night = False
if "hide_sidebar" not in ss: ss.hide_sidebar = False
if "qc_src" not in ss: ss.qc_src = pd.DataFrame()
if "qc_map" not in ss: ss.qc_map = {}
if "qc_work" not in ss: ss.qc_work = pd.DataFrame()
if "qc_idx" not in ss: ss.qc_idx = 0
if "uploaded_name" not in ss: ss.uploaded_name = None
if "edit_cache" not in ss: ss.edit_cache = {}

# ================= Styles =================
st.markdown("""
<style>
.block-container { padding-top: 0.6rem; padding-bottom: 0.6rem; }
.box { border-radius: 10px; padding: .6rem .9rem .7rem .9rem; margin: .5rem 0 0.6rem 0; border: 2px solid rgba(0,0,0,.12);}
.box h4 { margin: 0 0 .35rem 0; font-size: .96rem; letter-spacing:.2px;}
.box .mono { white-space: pre-wrap; line-height: 1.45; }
.box.en  { background: #eaf3ff; border-color:#9cc6ff;}
.box.ta0 { background: #e8f7ea; border-color:#8ad199;}
.box.prev { background:#fff7da; border-color:#f1cf59;}
.idtag{display:inline-block;background:#111;color:#fff;border-radius:8px;padding:.25rem .55rem;font-size:.78rem;}
.kabs{font-size:.78rem; opacity:.8;}
hr{margin:.35rem 0 .35rem 0;}
.smallgap{height:.25rem;}
.compact label p{margin-bottom:0}
.sublabel{font-size:.85rem; opacity:.8; margin-bottom:.2rem;}
.togwrap{margin: .2rem 0 .6rem 0; display:flex; gap:1rem; align-items:center;}
[data-baseweb="input"]{margin:0}
</style>
""", unsafe_allow_html=True)

# ================ File load & mapping (tiny) =================
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
            cols = list(src.columns)
            st.caption("Map the required columns (kept as-is on export):")
            c1, c2 = st.columns(2)
            with c1:
                id_col   = st.selectbox("ID", cols, index=cols.index(auto["ID"]) if auto["ID"] in cols else 0)
                q_en     = st.selectbox("Question (EN)", cols, index=cols.index(auto["Q_EN"]) if auto["Q_EN"] in cols else 0)
                op_en    = st.selectbox("Options (EN)",  cols, index=cols.index(auto["OPT_EN"]) if auto["OPT_EN"] in cols else 0)
                ans_en   = st.selectbox("Answer (EN)",   cols, index=cols.index(auto["ANS_EN"]) if auto["ANS_EN"] in cols else 0)
                exp_en   = st.selectbox("Explanation (EN)", cols, index=cols.index(auto["EXP_EN"]) if auto["EXP_EN"] in cols else 0)
            with c2:
                q_ta     = st.selectbox("Question (TA)", cols, index=cols.index(auto["Q_TA"]) if auto["Q_TA"] in cols else 0)
                op_ta    = st.selectbox("Options (TA)",  cols, index=cols.index(auto["OPT_TA"]) if auto["OPT_TA"] in cols else 0)
                ans_ta   = st.selectbox("Answer (TA)",   cols, index=cols.index(auto["ANS_TA"]) if auto["ANS_TA"] in cols else 0)
                exp_ta   = st.selectbox("Explanation (TA)", cols, index=cols.index(auto["EXP_TA"]) if auto["EXP_TA"] in cols else 0)

            if st.button("✅ Confirm mapping & start"):
                ss.qc_map = dict(ID=id_col, Q_EN=q_en, OPT_EN=op_en, ANS_EN=ans_en, EXP_EN=exp_en,
                                 Q_TA=q_ta, OPT_TA=op_ta, ANS_TA=ans_ta, EXP_TA=exp_ta)
                work = ensure_work(ss.qc_src, ss.qc_map).copy()
                if "QC_TA" not in work.columns:
                    work["QC_TA"] = ""
                ss.qc_work = work
                ss.qc_idx = 0
                st.success(f"Loaded {len(work)} rows.")
                st.rerun()

# stop if nothing yet
if ss.qc_work.empty:
    st.stop()

# ================ helpers ================
def _txt(x) -> str:
    s = "" if pd.isna(x) else str(x)
    return s.replace("\r\n","\n").strip()

def split_options(raw: str):
    raw = _txt(raw)
    if not raw:
        return "", "", "", ""
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) >= 4:
        A, B, C, D = (re.sub(r"^[A-D]\)?\s*[:．.、)]\s*","",p, flags=re.I) for p in parts[:4])
        return A, B, C, D
    m = re.split(r"\bA\)\s*|\bB\)\s*|\bC\)\s*|\bD\)\s*", raw)
    if len(m) >= 5:
        return m[1].strip(), m[2].strip(), m[3].strip(), m[4].strip()
    return raw, "", "", ""

def compose_qc(q, A, B, C, D, ans, exp):
    return (
        f"கேள்வி: {q}\n"
        f"விருப்பங்கள் (A–D): A) {A} | B) {B} | C) {C} | D) {D}\n"
        f"பதில்: {ans}\n"
        f"விளக்கம்:\n{exp}"
    ).strip()

# current row
m  = ss.qc_map
row = ss.qc_work.iloc[ss.qc_idx]
rid = _txt(row[m["ID"]])

# ================ header (thin) ================
top = st.columns([6,2,2,2])
with top[0]:
    st.markdown(f"### 📝 SME QC Panel  &nbsp;&nbsp;<span class='kabs'>English ⇄ Tamil · Row {ss.qc_idx+1}/{len(ss.qc_work)}</span>", unsafe_allow_html=True)
with top[1]:
    st.markdown(f"<span class='idtag'>ID: {rid}</span>", unsafe_allow_html=True)
with top[2]:
    if st.button("◀️ Prev", use_container_width=True, disabled=ss.qc_idx==0):
        ss.qc_idx = max(0, ss.qc_idx-1); st.rerun()
with top[3]:
    if st.button("Next ▶️", use_container_width=True, disabled=ss.qc_idx>=len(ss.qc_work)-1):
        ss.qc_idx = min(len(ss.qc_work)-1, ss.qc_idx+1); st.rerun()

st.progress((ss.qc_idx+1)/len(ss.qc_work))

# ================ English panel (compact) ================
en_q  = _txt(row[m["Q_EN"]])
en_op = _txt(row[m["OPT_EN"]])
en_ans= _txt(row[m["ANS_EN"]])
en_exp= _txt(row[m["EXP_EN"]])

st.markdown("<div class='box en'><h4>English Version / ஆங்கிலம்</h4>"
            f"<div class='mono'><b>Q:</b> {en_q}\n\n"
            f"<b>Options (A–D):</b> {en_op}\n\n"
            f"<b>Answer:</b> {en_ans}\n\n"
            f"<b>Explanation:</b> {en_exp}</div></div>", unsafe_allow_html=True)

# ================ Tamil Original (compact) ================
ta_q  = _txt(row[m["Q_TA"]])
ta_op = _txt(row[m["OPT_TA"]])
ta_ans= _txt(row[m["ANS_TA"]])
ta_exp= _txt(row[m["EXP_TA"]])

st.markdown("<div class='box ta0'><h4>Tamil Original / தமிழ் மூலப் பதிப்பு</h4>"
            f"<div class='mono'><b>கேள்வி:</b> {ta_q}\n\n"
            f"<b>விருப்பங்கள் (A–D):</b> {ta_op}\n\n"
            f"<b>பதில்:</b> {ta_ans}\n\n"
            f"<b>விளக்கம்:</b> {ta_exp}</div></div>", unsafe_allow_html=True)

# ====== toggles BELOW the Tamil panel ======
with st.container():
    st.markdown("<div class='togwrap'>", unsafe_allow_html=True)
    c1, c2 = st.columns([1,1])
    with c1:
        ss.night = st.toggle("🌙 Night mode", value=ss.night)
    with c2:
        ss.hide_sidebar = st.toggle("🧼 Clean view (hide left menu)", value=ss.hide_sidebar)
    st.markdown("</div>", unsafe_allow_html=True)

apply_theme(ss.night, hide_sidebar=ss.hide_sidebar)

# ================ SME Edit Console ================
st.markdown("<div class='box prev'><h4>SME Edit Console / ஆசிரியர் திருத்தம்</h4></div>", unsafe_allow_html=True)

row_key = f"r{ss.qc_idx}"
if row_key not in ss.edit_cache:
    A0,B0,C0,D0 = split_options(ta_op)
    ss.edit_cache[row_key] = dict(q=ta_q, A=A0, B=B0, C=C0, D=D0, ans=ta_ans, exp=ta_exp)
cache = ss.edit_cache[row_key]

q_val = st.text_area("கேள்வி", value=cache["q"], key=f"q_{row_key}", height=90)
cA, cB = st.columns(2)
with cA:
    A_val = st.text_input("A", value=cache["A"], key=f"A_{row_key}")
with cB:
    B_val = st.text_input("B", value=cache["B"], key=f"B_{row_key}")
cC, cD = st.columns(2)
with cC:
    C_val = st.text_input("C", value=cache["C"], key=f"C_{row_key}")
with cD:
    D_val = st.text_input("D", value=cache["D"], key=f"D_{row_key}")
ans_val = st.text_input("பதில்", value=cache["ans"], key=f"ans_{row_key}")
exp_val = st.text_area("விளக்கம்", value=cache["exp"], key=f"exp_{row_key}", height=120)

qc_live = compose_qc(q_val, A_val, B_val, C_val, D_val, ans_val, exp_val)
st.markdown(f"<div class='box prev'><h4>Live Preview / முன்னோட்டம்</h4><div class='mono'>{qc_live}</div></div>", unsafe_allow_html=True)

bL, bR = st.columns([1.2, 1.2])
with bL:
    if st.button("💾 Save this row", use_container_width=True):
        if "QC_TA" not in ss.qc_work.columns:
            ss.qc_work["QC_TA"] = ""
        ss.qc_work.at[ss.qc_idx, "QC_TA"] = qc_live
        ss.edit_cache[row_key] = dict(q=q_val, A=A_val, B=B_val, C=C_val, D=D_val, ans=ans_val, exp=exp_val)
        st.success("Saved ✅ (QC_TA updated)")
with bR:
    if st.button("💾 Save & Next ▶️", use_container_width=True, disabled=ss.qc_idx>=len(ss.qc_work)-1):
        if "QC_TA" not in ss.qc_work.columns:
            ss.qc_work["QC_TA"] = ""
        ss.qc_work.at[ss.qc_idx, "QC_TA"] = qc_live
        ss.edit_cache[row_key] = dict(q=q_val, A=A_val, B=B_val, C=C_val, D=D_val, ans=ans_val, exp=exp_val)
        ss.qc_idx = min(len(ss.qc_work)-1, ss.qc_idx+1)
        st.rerun()

st.divider()

# ================ Export =================
st.markdown("#### ⬇️ Export")
xlsx_bytes, csv_bytes = export_qc(ss.qc_src, ss.qc_work, ss.qc_map)
base = (ss.uploaded_name or "qc_file").replace(".","_")
if xlsx_bytes:
    st.download_button("Download QC Excel (.xlsx)", data=xlsx_bytes,
        file_name=f"{base}_qc_verified.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
if csv_bytes:
    st.download_button("Download QC CSV (.csv)", data=csv_bytes,
        file_name=f"{base}_qc_verified.csv", mime="text/csv")
