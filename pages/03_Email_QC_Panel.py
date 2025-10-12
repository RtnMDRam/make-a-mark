# pages/03_Email_QC_Panel.py
import streamlit as st
import pandas as pd
from lib.top_strip import render_top_strip

st.set_page_config(
    page_title="SME QC Panel",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# render top area; stop if no data yet
ready = render_top_strip()
if not ready:
    st.stop()

df: pd.DataFrame = st.session_state.qc_df
idx: int = st.session_state.qc_idx

# ------- Your three main blocks (Editor first, then Tamil, then English) -------
st.markdown("## SME Edit Console / ஆசிரியர் திருத்தம்")

q = df.get("ta_question", [""])[idx] if "ta_question" in df else ""
a = df.get("ta_option_a", [""])[idx] if "ta_option_a" in df else ""
b = df.get("ta_option_b", [""])[idx] if "ta_option_b" in df else ""
c = df.get("ta_option_c", [""])[idx] if "ta_option_c" in df else ""
d = df.get("ta_option_d", [""])[idx] if "ta_option_d" in df else ""
ans = df.get("ta_answer", [""])[idx] if "ta_answer" in df else ""
exp = df.get("ta_explanation", [""])[idx] if "ta_explanation" in df else ""

c1, c2 = st.columns([2, 1.2])
with c1:
    q = st.text_area(" ", q, height=90, label_visibility="collapsed", key="q_ta")
    colA, colB = st.columns(2)
    with colA:
        a = st.text_input("A", a, key="a_ta")
    with colB:
        b = st.text_input("B", b, key="b_ta")
    colC, colD = st.columns(2)
    with colC:
        c = st.text_input("C", c, key="c_ta")
    with colD:
        d = st.text_input("D", d, key="d_ta")
with c2:
    st.text_input("பதில் / Answer", ans, key="ans_ta")
    st.text_area("விளக்கங்கள் :", exp, height=120, key="exp_ta")

st.divider()

# Tamil Original (read-only)
st.markdown("### Tamil Original / தமிழ் மூலப் பதிவு")
ta = df.get("ta_original", [""])[idx] if "ta_original" in df else ""
st.info(ta or "—", icon="📄")

# English Original (read-only)
st.markdown("### English Version / ஆங்கிலம்")
en = df.get("en_original", [""])[idx] if "en_original" in df else ""
st.info(en or "—", icon="📄")
