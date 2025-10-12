import streamlit as st
import pandas as pd
from lib.top_strip import render_top_strip

st.set_page_config(page_title="SME QC Panel", layout="wide")

ready = render_top_strip()

# If dataset is ready, show Editor (top), then Tamil, then English
if ready:
    df: pd.DataFrame = st.session_state.qc_df
    idx = st.session_state.get("qc_idx", 0)
    row = df.iloc[idx] if len(df) > 0 else {}

    # Pull safe values (handle missing columns gracefully)
    q_ta = str(row.get("q_ta", "") or "")
    a_ta = str(row.get("a_ta", "") or "")
    b_ta = str(row.get("b_ta", "") or "")
    c_ta = str(row.get("c_ta", "") or "")
    d_ta = str(row.get("d_ta", "") or "")
    ans_ta = str(row.get("ans_ta", "") or "")
    expl_ta = str(row.get("expl_ta", "") or "")

    q_en = str(row.get("q_en", "") or "")
    a_en = str(row.get("a_en", "") or "")
    b_en = str(row.get("b_en", "") or "")
    c_en = str(row.get("c_en", "") or "")
    d_en = str(row.get("d_en", "") or "")
    ans_en = str(row.get("ans_en", "") or "")
    expl_en = str(row.get("expl_en", "") or "")

    st.markdown("### SME Edit Console / ஆசிரியர் திருத்தம்")

    # Question + Answer row
    colQ, colAns = st.columns([2,1])
    with colQ:
        q_ta = st.text_area("", value=q_ta, key=f"q_ta_{idx}", height=90, label_visibility="collapsed")
    with colAns:
        ans_ta = st.text_input("பதில் / Answer", value=ans_ta, key=f"ans_ta_{idx}")

    # A-B-C-D in one row
    A, B = st.columns(2)
    with A:
        a_ta = st.text_input("A", value=a_ta, key=f"a_ta_{idx}")
    with B:
        b_ta = st.text_input("B", value=b_ta, key=f"b_ta_{idx}")
    C, D = st.columns(2)
    with C:
        c_ta = st.text_input("C", value=c_ta, key=f"c_ta_{idx}")
    with D:
        d_ta = st.text_input("D", value=d_ta, key=f"d_ta_{idx}")

    # Explanation
    expl_ta = st.text_area("விளக்கங்கள் :", value=expl_ta, key=f"expl_ta_{idx}", height=120)

    st.markdown("---")

    # Tamil Original
    with st.container():
        st.markdown("### Tamil Original / தமிழ் மூலப் பதிப்பு")
        st.markdown(
            f"""<div style="background:#eef9ee;border:1px solid #cfe8cf;border-radius:10px;padding:14px">
            <b>Q:</b> {q_ta or "—"}<br/>
            <b>Options (A–D):</b> {a_ta or "—"} | {b_ta or "—"} | {c_ta or "—"} | {d_ta or "—"}<br/>
            <b>Answer:</b> {ans_ta or "—"}<br/>
            <b>Explanation:</b> {expl_ta or "—"}
            </div>""",
            unsafe_allow_html=True
        )

    # English Version
    with st.container():
        st.markdown("### English Version / ஆங்கிலம்")
        st.markdown(
            f"""<div style="background:#eaf2ff;border:1px solid #cfe0ff;border-radius:10px;padding:14px">
            <b>Q:</b> {q_en or "—"}<br/>
            <b>Options (A–D):</b> {a_en or "—"} | {b_en or "—"} | {c_en or "—"} | {d_en or "—"}<br/>
            <b>Answer:</b> {ans_en or "—"}<br/>
            <b>Explanation:</b> {expl_en or "—"}
            </div>""",
            unsafe_allow_html=True
        )
