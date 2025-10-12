# pages/03_Email_QC_Panel.py
# SME QC Panel – integrated version with top admin strip & compact layout

import streamlit as st
import pandas as pd
import io

from lib.header_bar import render_header
from lib.ux_mobile import enable_ipad_keyboard_aid, glossary_drawer
from lib.admin_uploader import render_admin_loader

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="SME QC Panel",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------- TOP HEADER ----------
render_header(top_height_vh=5)
enable_ipad_keyboard_aid()

# ---------- ADMIN UPLOAD STRIP ----------
render_admin_loader()

# Stop if no file loaded
ss = st.session_state
if "qc_work" not in ss or ss.qc_work.empty:
    st.stop()

# ---------- CSS for compact layout ----------
st.markdown("""
<style>
/* Hide Streamlit chrome */
[data-testid="stSidebar"] {display:none;}
header, footer, .stAppToolbar {visibility:hidden;height:0;}

/* Tighten padding */
main .block-container {padding: 4px 8px !important;}
.element-container {margin-bottom:4px !important;}

/* Card visuals for English / Tamil */
.qblock {background:#edf3fe;border:1px solid #d0dfff;border-radius:10px;padding:10px;}
.tblock {background:#f1f8f1;border:1px solid #d6eed6;border-radius:10px;padding:10px;}
h4 {margin-bottom:6px;font-weight:600;}
.sme-console {margin-top:10px;background:#fdfdfd;border:1px solid #ddd;border-radius:10px;padding:10px;}
.btnrow {display:flex;justify-content:center;gap:20px;margin-top:6px;}
</style>
""", unsafe_allow_html=True)

# ---------- DISPLAY CURRENT ROW ----------
row_idx = ss.qc_idx
row = ss.qc_work.iloc[row_idx]

st.markdown(f"**English ⇄ Tamil — Row {row_idx+1}/{len(ss.qc_work)}**")

# ---------- ENGLISH PANEL ----------
with st.container():
    st.markdown('<div class="qblock">', unsafe_allow_html=True)
    st.markdown("**English Version / ஆங்கிலம்**")
    st.markdown(f"**Q:** {row['Question (English)']}")
    st.markdown(f"**Options (A–D):** {row['Options (English)']}")
    st.markdown(f"**Answer:** {row['Answer (English)']}")
    st.markdown(f"**Explanation:** {row['Explanation (English)']}")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- TAMIL PANEL ----------
with st.container():
    st.markdown('<div class="tblock">', unsafe_allow_html=True)
    st.markdown("**Tamil Original / தமிழ் மூலப் பதிப்பு**")
    st.markdown(f"**Q:** {row['Question (Tamil)']}")
    st.markdown(f"**Options (A–D):** {row['Options (Tamil)']}")
    st.markdown(f"**Answer:** {row['Answer (Tamil)']}")
    st.markdown(f"**Explanation:** {row['Explanation (Tamil)']}")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- SME EDIT CONSOLE ----------
st.markdown('<div class="sme-console">', unsafe_allow_html=True)
st.markdown("### SME Edit Console / ஆசிரியர் திருத்தம்")

q_edit = st.text_area("Question", value=row['Question (Tamil)'], height=80)
opt_edit = st.text_area("Options", value=row['Options (Tamil)'], height=60)
ans_edit = st.text_input("Answer", value=row['Answer (Tamil)'])
exp_edit = st.text_area("Explanation", value=row['Explanation (Tamil)'], height=100)

# ---------- BOTTOM BUTTONS ----------
st.markdown('<div class="btnrow">', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("💾 Save"):
        ss.qc_work.at[row_idx, 'Question (Tamil)'] = q_edit
        ss.qc_work.at[row_idx, 'Options (Tamil)'] = opt_edit
        ss.qc_work.at[row_idx, 'Answer (Tamil)'] = ans_edit
        ss.qc_work.at[row_idx, 'Explanation (Tamil)'] = exp_edit
        st.toast("Saved ✅")
with col2:
    if st.button("✅ Mark Complete"):
        ss.qc_work.at[row_idx, 'QC_TA'] = "✅"
        st.toast("Marked complete")
with col3:
    if st.button("➡ Save & Next"):
        ss.qc_work.at[row_idx, 'Question (Tamil)'] = q_edit
        ss.qc_work.at[row_idx, 'Options (Tamil)'] = opt_edit
        ss.qc_work.at[row_idx, 'Answer (Tamil)'] = ans_edit
        ss.qc_work.at[row_idx, 'Explanation (Tamil)'] = exp_edit
        ss.qc_work.at[row_idx, 'QC_TA'] = "✅"
        if row_idx < len(ss.qc_work) - 1:
            ss.qc_idx += 1
        st.rerun()
st.markdown('</div></div>', unsafe_allow_html=True)

# ---------- GLOSSARY DRAWER ----------
glossary_drawer()
