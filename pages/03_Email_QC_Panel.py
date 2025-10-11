# pages/03_Email_QC_Panel.py
import streamlit as st
import pandas as pd

from lib import (
    apply_theme, read_bilingual, export_qc,
    render_matches, sort_glossary,
    auto_guess_map, ensure_work, step_columns
)

st.set_page_config(page_title="SME QC Panel", page_icon="📝", layout="wide")
st.title("📝 SME QC Panel")

# ---------- Session -----------
ss = st.session_state
if "night" not in ss: ss.night = False
if "hide_sidebar" not in ss: ss.hide_sidebar = False
if "qc_src" not in ss: ss.qc_src = pd.DataFrame()
if "qc_map" not in ss: ss.qc_map = {}
if "qc_work" not in ss: ss.qc_work = pd.DataFrame()
if "qc_idx" not in ss: ss.qc_idx = 0
if "qc_step" not in ss: ss.qc_step = "Question"
if "full_view" not in ss: ss.full_view = False
if "glossary" not in ss: ss.glossary = []
if "vocab_query" not in ss: ss.vocab_query = ""
if "uploaded_name" not in ss: ss.uploaded_name = None

# ---------- Theme -----------
hdr_left, hdr_mid, hdr_right = st.columns([2,4,2])
with hdr_left:
    st.caption("iPad-friendly layout · preserves headers")
with hdr_right:
    c1, c2 = st.columns(2)
    with c1:
        ss.night = st.toggle("🌙 Night", value=ss.night)
    with c2:
        ss.hide_sidebar = st.toggle("🧼 Clean view", value=ss.hide_sidebar, help="Hide left app menu for full-width view")

apply_theme(ss.night, hide_sidebar=ss.hide_sidebar)

# ---------- Upload & map ----------
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
                ss.qc_map = sel
                ss.qc_work = ensure_work(ss.qc_src, ss.qc_map)
                ss.qc_idx = 0
                st.success(f"Loaded {len(ss.qc_work)} rows. Headers will be preserved in exports.")
                st.rerun()

if ss.qc_work.empty:
    st.stop()

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

# view mode
mode_left, mode_right = st.columns([3,1])
with mode_left:
    ss.full_view = st.toggle("🗔 Full view (show all blocks)", value=ss.full_view, help="Turn OFF to use step-by-step mode")
with mode_right:
    if not ss.full_view:
        st.caption("Step")
        ss.qc_step = st.radio("", ["Question","Options","Answer","Explanation"], horizontal=True, label_visibility="collapsed")

# step columns
cols_map = step_columns(ss.qc_step)

# ---------- Vocabulary panel ----------
g_html = render_matches(ss.glossary, ss.vocab_query)
st.markdown(f"<div class='box gloss'><h4>Vocabulary / சொற்க்களஞ்சியம்</h4><div class='fine'>{g_html}</div></div>", unsafe_allow_html=True)

with st.expander("➕ Add to glossary"):
    ven = st.text_input("English")
    vta = st.text_input("Tamil")
    addcol1, addcol2 = st.columns([1,3])
    with addcol1:
        if st.button("➕ Add term"):
            if ven.strip() and vta.strip():
                ss.glossary.append({"en": ven.strip(), "ta": vta.strip()})
                ss.vocab_query = ven.strip()
                st.success("Added.")
            else:
                st.warning("Enter both English and Tamil.")
    with addcol2:
        ss.vocab_query = st.text_input("🔎 Quick search", value=ss.vocab_query, label_visibility="hidden")

def _panel(title, color_class, html):
    st.markdown(f"<div class='box {color_class}'><h4>{title}</h4><div class='mono'>{html}</div></div>", unsafe_allow_html=True)

def _clean(s: str) -> str:
    return (s or "").replace("\r\n","\n").replace("\n","<br>")

# ---------- Content blocks ----------
if ss.full_view or ss.qc_step=="Question":
    _panel("English Version / ஆங்கில பதிப்பு", "en",  _clean(row[cols_map["EN"]]))
    _panel("Tamil Version / தமிழ் பதிப்பு",    "tao", _clean(row[cols_map["TA"]]))
    _panel("SME QC Verified / ஆசிரியரால் தணிக்கை செய்யப்பட்டது", "qc", _clean(row[cols_map["QC"]]))

    st.markdown("<div class='box edit'><h4>For SME QC Check / ஆசிரியர் தணிக்கை செய்திட</h4></div>", unsafe_allow_html=True)
    edited_text = st.text_area("Edit (Tamil)", value=str(row[cols_map["QC"]] or ""), height=170, key=f"edit_{ss.qc_idx}_{cols_map['QC']}")
    vf = st.text_input("🔎 Vocabulary feeder (paste/type English word)", value=ss.vocab_query)
    if vf.strip(): ss.vocab_query = vf.strip()
    b1,b2,b3 = st.columns([1.4,1.4,3])
    with b1:
        if st.button("💾 Save this step", use_container_width=True):
            ss.qc_work.at[ss.qc_idx, cols_map["QC"]] = edited_text
            st.success("Saved. Red panel updated.")
    with b2:
        if st.button("💾 Save & Next ▶️", use_container_width=True):
            ss.qc_work.at[ss.qc_idx, cols_map["QC"]] = edited_text
            if ss.qc_idx < len(ss.qc_work)-1:
                ss.qc_idx += 1
            st.success("Saved. Moving to next row…")
            st.rerun()
    with b3:
        st.markdown("<div class='tip'>Tip: ‘Save & Next’ to move quickly. The red block (QC Verified) shows your latest saved text.</div>", unsafe_allow_html=True)

else:
    # step view: show only the selected slice
    _panel("English Version / ஆங்கில பதிப்பு", "en",  _clean(row[cols_map["EN"]]))
    _panel("Tamil Version / தமிழ் பதிப்பு",    "tao", _clean(row[cols_map["TA"]]))
    _panel("SME QC Verified / ஆசிரியரால் தணிக்கை செய்யப்பட்டது", "qc", _clean(row[cols_map["QC"]]))

    st.markdown("<div class='box edit'><h4>For SME QC Check / ஆசிரியர் தணிக்கை செய்திட</h4></div>", unsafe_allow_html=True)
    edited_text = st.text_area("Edit (Tamil)", value=str(row[cols_map["QC"]] or ""), height=170, key=f"edit_{ss.qc_idx}_{cols_map['QC']}")
    vf = st.text_input("🔎 Vocabulary feeder (paste/type English word)", value=ss.vocab_query)
    if vf.strip(): ss.vocab_query = vf.strip()
    b1,b2,b3 = st.columns([1.4,1.4,3])
    with b1:
        if st.button("💾 Save this step", use_container_width=True):
            ss.qc_work.at[ss.qc_idx, cols_map["QC"]] = edited_text
            st.success("Saved. Red panel updated.")
    with b2:
        if st.button("💾 Save & Next ▶️", use_container_width=True):
            ss.qc_work.at[ss.qc_idx, cols_map["QC"]] = edited_text
            if ss.qc_idx < len(ss.qc_work)-1:
                ss.qc_idx += 1
            st.success("Saved. Moving to next row…")
            st.rerun()
    with b3:
        st.markdown("<div class='tip'>Tip: ‘Save & Next’ to move quickly. The red block (QC Verified) shows your latest saved text.</div>", unsafe_allow_html=True)

# ---------- Export ----------
st.divider()
st.subheader("⬇️ Export")

xlsx_bytes, csv_bytes = export_qc(ss.qc_src, ss.qc_work, ss.qc_map)
base = (ss.uploaded_name or "qc_file").replace(".","_")
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
