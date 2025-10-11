# pages/03_Email_QC_Panel.py
# FINAL — SME version only (no upload, no validation, admin preloads data)

import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SME QC Panel", page_icon="📝", layout="wide")
ss = st.session_state

# --- Required columns the admin must have preloaded ---
COLS = [
    "ID",
    "Question (English)",
    "Options (English)",
    "Answer (English)",
    "Explanation (English)",
    "Question (Tamil)",
    "Options (Tamil)",
    "Answer (Tamil)",
    "Explanation (Tamil)",
    "QC_TA"
]

# --- Helper functions ---
def _txt(x):
    if pd.isna(x): return ""
    return str(x).replace("\r\n","\n").strip()

def split_opts(txt):
    t = _txt(txt)
    if not t: return ["","","",""]
    parts = re.split(r"\s*[|•;]\s*", t)
    parts = [p.strip() for p in parts if p.strip()]
    while len(parts) < 4: parts.append("")
    return parts[:4]

def build_ta(q,a,b,c,d,ans,exp):
    out=[]
    if q: out.append(f"கேள்வி: {q}")
    opts=[a,b,c,d]; lbl=["A","B","C","D"]
    op=" | ".join([f"{lbl[i]}) {opts[i]}" for i in range(4) if opts[i]])
    if op: out.append(f"விருப்பங்கள் (A–D): {op}")
    if ans: out.append(f"பதில்: {ans}")
    if exp: out.append(f"விளக்கம்: {exp}")
    return "\n\n".join(out)

# --- If no data, tell SME politely ---
if "qc_src" not in ss or ss.qc_src.empty:
    st.title("📝 SME QC Panel")
    st.warning("Data not loaded. Admin will provide bilingual file for your review.")
    st.stop()

# --- Create working copy if not present ---
if "qc_work" not in ss or ss.qc_work.empty:
    ss.qc_work = ss.qc_src.copy()

row = ss.qc_work.iloc[ss.qc_idx]
rid = row["ID"]

# --- Header bar ---
c1,c2,c3 = st.columns([2,4,2])
with c1:
    st.markdown("### 📝 SME QC Panel")
with c2:
    st.caption(f"Row {ss.qc_idx+1} of {len(ss.qc_work)} | ID: {rid}")
    st.progress((ss.qc_idx+1)/len(ss.qc_work))
with c3:
    p,n = st.columns(2)
    with p:
        if st.button("◀ Prev", use_container_width=True, disabled=ss.qc_idx<=0):
            ss.qc_idx -= 1; st.rerun()
    with n:
        if st.button("Next ▶", use_container_width=True, disabled=ss.qc_idx>=len(ss.qc_work)-1):
            ss.qc_idx += 1; st.rerun()

st.divider()

# --- English + Tamil reference panels ---
def ref_block(title, body, color):
    st.markdown(
        f"<div style='border-radius:10px;padding:10px;margin:5px 0;background:{color};'>"
        f"<b>{title}</b><br><br>{body}</div>", unsafe_allow_html=True)

def render_en(q,o,a,e):
    return f"<b>Q:</b> {q}<br><b>Options:</b> {o}<br><b>Answer:</b> {a}<br><b>Explanation:</b> {e}"

def render_ta(q,o,a,e):
    return f"<b>கேள்வி:</b> {q}<br><b>விருப்பங்கள்:</b> {o}<br><b>பதில்:</b> {a}<br><b>விளக்கம்:</b> {e}"

en_q,en_o,en_a,en_e=[_txt(row[c]) for c in COLS[1:5]]
ta_q,ta_o,ta_a,ta_e=[_txt(row[c]) for c in COLS[5:9]]

ref_block("English Version / ஆங்கிலம்", render_en(en_q,en_o,en_a,en_e), "#eaf2ff")
ref_block("Tamil Original / தமிழ் மூலப் பதிப்பு", render_ta(ta_q,ta_o,ta_a,ta_e), "#eaf7ec")

# --- SME edit console ---
st.markdown("<h4 style='background:#fff4d8;padding:6px;border-radius:6px;'>SME Edit Console / ஆசிரியர் திருத்தம்</h4>", unsafe_allow_html=True)
A,B,C,D=split_opts(ta_o)
qid=f"row{ss.qc_idx}"
if f"q_{qid}" not in ss:
    ss[f"q_{qid}"]=ta_q; ss[f"a_{qid}"]=A; ss[f"b_{qid}"]=B; ss[f"c_{qid}"]=C; ss[f"d_{qid}"]=D
    ss[f"ans_{qid}"]=ta_a; ss[f"exp_{qid}"]=ta_e

q=st.text_area("கேள்வி / Question (TA)",ss[f"q_{qid}"],key=f"q_{qid}_in",height=90)
c1,c2=st.columns(2)
with c1:
    A=st.text_input("A",ss[f"a_{qid}"],key=f"a_{qid}_in")
    C=st.text_input("C",ss[f"c_{qid}"],key=f"c_{qid}_in")
with c2:
    B=st.text_input("B",ss[f"b_{qid}"],key=f"b_{qid}_in")
    D=st.text_input("D",ss[f"d_{qid}"],key=f"d_{qid}_in")
ans=st.text_input("பதில் / Answer",ss[f"ans_{qid}"],key=f"ans_{qid}_in")
exp=st.text_area("விளக்கம் / Explanation",ss[f"exp_{qid}"],key=f"exp_{qid}_in",height=120)

# --- Live Preview ---
preview=build_ta(q,A,B,C,D,ans,exp)
st.markdown(f"<div style='background:#fffbe6;border:1px solid #ffe58f;border-radius:8px;padding:10px;margin:5px 0;'>"
            f"<b>Live Preview / நேரடி முன்னோட்டம்</b><br><br>{preview}</div>",unsafe_allow_html=True)

# --- Save buttons ---
c1,c2=st.columns([1,2])
with c1:
    if st.button("💾 Save this row", use_container_width=True):
        ss.qc_work.at[ss.qc_idx,"QC_TA"]=preview
        st.success("Saved successfully.")
with c2:
    if st.button("💾 Save & Next ▶", use_container_width=True,disabled=ss.qc_idx>=len(ss.qc_work)-1):
        ss.qc_work.at[ss.qc_idx,"QC_TA"]=preview
        ss.qc_idx+=1
        st.rerun()

st.caption("✅ Teachers only review translation and edit Tamil content. Admin manages files and validation.")
