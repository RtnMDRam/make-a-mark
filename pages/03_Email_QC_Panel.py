# pages/03_Email_QC_Panel.py
# SME QC panel: Sidebar Glossary + English(RO) + Tamil Original(RO) + QC Verified (saved) + SME Edit (live)
# - Preserves input headers & column order on export
# - iPad-friendly layout, Night Mode, Clean View (hide sidebar), Prev/Next, Save & Export

import streamlit as st
import pandas as pd

# ---- our modular helpers (you already created these in lib/) ----
from lib import (
    apply_theme,            # theme & CSS + clean view
    read_bilingual,         # csv/xlsx -> DataFrame (header row preserved)
    export_qc,              # build xlsx/csv bytes with source headers + QC values
    auto_guess_map,         # guess columns
    ensure_work,            # make working copy & QC_* columns
    step_columns,           # map by step (kept for future, but we show all in yellow)
    render_matches,         # glossary search -> html
    sort_glossary,          # glossary sort
)

st.set_page_config(page_title="SME QC Panel", page_icon="📝", layout="wide")
st.title("📝 SME QC Panel")

# ---------- Session ----------
ss = st.session_state
if "night" not in ss: ss.night = False
if "clean" not in ss: ss.clean = True          # hide sidebar by default for SMEs
if "qc_src" not in ss: ss.qc_src = pd.DataFrame()
if "qc_map" not in ss: ss.qc_map = {}
if "qc_work" not in ss: ss.qc_work = pd.DataFrame()
if "qc_idx" not in ss: ss.qc_idx = 0
if "qc_step" not in ss: ss.qc_step = "Question"
if "glossary" not in ss: ss.glossary = []
if "vocab_query" not in ss: ss.vocab_query = ""
if "uploaded_name" not in ss: ss.uploaded_name = None

# ---------- Small helpers ----------
def _split_opts(s: str):
    """Return a list of 4 option lines from a single text field."""
    lines = [ln.strip() for ln in str(s or "").replace("\r\n","\n").split("\n")]
    lines = [ln for ln in lines if ln]
    while len(lines) < 4:
        lines.append("")
    return lines[:4]

def _join_opts(lines):
    """Join 4 lines into one multiline string for storage."""
    return "\n".join((lines or [])[:4])

def _clean_lines(s: str) -> str:
    return (s or "").replace("\r\n", "\n").replace("\n", "<br>")

def _qc_preview_text(q, opts4, ans, exp):
    parts = []
    if q:    parts.append(str(q))
    if opts4 and any(opts4):
        parts.append("விருப்பங்கள் (A–D):")
        parts.extend([str(x) for x in opts4])
    if ans:  parts.append(f"பதில்: {ans}")
    if exp:  parts.append("விளக்கம்:\n" + str(exp))
    return "\n\n".join(parts)

def _panel(title, color_class, html):
    st.markdown(
        f"<div class='box {color_class}'><h4>{title}</h4><div class='mono'>{html}</div></div>",
        unsafe_allow_html=True
    )

# ---------- Header controls ----------
hdr_left, hdr_mid, hdr_right = st.columns([2,4,2])
with hdr_left:
    st.caption("iPad-friendly layout · preserves headers")
with hdr_right:
    c1, c2 = st.columns(2)
    with c1:
        ss.night = st.toggle("🌙 Night", value=ss.night)
    with c2:
        ss.clean = st.toggle("🧼 Clean view", value=ss.clean, help="Hide left app menu")

# apply theme + hide sidebar if clean
apply_theme(ss.night, hide_sidebar=ss.clean)

# ---------- Upload + map ----------
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
            st.write("**Map the required columns (kept exactly in export):**")
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

            if st.button("✅ Confirm mapping & start QC"):
                ss.qc_map  = sel
                ss.qc_work = ensure_work(ss.qc_src, ss.qc_map)  # creates QC_Q_TA, QC_OPT_TA, QC_ANS_TA, QC_EXP_TA
                ss.qc_idx  = 0
                st.success(f"Loaded {len(ss.qc_work)} rows. Headers will be preserved in exports.")
                st.rerun()

if ss.qc_work.empty:
    st.stop()

# ---------- Sidebar: Vocabulary (collapsible, keeps main page clean) ----------
with st.sidebar:
    st.subheader("🗂️ Vocabulary / சொற்க்களஞ்சியம்")
    # quick search
    ss.vocab_query = st.text_input("🔎 Search English", value=ss.vocab_query)
    st.markdown(render_matches(ss.glossary, ss.vocab_query), unsafe_allow_html=True)
    with st.expander("➕ Add term"):
        ven = st.text_input("English", key="ven_add")
        vta = st.text_input("Tamil",   key="vta_add")
        if st.button("Add to glossary"):
            if ven.strip() and vta.strip():
                ss.glossary.append({"en": ven.strip(), "ta": vta.strip()})
                ss.vocab_query = ven.strip()
                st.success("Added.")
            else:
                st.warning("Enter both English and Tamil.")

# ---------- Navigation ----------
row = ss.qc_work.iloc[ss.qc_idx]
nav1, nav2, nav3, nav4 = st.columns([1,2.4,4,1])
with nav1:
    if st.button("◀️ Prev", use_container_width=True, disabled=ss.qc_idx<=0):
        ss.qc_idx = max(0, ss.qc_idx-1); st.rerun()
with nav2:
    rid = row["ID"]
    st.markdown(f"<div class='idtag'>ID: {rid}</div>", unsafe_allow_html=True)
with nav3:
    st.progress((ss.qc_idx+1)/len(ss.qc_work))
    st.caption(f"Row {ss.qc_idx+1} / {len(ss.qc_work)}")
