# lib/qc_state.py
from __future__ import annotations
import streamlit as st
import pandas as pd
from typing import List, Optional, Tuple

# ---------- small CSS (fonts, paddings, card look) ----------
_CSS = """
<style>
:root{
  --card-bg:#f6fbff; --card-br:#dfeaf5;
  --ta-bg:#f6fff6; --ta-br:#d8efd8;
}
.ref-card{border:1px solid var(--ta-br); background:var(--ta-bg);
          border-radius:10px; padding:14px 14px 10px 14px; margin:10px 0 22px;}
.en-card{border:1px solid var(--card-br); background:var(--card-bg);
         border-radius:10px; padding:14px 14px 10px 14px;  margin:10px 0 22px;}
h3.sme {margin: 6px 0 10px 0;}
.lbl{font-size:14px; color:#444; margin:2px 0 6px 2px; font-weight:600;}
.note{font-size:13px; color:#666;}
hr.tight {margin: 14px 0 10px 0;}
div.block-container{padding-top:1rem;}
.stTextInput>div>div input[disabled] {opacity:0.85;}
/* keep option inputs same width/height */
.opt .stTextInput>div>div, .opt .stTextInput>div>div>input {height:40px;}
</style>
"""
def _css_once():
    if "qc_css_once" not in st.session_state:
        st.session_state.qc_css_once = True
        st.markdown(_CSS, unsafe_allow_html=True)

# ---------- utilities ----------
CANDIDATES = {
    "ta_q": ["ta_q", "t_q", "ta_question", "ta_ques", "ques_ta"],
    "ta_a": ["ta_a", "t_ans", "ta_answer", "answer_ta"],
    "ta_exp": ["ta_exp", "t_exp", "ta_explanation", "explanation_ta", "ta_expl"],
    "ta_opt_a": ["ta_opt_a", "ta_a_opt", "ta_A", "ta_opt1", "ta_option_a"],
    "ta_opt_b": ["ta_opt_b", "ta_b_opt", "ta_B", "ta_opt2", "ta_option_b"],
    "ta_opt_c": ["ta_opt_c", "ta_c_opt", "ta_C", "ta_opt3", "ta_option_c"],
    "ta_opt_d": ["ta_opt_d", "ta_d_opt", "ta_D", "ta_opt4", "ta_option_d"],

    "en_q": ["en_q", "e_q", "en_question", "question_en"],
    "en_a": ["en_a", "e_ans", "en_answer", "answer_en"],
    "en_exp": ["en_exp", "e_exp", "en_explanation", "explanation_en"],
    "en_opt_a": ["en_opt_a", "en_A", "en_opt1", "option_a", "en_option_a"],
    "en_opt_b": ["en_opt_b", "en_B", "en_opt2", "option_b", "en_option_b"],
    "en_opt_c": ["en_opt_c", "en_C", "en_opt3", "option_c", "en_option_c"],
    "en_opt_d": ["en_opt_d", "en_D", "en_opt4", "option_d", "en_option_d"],
}

def _pick(df: pd.DataFrame, wanted: List[str]) -> Optional[str]:
    for name in wanted:
        if name in df.columns:
            return name
    return None

def _row_value(row: pd.Series, col: Optional[str]) -> str:
    if not col: return ""
    val = row.get(col, "")
    if pd.isna(val): return ""
    return str(val).strip()

def _options_from_row(row: pd.Series, prefix_map: Tuple[str, str, str, str]) -> List[str]:
    a = _row_value(row, prefix_map[0])
    b = _row_value(row, prefix_map[1])
    c = _row_value(row, prefix_map[2])
    d = _row_value(row, prefix_map[3])
    return [a, b, c, d]

def _format_opt_line(opts: List[str]) -> str:
    # If nothing, show short dashes so the line never looks broken
    if not any(o for o in opts):
        return "— | — | — | —"
    parts = [(o if o else "—") for o in opts]
    return " | ".join(parts)

