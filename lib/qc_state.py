# lib/qc_state.py
from __future__ import annotations
import streamlit as st
import pandas as pd

def _css_editor_once():
    if st.session_state.get("_qc_css_done"): 
        return
    st.session_state["_qc_css_done"] = True
    st.markdown("""
    <style>
      .h6{font-size:15px;font-weight:700;margin:8px 0 4px;}
      .card{
        background:#f6f9ff;border:1px solid #cfe0ff;border-radius:12px;padding:10px 14px;
      }
      .card.ta{background:#f6fff6;border-color:#cfead1;}
      .sm-title{font-size:18px;font-weight:700;margin:6px 0 10px;}
      .rowgap > div{margin-bottom:8px;}
      .stTextInput>div>div>input{font-size:16px;}
      .stTextArea textarea{font-size:16px; line-height:1.4;}
      .tightbox .stTextArea>div{margin-bottom:0;}
    </style>
    """, unsafe_allow_html=True)

def _field(df: pd.DataFrame, row: int, col: str, label: str, key: str, area=False):
    """No default+set clash: we only set value if key absent."""
    if key not in st.session_state:
        st.session_state[key] = str(df.at[row, col]) if col in df.columns else ""
    if area:
        return st.text_area(label, key=key, label_visibility="collapsed", height=84)
    return st.text_input(label, key=key, label_visibility="collapsed")

def render_reference_and_editor(editor_first: bool=True):
    """
    Shows (1) editor grid, (2) Tamil Original, (3) English Original when editor_first=True.
    Expects st.session_state.qc_df and qc_idx.
    """
    _css_editor_once()
    if "qc_df" not in st.session_state or st.session_state.qc_df.empty:
        st.info("Paste a link or upload a file at the top strip to begin.")
        return

    df: pd.DataFrame = st.session_state.qc_df
    i = st.session_state.get("qc_idx", 0)

    # ---- 1) EDITOR FIRST ------------------------------------------------------
    st.markdown('<div class="sm-title">SME Edit Console / ஆசிரியர் திருத்தம்</div>', unsafe_allow_html=True)
    # Q
    _field(df, i, "ta_question", "Q", "q_ta", area=True)

    # ABCD grid (two columns, tight)
    c1, c2 = st.columns(2)
    with c1:
        _field(df, i, "ta_opt_a", "A", "opt_a")
        _field(df, i, "ta_opt_c", "C", "opt_c")
    with c2:
        _field(df, i, "ta_opt_b", "B", "opt_b")
        _field(df, i, "ta_opt_d", "D", "opt_d")

    g1, g2 = st.columns([1,1])
    with g1:
        st.caption("சொல் அகராதி / Glossary")
        _field(df, i, "glossary", "Glossary", "glossary_word")
    with g2:
        st.caption("பதில் / Answer")
        _field(df, i, "ta_answer", "Answer", "ans_ta")

    st.caption("விளக்கங்கள் :")
    _field(df, i, "ta_explanation", "Explanation", "exp_ta", area=True)

    st.write("")  # small spacer

    # ---- 2) TAMIL ORIGINAL ----------------------------------------------------
    st.markdown('<div class="h6">Tamil Original / தமிழ் மூலப் பதிப்பு</div>', unsafe_allow_html=True)
    st.markdown(
        _ref_card(
            df, i,
            q_col="ta_question",
            a_col="ta_answer",
            o_cols=["ta_opt_a","ta_opt_b","ta_opt_c","ta_opt_d"],
            e_col="ta_explanation",
            ta=True
        ),
        unsafe_allow_html=True
    )

    # ---- 3) ENGLISH ORIGINAL --------------------------------------------------
    st.markdown('<div class="h6">English Version / ஆங்கிலம்</div>', unsafe_allow_html=True)
    st.markdown(
        _ref_card(
            df, i,
            q_col="en_question",
            a_col="en_answer",
            o_cols=["en_opt_a","en_opt_b","en_opt_c","en_opt_d"],
            e_col="en_explanation",
            ta=False
        ),
        unsafe_allow_html=True
    )

def _ref_card(df, i, q_col, a_col, o_cols, e_col, ta=False):
    def val(c): 
        return (str(df.at[i,c]) if c in df.columns and pd.notna(df.at[i,c]) else "").strip()

    q = val(q_col); a = val(a_col); e = val(e_col)
    o = [val(c) for c in o_cols]
    cls = "card ta" if ta else "card"
    html = f"""
    <div class="{cls}">
      <div><b>Q:</b> {q}</div>
      <div><b>Options (A–D):</b> A) {o[0]} &nbsp;|&nbsp; B) {o[1]} &nbsp;|&nbsp; C) {o[2]} &nbsp;|&nbsp; D) {o[3]}</div>
      <div><b>Answer:</b> {a}</div>
      <div><b>Explanation:</b> {e}</div>
    </div>
    """
    return html
