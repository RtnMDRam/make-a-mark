# lib/qc_state.py
import streamlit as st
import pandas as pd
from typing import List, Optional

# ---------- helpers ----------
def _pick(row: pd.Series, keys: List[str], default: str = "—") -> str:
    """Pick the first non-empty value from possible column name variants."""
    for k in keys:
        if k in row and pd.notna(row[k]) and str(row[k]).strip() != "":
            return str(row[k]).strip()
    return default

def _pick_many(row: pd.Series, key_groups: List[List[str]]) -> List[str]:
    """Pick 4 option values given 4 groups of possible keys for A/B/C/D."""
    vals = []
    for group in key_groups:
        vals.append(_pick(row, group, default="—"))
    return vals

def _opts_line(vals: List[str]) -> str:
    """Join options into a single compact line, always 4 items."""
    # Ensure 4 items:
    vals = (vals + ["—"] * 4)[:4]
    return " | ".join(vals)

def _card(title: str, q: str, opts_line: str, ans: str, expl: str, css_class: str):
    st.markdown(
        f"""
<div class="{css_class}">
  <p class="title">{title}</p>
  <p><b>Q:</b> {q}</p>
  <p><b>Options (A–D):</b> {opts_line}</p>
  <p><b>Answer:</b> {ans}</p>
  <p><b>Explanation:</b> {expl}</p>
</div>
""",
        unsafe_allow_html=True,
    )

def _inject_reference_css_once():
    if st.session_state.get("_ref_css_done"):
        return
    st.session_state["_ref_css_done"] = True
    st.markdown(
        """
<style>
.ref-card{
  border:1px solid #e5e7eb;
  border-radius:12px;
  padding:14px 16px;
  margin:14px 0 18px 0;
  line-height:1.5;
  font-size:14.5px;
}
.ta-card{ background:#eaf6ef; }   /* soft green */
.en-card{ background:#eaf2ff; }   /* soft blue  */
.ref-card .title{
  display:inline-block;
  font-weight:600;
  margin:0 0 6px 0;
  padding:2px 8px;
  border-radius:8px;
  background:rgba(0,0,0,0.06);
}
.ref-card b{ font-weight:600; }
</style>
""",
        unsafe_allow_html=True,
    )

# ---------- main renderer ----------
def render_reference_and_editor():
    """
    Renders (1) reference cards (Tamil, English) exactly like the approved look,
    then (2) the existing editor (kept as-is). If you want *only* the cards for now,
    comment the EDITOR block at the bottom.
    Requires:
        st.session_state.qc_df : pandas.DataFrame
        st.session_state.qc_idx: int   (current row index)
    """
    df: Optional[pd.DataFrame] = st.session_state.get("qc_df")
    idx: Optional[int] = st.session_state.get("qc_idx")
    if df is None or idx is None or idx < 0 or idx >= len(df):
        return

    row = df.iloc[idx]

    _inject_reference_css_once()

    # --- Tamil pickers (robust name variants) ---
    ta_q      = _pick(row, ["ta_q", "q_ta", "ta_question", "question_ta", "tq"])
    ta_ans    = _pick(row, ["ta_answer", "answer_ta", "ta_ans", "ans_ta"])
    ta_expl   = _pick(row, ["ta_explanation", "explanation_ta", "ta_expl", "expl_ta"])

    ta_opts = _pick_many(
        row,
        [
            ["ta_opt_a", "ta_A", "opt_a_ta", "taA", "A_ta"],
            ["ta_opt_b", "ta_B", "opt_b_ta", "taB", "B_ta"],
            ["ta_opt_c", "ta_C", "opt_c_ta", "taC", "C_ta"],
            ["ta_opt_d", "ta_D", "opt_d_ta", "taD", "D_ta"],
        ],
    )
    ta_opts_line = _opts_line(ta_opts)

    # --- English pickers ---
    en_q    = _pick(row, ["en_q", "q_en", "en_question", "question_en", "eq"])
    en_ans  = _pick(row, ["en_answer", "answer_en", "en_ans", "ans_en"])
    en_expl = _pick(row, ["en_explanation", "explanation_en", "en_expl", "expl_en"])

    en_opts = _pick_many(
        row,
        [
            ["en_opt_a", "en_A", "opt_a_en", "enA", "A_en"],
            ["en_opt_b", "en_B", "opt_b_en", "enB", "B_en"],
            ["en_opt_c", "en_C", "opt_c_en", "enC", "C_en"],
            ["en_opt_d", "en_D", "opt_d_en", "enD", "D_en"],
        ],
    )
    en_opts_line = _opts_line(en_opts)

    # --- Reference cards (non-editable) ---
    _card("Tamil Original / தமிழ் மூலப் பதிப்பு", ta_q, ta_opts_line, ta_ans, ta_expl, "ref-card ta-card")
    _card("English Version / ஆங்கிலம்",        en_q, en_opts_line, en_ans, en_expl, "ref-card en-card")

    # --------- EDITOR (kept as-is) ----------
    # If you want to hide the edit console temporarily, just comment out the block below.
    if st.session_state.get("_show_editor", True):
        st.write("")  # small spacer; your page likely already renders editor elsewhere
        # (Leave your current editor controls untouched; this function now only guarantees
        # the reference cards above look right. If your editor UI is built elsewhere,
        # you can remove this whole section.)
        pass
