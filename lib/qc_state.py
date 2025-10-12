# lib/qc_state.py
from __future__ import annotations
import streamlit as st
import pandas as pd

# -------------------------------------------------------
# CSS for card display (green for Tamil, blue for English)
# -------------------------------------------------------
_CARD_STYLE = """
<style>
.card-ta, .card-en {
    border-radius: 10px;
    padding: 14px 18px;
    margin: 10px 0 18px 0;
    border: 1px solid rgba(0,0,0,0.06);
}
.card-ta {
    background-color: #eaf6ea;  /* Light green */
}
.card-en {
    background-color: #eaf0ff;  /* Light blue */
}
.card-title {
    display:inline-block;
    font-weight:600;
    font-size:0.95rem;
    color:#1f3554;
    background:rgba(255,255,255,0.6);
    padding:4px 10px;
    border-radius:12px;
    margin-bottom:10px;
}
.card-line {
    margin:6px 0;
}
.card-label {
    font-weight:600;
}
</style>
"""

def _load_css_once():
    if not st.session_state.get("_qc_css_loaded"):
        st.markdown(_CARD_STYLE, unsafe_allow_html=True)
        st.session_state["_qc_css_loaded"] = True


# -------------------------------------------------------
# Render one bilingual question set
# -------------------------------------------------------
def render_reference_and_editor():
    _load_css_once()

    df = st.session_state.get("qc_df", None)
    idx = st.session_state.get("qc_idx", 0)

    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        _render_cards(
            ta={"Q": "—", "Options": "—", "Answer": "—", "Explanation": "—"},
            en={"Q": "—", "Options": "—", "Answer": "—", "Explanation": "—"}
        )
        return

    # Safely clip index
    if idx is None or not isinstance(idx, int):
        idx = 0
    idx = max(0, min(idx, len(df) - 1))
    row = df.iloc[idx]

    # Extract Tamil content
    ta_Q = str(row.get("கேள்வி", "—")).strip()
    ta_OP = str(row.get("விருப்பங்கள்", "—")).strip()
    ta_ANS = str(row.get("பதில்", "—")).strip()
    ta_EXP = str(row.get("விளக்கம்", "—")).strip()

    # Extract English content
    en_Q = str(row.get("question", "—")).strip()
    en_OP = str(row.get("questionOptions", "—")).strip()
    en_ANS = str(row.get("answers", "—")).strip()
    en_EXP = str(row.get("explanation", "—")).strip()

    _render_cards(
        ta={"Q": ta_Q, "Options": ta_OP, "Answer": ta_ANS, "Explanation": ta_EXP},
        en={"Q": en_Q, "Options": en_OP, "Answer": en_ANS, "Explanation": en_EXP}
    )


# -------------------------------------------------------
# UI layout of Tamil (top) and English (bottom)
# -------------------------------------------------------
def _render_cards(ta, en):
    st.markdown(f"""
<div class="card-ta">
  <div class="card-title">தமிழ் மூலப் பதிப்பு</div>
  <p class="card-line"><span class="card-label">கேள்வி:</span> {ta['Q']}</p>
  <p class="card-line"><span class="card-label">விருப்பங்கள் (A–D):</span> {ta['Options']}</p>
  <p class="card-line"><span class="card-label">பதில்:</span> {ta['Answer']}</p>
  <p class="card-line"><span class="card-label">விளக்கம்:</span> {ta['Explanation']}</p>
</div>

<div class="card-en">
  <div class="card-title">English Version</div>
  <p class="card-line"><span class="card-label">Q:</span> {en['Q']}</p>
  <p class="card-line"><span class="card-label">Options (A–D):</span> {en['Options']}</p>
  <p class="card-line"><span class="card-label">Answer:</span> {en['Answer']}</p>
  <p class="card-line"><span class="card-label">Explanation:</span> {en['Explanation']}</p>
</div>
""", unsafe_allow_html=True)