# ---------- main renderer ----------
def render_reference_and_editor():
    """
    Renders (1) SME editor (top), (2) Tamil Original (middle), (3) English Version (bottom).
    Works with flexible column names; reads current row from st.session_state.qc_df & qc_idx.
    """
    _css_once()

    df: pd.DataFrame = st.session_state.get("qc_df", pd.DataFrame())
    idx: int = int(st.session_state.get("qc_idx", 0))
    if df.empty or idx < 0 or idx >= len(df):
        st.info("Paste a link or upload a file, then press **Load**.", icon="ℹ️")
        return

    row = df.iloc[idx]

    # --- detect columns once from the dataframe ----
    ta_cols = {
        "q": _pick(df, CANDIDATES["ta_q"]),
        "a": _pick(df, CANDIDATES["ta_a"]),
        "exp": _pick(df, CANDIDATES["ta_exp"]),
        "A": _pick(df, CANDIDATES["ta_opt_a"]),
        "B": _pick(df, CANDIDATES["ta_opt_b"]),
        "C": _pick(df, CANDIDATES["ta_opt_c"]),
        "D": _pick(df, CANDIDATES["ta_opt_d"]),
    }
    en_cols = {
        "q": _pick(df, CANDIDATES["en_q"]),
        "a": _pick(df, CANDIDATES["en_a"]),
        "exp": _pick(df, CANDIDATES["en_exp"]),
        "A": _pick(df, CANDIDATES["en_opt_a"]),
        "B": _pick(df, CANDIDATES["en_opt_b"]),
        "C": _pick(df, CANDIDATES["en_opt_c"]),
        "D": _pick(df, CANDIDATES["en_opt_d"]),
    }

    # values
    ta_q  = _row_value(row, ta_cols["q"])
    ta_a  = _row_value(row, ta_cols["a"])
    ta_ex = _row_value(row, ta_cols["exp"])
    ta_opts = _options_from_row(row, (ta_cols["A"], ta_cols["B"], ta_cols["C"], ta_cols["D"]))

    en_q  = _row_value(row, en_cols["q"])
    en_a  = _row_value(row, en_cols["a"])
    en_ex = _row_value(row, en_cols["exp"])
    en_opts = _options_from_row(row, (en_cols["A"], en_cols["B"], en_cols["C"], en_cols["D"]))

    # Auto-answer: if 'ta_a' is a single letter A/B/C/D and that option exists, compute display
    auto_ta_ans = ta_a
    if ta_a.upper() in ("A", "B", "C", "D"):
        m = {"A":0, "B":1, "C":2, "D":3}
        auto_ta_ans = ta_opts[m[ta_a.upper()]] if ta_opts[m[ta_a.upper()]] else ta_a

    st.markdown('<h3 class="sme">SME Edit Console / ஆசிரியர் திருத்தம்</h3>', unsafe_allow_html=True)

    # --------------- Editor (top) ----------------
    st.markdown('<div class="lbl">கேள்வி :</div>', unsafe_allow_html=True)
    q_col, ans_col = st.columns([2.4, 1.1])
    with q_col:
        st.text_area(" ", value=ta_q or "—", key="ed_q", label_visibility="collapsed", height=86)
    with ans_col:
        st.markdown('<div class="lbl">பதில் / Answer</div>', unsafe_allow_html=True)
        st.text_input(" ", value=auto_ta_ans or "—", key="ed_ans", label_visibility="collapsed")

    st.markdown('<div class="lbl">விருப்பங்கள் (A–D) / Options</div>', unsafe_allow_html=True)
    r1c1, r1c2 = st.columns(2)
    r2c1, r2c2 = st.columns(2)
    with r1c1:
        st.text_input("A", value=ta_opts[0] or "—", key="ed_A", help="Auto Display \"A\"", disabled=True)
    with r1c2:
        st.text_input("C", value=ta_opts[2] or "—", key="ed_C", help="Auto Display \"C\"", disabled=True)
    with r2c1:
        st.text_input("B", value=ta_opts[1] or "—", key="ed_B", help="Auto Display \"B\"", disabled=True)
    with r2c2:
        st.text_input("D", value=ta_opts[3] or "—", key="ed_D", help="Auto Display \"D\"", disabled=True)

    gl_col, exp_col = st.columns([1.1, 2.4])
    with gl_col:
        st.markdown('<div class="lbl">சொல் அகராதி / Glossary (Type the word)</div>', unsafe_allow_html=True)
        st.text_input(" ", key="ed_gloss", label_visibility="collapsed")
    with exp_col:
        st.markdown('<div class="lbl">விளக்கங்கள் :</div>', unsafe_allow_html=True)
        st.text_area(" ", value=ta_ex or "—", key="ed_exp", label_visibility="collapsed", height=120)

    st.markdown('<hr class="tight">', unsafe_allow_html=True)

    # --------------- Tamil Original (middle) ----------------
    with st.container():
        st.markdown("### Tamil Original / தமிழ் மூலப் பதிப்பு")
        opts_line_ta = _format_opt_line(ta_opts)
        st.markdown(
            f"""
<div class="ref-card">
<p><b>Q:</b> {ta_q or "—"}</p>
<p><b>Options (A–D):</b> {opts_line_ta}</p>
<p><b>Answer:</b> {ta_a or "—"}</p>
<p><b>Explanation:</b> {ta_ex or "—"}</p>
</div>
""",
            unsafe_allow_html=True,
        )

    # --------------- English Version (bottom) ----------------
    with st.container():
        st.markdown("### English Version / ஆங்கிலம்")
        opts_line_en = _format_opt_line(en_opts)
        st.markdown(
            f"""
<div class="en-card">
<p><b>Q:</b> {en_q or "—"}</p>
<p><b>Options (A–D):</b> {opts_line_en}</p>
<p><b>Answer:</b> {en_a or "—"}</p>
<p><b>Explanation:</b> {en_ex or "—"}</p>
</div>
""",
            unsafe_allow_html=True,
        )
