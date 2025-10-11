# pages/03_Email_QC_Panel.py
# Final Compact SME QC Panel (English ↔ Tamil)
# Version: Streamlit Compact Panel Layout for iPad — Oct 2025

import re
import pandas as pd
import streamlit as st
from lib import apply_theme, read_bilingual, export_qc, auto_guess_map, ensure_work

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="SME QC Panel", page_icon="📝", layout="wide")

# ---------------- CSS STYLING ----------------
st.markdown("""
<style>
section.main > div {padding-top: 0.4rem;}
.block {padding:10px 12px;margin:6px 0;border-radius:10px;border:1.5px solid var(--secondary-background-color);}
.block.en {background:rgba(66,133,244,.08);border-color:rgba(66,133,244,.35);}
.block.ta {background:rgba(52,168,83,.10);border-color:rgba(52,168,83,.35);}
.block.qc {background:rgba(244,180,0,.10);border-color:rgba(244,180,0,.35);}
.block.saved {background:rgba(234,67,53,.08);border-color:rgba(234,67,53,.35);}
.block h5 {margin:0 0 6px 0;font-size:0.95rem;}
.rowline {margin:4px 0;}
.smallcap {opacity:.7;font-size:.85rem;margin-bottom:4px}
.stTextArea textarea {line-height:1.4;}
.stTextInput > div > div > input {height:38px;}
.element-container {margin-bottom:8px;}
.topbar {display:flex;align-items:center;gap:.6rem;margin:4px 0 6px 0;}
.topbar .grow {flex:1;}
.idtag {font-weight:600;padding:4px 8px;border-radius:6px;background:var(--secondary-background-color);}
.progresswrap {display:flex;align-items:center;gap:.6rem;}
.tip {font-size:.85rem;opacity:.75;margin-top:.35rem}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION SETUP ----------------
ss = st.session_state
if "night" not in ss: ss.night = False
if "qc_src" not in ss: ss.qc_src = pd.DataFrame()
if "qc_map" not in ss: ss.qc_map = {}
if "qc_work" not in ss: ss.qc_work = pd.DataFrame()
if "qc_idx" not in ss: ss.qc_idx = 0
if "uploaded_name" not in ss: ss.uploaded_name = None
if "show_loader" not in ss: ss.show_loader = True

apply_theme(ss.night, hide_sidebar=True)

# ---------------- HELPERS ----------------
def _txt(s): 
    s = "" if s is None else str(s)
    return s.replace("\r\n","\n").replace("\r","\n").strip()

def split_options(text):
    t = _txt(text)
    parts = re.split(r"\s*\|\s*|\s*[;]\s*|\s*[।]\s*\|\s*|\s*⑴|⑵|⑶|⑷", t)
    parts = [p for p in parts if p.strip()]
    if len(parts) >= 4:
        return dict(zip(list("ABCD"), [p.strip(" .:)") for p in parts[:4]]))
    chunks = re.split(r"(?:^| )A\)[\s:]*| B\)[\s:]*| C\)[\s:]*| D\)[\s:]*", t)
    chunks = [c for c in chunks if c and c.strip()]
    if len(chunks) >= 4:
        return dict(zip(list("ABCD"), [c.strip() for c in chunks[:4]]))
    fill = {"A":"","B":"","C":"","D":""}
    for i,k in enumerate("ABCD"):
        if i < len(parts): fill[k]=parts[i].strip()
    return fill

def join_options(ABCD):
    return f"A) {ABCD.get('A','')} | B) {ABCD.get('B','')} | C) {ABCD.get('C','')} | D) {ABCD.get('D','')}"

def compose_qc_ta(q,abcd,ans,exp):
    return f"கேள்வி: {_txt(q)}\nவிருப்பங்கள் (A–D): {join_options(abcd)}\nபதில்: {_txt(ans)}\nவிளக்கம்:\n{_txt(exp)}"

# ---------------- FILE LOAD ----------------
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
            c1,c2 = st.columns(2)
            with c1:
                id_col=st.selectbox("ID",cols,index=cols.index(auto["ID"]) if auto["ID"] in cols else 0)
                en_q=st.selectbox("Question (EN)",cols,index=cols.index(auto["Q_EN"]) if auto["Q_EN"] in cols else 0)
                en_opt=st.selectbox("Options (EN)",cols,index=cols.index(auto["OPT_EN"]) if auto["OPT_EN"] in cols else 0)
                en_ans=st.selectbox("Answer (EN)",cols,index=cols.index(auto["ANS_EN"]) if auto["ANS_EN"] in cols else 0)
                en_exp=st.selectbox("Explanation (EN)",cols,index=cols.index(auto["EXP_EN"]) if auto["EXP_EN"] in cols else 0)
            with c2:
                ta_q=st.selectbox("Question (TA)",cols,index=cols.index(auto["Q_TA"]) if auto["Q_TA"] in cols else 0)
                ta_opt=st.selectbox("Options (TA)",cols,index=cols.index(auto["OPT_TA"]) if auto["OPT_TA"] in cols else 0)
                ta_ans=st.selectbox("Answer (TA)",cols,index=cols.index(auto["ANS_TA"]) if auto["ANS_TA"] in cols else 0)
                ta_exp=st.selectbox("Explanation (TA)",cols,index=cols.index(auto["EXP_TA"]) if auto["EXP_TA"] in cols else 0)

            if st.button("✅ Confirm mapping & start QC"):
                ss.qc_map = {
                    "ID":id_col,
                    "Q_EN":en_q,"OPT_EN":en_opt,"ANS_EN":en_ans,"EXP_EN":en_exp,
                    "Q_TA":ta_q,"OPT_TA":ta_opt,"ANS_TA":ta_ans,"EXP_TA":ta_exp
                }
                ss.qc_work = ensure_work(ss.qc_src, ss.qc_map)
                ss.qc_idx=0
                ss.show_loader=False
                st.success(f"Loaded {len(ss.qc_work)} rows.")
                st.rerun()

if ss.qc_work.empty: st.stop()
m = ss.qc_map
row = ss.qc_work.iloc[ss.qc_idx]

# ---------------- HEADER (5%) ----------------
st.markdown(f"""
<div class='topbar'>
 <div class='idtag'>🆔 ID: {row[m["ID"]]}</div>
 <div class='grow progresswrap'></div>
</div>
""", unsafe_allow_html=True)
st.progress((ss.qc_idx+1)/len(ss.qc_work))

nav1,nav2,nav3=st.columns([1,6,2])
with nav1:
    if st.button("◀️ Prev",use_container_width=True,disabled=ss.qc_idx<=0):
        ss.qc_idx-=1; st.rerun()
with nav2:
    st.caption(f"English ↔ Tamil | Row {ss.qc_idx+1}/{len(ss.qc_work)}")
with nav3:
    if st.button("Next ▶️",use_container_width=True,disabled=ss.qc_idx>=len(ss.qc_work)-1):
        ss.qc_idx+=1; st.rerun()

# ---------------- DISPLAY PANELS ----------------
en_q=_txt(row[m["Q_EN"]]); en_op=_txt(row[m["OPT_EN"]]); en_ans=_txt(row[m["ANS_EN"]]); en_exp=_txt(row[m["EXP_EN"]])
ta_q0=_txt(row[m["Q_TA"]]); ta_op0=_txt(row[m["OPT_TA"]]); ta_ans0=_txt(row[m["ANS_TA"]]); ta_exp0=_txt(row[m["EXP_TA"]])

st.markdown(f"""
<div class='block en'>
<h5>English Version / ஆங்கிலம்</h5>
<div class='rowline'><b>Q:</b> {en_q}</div>
<div class='rowline'><b>Options:</b> {en_op}</div>
<div class='rowline'><b>Answer:</b> {en_ans}</div>
<div class='rowline'><b>Explanation:</b> {en_exp}</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class='block ta'>
<h5>Tamil Original / தமிழ் மூலப் பதிப்பு</h5>
<div class='rowline'><b>கேள்வி:</b> {ta_q0}</div>
<div class='rowline'><b>விருப்பங்கள் (A–D):</b> {ta_op0}</div>
<div class='rowline'><b>பதில்:</b> {ta_ans0}</div>
<div class='rowline'><b>விளக்கம்:</b> {ta_exp0}</div>
</div>
""", unsafe_allow_html=True)

# ---------------- SME EDIT PANEL ----------------
row_key=f"r{ss.qc_idx}"
if f"init_{row_key}" not in ss:
    opts0=split_options(ta_op0)
    ss[f"q_{row_key}"]=ta_q0
    for k in "ABCD": ss[f"o{k}_{row_key}"]=opts0.get(k,"")
    ss[f"ans_{row_key}"]=ta_ans0
    ss[f"exp_{row_key}"]=ta_exp0
    ss[f"init_{row_key}"]=True

st.markdown("<div class='block qc'><h5>SME Edit Console / ஆசிரியர் திருத்தம்</h5>",unsafe_allow_html=True)
q_val=st.text_area("கேள்வி",value=ss[f"q_{row_key}"],key=f"qedit_{row_key}",height=80)
oa,ob=st.columns(2)
with oa: a_val=st.text_input("A",value=ss[f"oA_{row_key}"],key=f"oa_{row_key}")
with ob: b_val=st.text_input("B",value=ss[f"oB_{row_key}"],key=f"ob_{row_key}")
oc,od=st.columns(2)
with oc: c_val=st.text_input("C",value=ss[f"oC_{row_key}"],key=f"oc_{row_key}")
with od: d_val=st.text_input("D",value=ss[f"oD_{row_key}"],key=f"od_{row_key}")
ans_val=st.text_input("பதில்",value=ss[f"ans_{row_key}"],key=f"ans_{row_key}")
exp_val=st.text_area("விளக்கம்",value=ss[f"exp_{row_key}"],key=f"exp_{row_key}",height=140)

# Live preview (Yellow)
live_html=compose_qc_ta(q_val,{"A":a_val,"B":b_val,"C":c_val,"D":d_val},ans_val,exp_val).replace("\n","<br>")
st.markdown(f"<div class='block qc'><b>Live Preview / ஆசிரியர் QC முன்னோட்டம்</b><br>{live_html}</div>",unsafe_allow_html=True)

# Last saved (Red)
qc_col="QC_TA"
if qc_col not in ss.qc_work.columns:
    ss.qc_work[qc_col]=""
saved_txt=_txt(row.get(qc_col,""))
if saved_txt:
    st.markdown(f"<div class='block saved'><b>Last Saved QC / சேமிக்கப்பட்ட QC</b><br>{saved_txt.replace(chr(10),'<br>')}</div>",unsafe_allow_html=True)

# Save controls
s1,s2,s3=st.columns([1.2,1.2,4])
with s1:
    if st.button("💾 Save Row",use_container_width=True):
        final_text=compose_qc_ta(q_val,{"A":a_val,"B":b_val,"C":c_val,"D":d_val},ans_val,exp_val)
        ss.qc_work.at[ss.qc_idx,qc_col]=final_text
        st.success("Saved successfully.")
with s2:
    if st.button("💾 Save & Next ▶️",use_container_width=True):
        final_text=compose_qc_ta(q_val,{"A":a_val,"B":b_val,"C":c_val,"D":d_val},ans_val,exp_val)
        ss.qc_work.at[ss.qc_idx,qc_col]=final_text
        if ss.qc_idx < len(ss.qc_work)-1:
            ss.qc_idx+=1
        st.rerun()
with s3:
    st.markdown("<div class='tip'>Tip: Yellow shows your live edits, Red shows last saved text.</div>",unsafe_allow_html=True)

# ---------------- EXPORT ----------------
st.subheader("⬇️ Export QC Files")
xlsx_bytes,csv_bytes=export_qc(ss.qc_src,ss.qc_work,ss.qc_map)
base=(ss.uploaded_name or "qc_file").replace(".","_")
st.download_button("Download QC Excel (.xlsx)",data=xlsx_bytes,file_name=f"{base}_qc_verified.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",disabled=not xlsx_bytes)
st.download_button("Download QC CSV (.csv)",data=csv_bytes,file_name=f"{base}_qc_verified.csv",mime="text/csv",disabled=not csv_bytes)
