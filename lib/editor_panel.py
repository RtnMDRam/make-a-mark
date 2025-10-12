# lib/editor_panel.py
import streamlit as st
import pandas as pd
from lib.qc_state import get_ss

def _txt(x) -> str:
    return "" if (x is None or (isinstance(x,float) and pd.isna(x))) else str(x).replace("\r\n","\n").strip()

def _split_opts(v: str):
    if not v: return ["","","",""]
    parts = [p.strip() for p in v.replace("A)","|").replace("B)","|").replace("C)","|").replace("D)","|").split("|") if p.strip()]
    while len(parts)<4: parts.append("")
    return parts[:4]

def render_editor():
    ss = get_ss()
    row = ss.qc_work.iloc[ss.qc_idx]
    rid = row["ID"]

    # ---- Reference cards -------------------------------------------------
    def card(title, q, op, ans, exp, cls):
        st.markdown(
            f"""
            <div style="border:1px solid #cdb; background:{cls}; padding:10px 12px; border-radius:8px; margin:6px 0;">
              <span style="font-weight:600; background:#e5e5e5; padding:3px 10px; border-radius:10px;">{title}</span><br>
              <b>Q:</b> {_txt(q)}<br>
              <b>Options (A–D):</b> {_txt(op)}<br>
              <b>Answer:</b> {_txt(ans)}<br>
              <b>Explanation:</b> {_txt(exp)}
            </div>
            """, unsafe_allow_html=True
        )

    en_q, en_op, en_ans, en_exp = [row[c] for c in ("Question (English)","Options (English)","Answer (English)","Explanation (English)")]
    ta_q, ta_op, ta_ans, ta_exp = [row[c] for c in ("Question (Tamil)","Options (Tamil)","Answer (Tamil)","Explanation (Tamil)")]

    card("English Version / ஆங்கிலம்", en_q, en_op, en_ans, en_exp, "#eef3ff")
    card("Tamil Original / தமிழ் மூலப் பதிப்பு", ta_q, ta_op, ta_ans, ta_exp, "#eff8e8")

    # ---- Compact SME editor ---------------------------------------------
    st.markdown('<div class="sme-title">SME Edit Console / ஆசிரியர் திருத்தம்</div>', unsafe_allow_html=True)

    rk = f"{ss.qc_idx}"
    q = st.text_area("", value=_txt(ta_q), key=f"q_in_{rk}", height=72, label_visibility="collapsed")

    A,B,C,D = _split_opts(_txt(ta_op))
    cA, cB = st.columns(2)
    with cA:
        A = st.text_input(" ", value=A, key=f"a_in_{rk}", label_visibility="collapsed", placeholder="A")
    with cB:
        B = st.text_input(" ", value=B, key=f"b_in_{rk}", label_visibility="collapsed", placeholder="B")

    cC, cD = st.columns(2)
    with cC:
        C = st.text_input(" ", value=C, key=f"c_in_{rk}", label_visibility="collapsed", placeholder="C")
    with cD:
        D = st.text_input(" ", value=D, key=f"d_in_{rk}", label_visibility="collapsed", placeholder="D")

    gL, gR = st.columns([2,2])
    with gL:
        st.caption("சொல் அகராதி / Glossary")
        gq = st.text_input("", key="gloss_q", label_visibility="collapsed", placeholder="(Type the word)")
    with gR:
        st.caption("பதில் / Answer")
        ans = st.text_input(" ", value=_txt(ta_ans), key=f"ans_in_{rk}", label_visibility="collapsed", placeholder="A:")

    st.caption("விளக்கங்கள் :")
    exp = st.text_area("", value=_txt(ta_exp), key=f"exp_in_{rk}", height=140, label_visibility="collapsed")

    # ---- Persist into merged Tamil column (QC_TA) -----------------------
    merged = []
    if _txt(q): merged.append(f"Q: {q}")
    opts = [A,B,C,D]
    if any(_txt(x) for x in opts):
        merged.append("Options (A–D): " + " | ".join([f"{lbl}) {opts[i]}" for i,lbl in enumerate(["A","B","C","D"])]))
    if _txt(ans): merged.append(f"Answer: {ans}")
    if _txt(exp): merged.append(f"Explanation: {exp}")
    ss.qc_work.at[ss.qc_idx, "QC_TA"] = "\n".join(merged)

    # ---- React to top buttons (set by top_strip) ------------------------
    if st.session_state.pop("_just_save", False):
        pass  # already saved into qc_work via QC_TA above
    if st.session_state.pop("_mark_complete", False):
        pass  # no-op here; you can add tagging if needed
    if st.session_state.pop("_save_and_next", False):
        if ss.qc_idx < len(ss.qc_work) - 1:
            ss.qc_idx += 1
            st.rerun()
