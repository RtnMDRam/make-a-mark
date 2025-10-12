# pages/03_Email_QC_Panel.py
import streamlit as st
from lib.top_strip import render_top_strip

st.set_page_config(page_title="SME QC Panel", layout="wide")

# minimal CSS (also hides the floating bottom-right control)
st.markdown("""
<style>
[data-testid="stToolbar"], .stAppDeployButton, [data-testid="stDecoration"]{visibility:hidden;height:0;}
footer{visibility:hidden;height:0;}
.block-container{padding-top:6px;padding-bottom:6px;}
/* SME title smaller */
h2, h3 { margin: 6px 0 4px 0; }
div[role="alert"] {display:none;} /* hide Session State banner */
</style>
""", unsafe_allow_html=True)

# ---------- TOP STRIP (10% height) ----------
render_top_strip()

# stop here until we have data
ss = st.session_state
if ("qc_work" not in ss) or (getattr(ss, "qc_work", None) is None) or ss.qc_work.empty:
    st.info("Paste a link or upload a file at the top strip to begin.")
    st.stop()

# ---------- English/Tamil reference blocks ----------
def ref_panel(title, text):
    st.markdown(f"#### {title}")
    st.markdown(f"<div style='background:#e9f2ff;border:1px solid #cbd8ff;border-radius:8px;padding:10px'>{text}</div>",
                unsafe_allow_html=True)

row = ss.qc_work.iloc[ss.qc_idx]
en = [
    f"**Q:** {row['Question (English)']}",
    f"**Options (A–D):** {row['Options (English)']}",
    f"**Answer:** {row['Answer (English)']}",
    f"**Explanation:** {row['Explanation (English)']}",
]
ta = [
    f"**Q:** {row['Question (Tamil)']}",
    f"**Options (A–D):** {row['Options (Tamil)']}",
    f"**Answer:** {row['Answer (Tamil)']}",
    f"**Explanation:** {row['Explanation (Tamil)']}",
]
ref_panel("English Version / ஆங்கிலம்", "<br>".join(en))
ref_panel("Tamil Original / தமிழ் மூலப் பதிப்பு", "<br>".join(ta))

# ---------- SME edit console (compact) ----------
st.markdown("### SME Edit Console / ஆசிரியர் திருத்தம்")

q = st.text_area("", value=row["Question (Tamil)"], label_visibility="collapsed")
c1,c2 = st.columns(2)
with c1:
    a = st.text_input("A", value="")
    c = st.text_input("C", value="")
with c2:
    b = st.text_input("B", value="")
    d = st.text_input("D", value="")

g1,g2 = st.columns([1,1])
with g1:
    gloss = st.text_input("சொல் அகராதி / Glossary", value="", placeholder="(Type the word)")
with g2:
    ans = st.text_input("பதில் / Answer", value=row["Answer (Tamil)"])

exp = st.text_area("விளக்கங்கள் :", value=row["Explanation (Tamil)"], height=140)

# actions (wired to state)
a1,a2,a3 = st.columns([1,1,1])
with a1:
    if st.button("💾 Save"):
        ss.qc_work.at[ss.qc_idx, "Question (Tamil)"] = q
        ss.qc_work.at[ss.qc_idx, "Answer (Tamil)"]   = ans
        ss.qc_work.at[ss.qc_idx, "Explanation (Tamil)"] = exp
        st.success("Saved.", icon="✅")
with a2:
    if st.button("✅ Mark Complete"):
        st.success("Marked complete.", icon="✅")
with a3:
    if st.button("📄 Save & Next"):
        ss.qc_work.at[ss.qc_idx, "Question (Tamil)"] = q
        ss.qc_work.at[ss.qc_idx, "Answer (Tamil)"]   = ans
        ss.qc_work.at[ss.qc_idx, "Explanation (Tamil)"] = exp
        ss.qc_idx = min(ss.qc_idx + 1, len(ss.qc_work)-1)
        st.rerun()
