# lib/qc_state.py
from __future__ import annotations
import streamlit as st
import pandas as pd
from typing import Iterable, Optional

# ---------- tiny CSS for the two display cards ----------
_CARD_CSS = """
<style>
.en-card, .ta-card{
  border-radius: 10px; padding: 14px 18px; margin: 8px 0 18px 0;
  border: 1px solid rgba(0,0,0,0.06);
}
.ta-card{ background: #eaf6ea; }   /* light green */
.en-card{ background: #eaf0ff; }   /* light blue  */
.card-h{
  display:inline-block; font-weight:600; font-size:0.95rem;
  color:#1f3554; background:rgba(255,255,255,0.6);
  padding:4px 10px; border-radius:12px; margin-bottom:8px;
}
.card-p{ margin: 6px 0; }
.card-lbl{ font-weight:600; }
</style>
"""

def _css_once():
    if not st.session_state.get("_qc_css_once"):
        st.markdown(_CARD_CSS, unsafe_allow_html=True)
        st.session_state["_qc_css_once"] = True

# ---------- helpers to read whichever column names you actually have ----------
def _first_nonempty(row: pd.Series, candidates: Iterable[str]) -> str:
    for c in candidates:
        if c in row and pd.notna(row[c]) and str(row[c]).strip():
            return str(row[c]).strip()
    return "—"

def _options_line(row: pd.Series, cand_join: Iterable[str], cand_split: Iterable[Iterable[str]]) -> str:
    """Try 1) a pre-joined Options column, else 2) join A/B/C/D columns, else 3) split by known separators."""
    # 1) already joined column
    joined = _first_nonempty(row, cand_join)
    if joined != "—":
        return joined

    # 2) join lettered columns (A/B/C/D in either lang)
    parts = []
    for choices in (("A","B","C","D"),
                    ("a","b","c","d"),
                    ("opt_a","opt_b","opt_c","opt_d"),
                    ("ta_A","ta_B","ta_C","ta_D"),
                    ("ta_a","ta_b","ta_c","ta_d")):
        if all((k in row) for k in choices):
            for k in choices:
                v = str(row.get(k, "")).strip()
                if v and v != "nan":
                    parts.append(v)
            if parts:
                return " | ".join(parts)
    # 3) split by known separators from any single cell
    for col in cand_join:
        if col in row and pd.notna(row[col]):
            raw = str(row[col]).strip()
            if raw:
                for seps in cand_split:
                    tmp = raw
                    for s in seps:
                        tmp = tmp.replace(s, "|")
                    segs = [s.strip() for s in tmp.split("|") if s.strip()]
                    if 1 < len(segs) <= 6:
                        return " | ".join(segs)
    return "—"

# ---------- main renderer you import on the page ----------
def render_reference_and_editor():
    """
    Shows the non-editable reference cards:
      - Tamil Original (green)
      - English Version (blue)
    Uses st.session_state.qc_df and st.session_state.qc_idx if present.
    If not present, shows placeholders.
    """
    _css_once()

    df: Optional[pd.DataFrame] = st.session_state.get("qc_df", None)
    idx: Optional[int] = st.session_state.get("qc_idx", 0)

    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        _render_card_pair(("தமிழ் மூலப் பதிப்பு", "—", "—", "—", "—"),
                          ("English Version",   "—", "—", "—", "—"))
        return

    # Clip index to range
    if idx is None or not isinstance(idx, int):
        idx = 0
    idx = max(0, min(idx, len(df)-1))
    row = df.iloc[idx]

    # Column candidates (you can add more variants safely)
    ta_Q_cols   = ["ta_q", "ta_question", "கேள்வி", "தமிழ்_கேள்வி"]
    ta_OP_cols  = ["ta_opts", "ta_options", "விருப்பங்கள்"]
    ta_A_cols   = ["ta_ans", "ta_answer", "பதில்"]
    ta_EX_cols  = ["ta_ex", "ta_expl", "விளக்கம்"]

    en_Q_cols   = ["en_q", "question", "Question", "EN_Question"]
    en_OP_cols  = ["en_opts", "options", "Options", "EN_Options"]
    en_A_cols   = ["en_ans", "answer", "Answer", "EN_Answer"]
    en_EX_cols  = ["en_ex", "explanation", "Explanation", "EN_Explanation"]

    # Build display values
    ta_q = _first_nonempty(row, ta_Q_cols)
    ta_opts = _options_line(row, ta_OP_cols, cand_split=[("||",), ("|",), ("  ",), (";",), (",",)])
    ta_ans = _first_nonempty(row, ta_A_cols)
    ta_ex  = _first_nonempty(row, ta_EX_cols)

    en_q = _first_nonempty(row, en_Q_cols)
    en_opts = _options_line(row, en_OP_cols, cand_split=[("||",), ("|",), ("  ",), (";",), (",",)])
    en_ans = _first_nonempty(row, en_A_cols)
    en_ex  = _first_nonempty(row, en_EX_cols)

    _render_card_pair(
        ("தமிழ் மூலப் பதிப்பு", ta_q, ta_opts, ta_ans, ta_ex),
        ("English Version",     en_q, en_opts, en_ans, en_ex),
    )

def _render_card_pair(ta_tuple, en_tuple):
    ta_title, ta_q, ta_opts, ta_ans, ta_ex = ta_tuple
    en_title, en_q, en_opts, en_ans, en_ex = en_tuple

    # Tamil card
    st.markdown(f"""
<div class="ta-card">
  <div class="card-h">{ta_title}</div>
  <p class="card-p"><span class="card-lbl">Q:</span> {ta_q}</p>
  <p class="card-p"><span class="card-lbl">Options (A–D):</span> {ta_opts}</p>
  <p class="card-p"><span class="card-lbl">Answer:</span> {ta_ans}</p>
  <p class="card-p"><span class="card-lbl">Explanation:</span> {ta_ex}</p>
</div>
""", unsafe_allow_html=True)

    # English card
    st.markdown(f"""
<div class="en-card">
  <div class="card-h">{en_title}</div>
  <p class="card-p"><span class="card-lbl">Q:</span> {en_q}</p>
  <p class="card-p"><span class="card-lbl">Options (A–D):</span> {en_opts}</p>
  <p class="card-p"><span class="card-lbl">Answer:</span> {en_ans}</p>
  <p class="card-p"><span class="card-lbl">Explanation:</span> {en_ex}</p>
</div>
""", unsafe_allow_html=True)