with nav4:
    if st.button("Next ▶️", use_container_width=True, disabled=ss.qc_idx>=len(ss.qc_work)-1):
        ss.qc_idx = min(len(ss.qc_work)-1, ss.qc_idx+1); st.rerun()

# Keep step mapping for English/Tamil read-only panels (teacher can still switch focus if needed)
ss.qc_step = st.radio("Step", ["Question","Options","Answer","Explanation"],
                      index=["Question","Options","Answer","Explanation"].index(ss.qc_step),
                      horizontal=True)

cols_map = step_columns(ss.qc_step)  # {'EN':..., 'TA':..., 'QC':...} — EN/TA change with step; QC we show full below

# ---------- Read-only panels (English & Tamil Original) ----------
_panel("English Version / ஆங்கில பதிப்பு", "en",  _clean_lines(row[cols_map["EN"]]))
_panel("Tamil Version / தமிழ் பதிப்பு",    "tao", _clean_lines(row[cols_map["TA"]]))

# ---------- SME QC Verified (Red: last saved) + SME Edit (Yellow: live) ----------
# Column keys inside the working df
q_col, opt_col, ans_col, exp_col = "Q_TA", "OPT_TA", "ANS_TA", "EXP_TA"
qc_q, qc_opt, qc_ans, qc_exp     = "QC_Q_TA", "QC_OPT_TA", "QC_ANS_TA", "QC_EXP_TA"

# Current values (prefer saved QC; fall back to Tamil original)
orig_q   = row.get(q_col, "")
orig_opt = row.get(opt_col, "")
orig_ans = row.get(ans_col, "")
orig_exp = row.get(exp_col, "")

saved_q   = row.get(qc_q,   "") or orig_q
saved_opt = row.get(qc_opt, "") or orig_opt
saved_ans = row.get(qc_ans, "") or orig_ans
saved_exp = row.get(qc_exp, "") or orig_exp

# Red: last saved QC
_panel("SME QC Verified / ஆசிரியரால் தணிக்கை செய்யப்பட்டது", "qc",
       _clean_lines(_qc_preview_text(saved_q, _split_opts(saved_opt), saved_ans, saved_exp)))

# Yellow: LIVE editable (Q + A–D + Answer + Explanation)
st.markdown("<div class='box edit'><h4>For SME QC Check / ஆசிரியர் தணிக்கை செய்திட</h4></div>", unsafe_allow_html=True)

optA, optB, optC, optD = _split_opts(saved_opt)
ed_q   = st.text_area("கேள்வி",  value=str(saved_q or ""),  height=100, key=f"ed_q_{ss.qc_idx}")
ed_oA  = st.text_input("விருப்பம் A", value=optA, key=f"ed_oA_{ss.qc_idx}")
ed_oB  = st.text_input("விருப்பம் B", value=optB, key=f"ed_oB_{ss.qc_idx}")
ed_oC  = st.text_input("விருப்பம் C", value=optC, key=f"ed_oC_{ss.qc_idx}")
ed_oD  = st.text_input("விருப்பம் D", value=optD, key=f"ed_oD_{ss.qc_idx}")
ed_ans = st.text_input("பதில்",      value=str(saved_ans or ""), key=f"ed_ans_{ss.qc_idx}")
ed_exp = st.text_area("விளக்கம்", value=str(saved_exp or ""), height=150, key=f"ed_exp_{ss.qc_idx}")

# Yellow live preview (mirrors inputs above)
live_preview = _qc_preview_text(ed_q, [ed_oA, ed_oB, ed_oC, ed_oD], ed_ans, ed_exp)
_panel("For SME QC Check (Live) / ஆசிரியர் தணிக்கை (நேரடி முன்னோட்டம்)", "edit",
       _clean_lines(live_preview))

# Save actions
b1, b2, b3 = st.columns([1.4, 1.4, 3])
with b1:
    if st.button("💾 Save this step", use_container_width=True):
        ss.qc_work.at[ss.qc_idx, qc_q]   = ed_q
        ss.qc_work.at[ss.qc_idx, qc_opt] = _join_opts([ed_oA, ed_oB, ed_oC, ed_oD])
        ss.qc_work.at[ss.qc_idx, qc_ans] = ed_ans
        ss.qc_work.at[ss.qc_idx, qc_exp] = ed_exp
        st.success("Saved. Red panel updated.")
with b2:
    if st.button("💾 Save & Next ▶️", use_container_width=True):
        ss.qc_work.at[ss.qc_idx, qc_q]   = ed_q
        ss.qc_work.at[ss.qc_idx, qc_opt] = _join_opts([ed_oA, ed_oB, ed_oC, ed_oD])
        ss.qc_work.at[ss.qc_idx, qc_ans] = ed_ans
        ss.qc_work.at[ss.qc_idx, qc_exp] = ed_exp
        if ss.qc_idx < len(ss.qc_work) - 1:
            ss.qc_idx += 1
        st.success("Saved. Moving to next row…")
        st.rerun()
with b3:
    st.caption("Tip: ‘Save & Next’ to move quickly. Red shows last saved; Yellow shows your live edits.")

# ---------- Export ----------
st.divider()
st.subheader("⬇️ Export")
xlsx_bytes, csv_bytes = export_qc(ss.qc_src, ss.qc_work, ss.qc_map)
base = (ss.uploaded_name or "qc_file").replace(".", "_")
if xlsx_bytes and csv_bytes:
    st.download_button("Download QC Excel (.xlsx)", data=xlsx_bytes,
        file_name=f"{base}_qc_verified.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.download_button("Download QC CSV (.csv)", data=csv_bytes,
        file_name=f"{base}_qc_verified.csv", mime="text/csv")
if st.button("✅ Work complete — Save QC file"):
    if not xlsx_bytes:
        st.error("Nothing to export yet.")
    else:
        st.success("QC file prepared. Use the buttons above to download now.")
