# lib/qc_state.py
import streamlit as st
import pandas as pd

# ---------- helpers ----------
def _get_first(row: pd.Series, candidates, default=""):
    for c in candidates:
        if c in row and pd.notna(row[c]) and str(row[c]).strip() != "":
            return str(row[c]).strip()
    return default

def _opts_line(a, b, c, d):
    # Always show 4 slots; use em dash for any missing ones
    slots = [a or "—", b or "—", c or "—", d or "—"]
    return " | ".join(slots)

# ---------- main renderer ----------
def render_reference_and_editor():
    """
    Uses st.session_state.qc_df (DataFrame) and st.session_state.qc_idx (int).
    Renders:
      1) Teacher edit console (top, minimal spacing, NO A/B/C/D labels)
      2) Tamil Original reference (middle) with Options line
      3) English reference (bottom) with Options line
    """
    if "qc_df" not in st.session_state or st.session_state.qc_df is None:
        return
    df: pd.DataFrame = st.session_state.qc_df
    idx: int = int(st.session_state.get("qc_idx", 0))
    if idx < 0 or idx >= len(df):
        st.warning("Row index is out of range.")
        return

    row = df.iloc[idx]

    # Column name fallbacks (works with your older/newer file headers)
    ta_q = _get_first(row, ["ta_q", "ta_question", "t_q", "q_ta"])
    ta_a = _get_first(row, ["ta_a", "ta_opt_a", "ta_A", "ta_optA"])
    ta_b = _get_first(row, ["ta_b", "ta_opt_b", "ta_B", "ta_optB"])
    ta_c = _get_first(row, ["ta_c", "ta_opt_c", "ta_C", "ta_optC"])
    ta_d = _get_first(row, ["ta_d", "ta_opt_d", "ta_D", "ta_optD"])
    ta_ans = _get_first(row, ["ta_ans", "ta_answer", "answer_ta"])
    ta_ex  = _get_first(row, ["ta_ex", "ta_explanation", "explanation_ta"])

    en_q = _get_first(row, ["en_q", "en_question", "e_q", "q_en"])
    en_a = _get_first(row, ["en_a", "en_opt_a", "en_A", "en_optA"])
    en_b = _get_first(row, ["en_b", "en_opt_b", "en_B", "en_optB"])
    en_c = _get_first(row, ["en_c", "en_opt_c", "en_C", "en_optC"])
    en_d = _get_first(row, ["en_d", "en_opt_d", "en_D", "en_optD"])
    en_ans = _get_first(row, ["en_ans", "en_answer", "answer_en"])
    en_ex  = _get_first(row, ["en_ex", "en_explanation", "explanation_en"])

    # ---------- 1) EDIT CONSOLE (top) ----------
    st.markdown("## ஆசிரியர் திருத்தம்")  # Tamil-only heading

    # Q + Answer row
    c1, c2 = st.columns([2, 1])
    with c1:
        st.text_area("கேள்வி :", value=ta_q, key="ed_ta_q", height=80)
    with c2:
        st.text_input("பதில் / Answer", value=ta_ans, key="ed_ta_ans")

    # Options row (NO explicit “A/B/C/D” labels — placeholders only)
    cA, cB, cC, cD = st.columns([1, 1, 1, 1])
    with cA:
        st.text_input(label="A", value=ta_a, key="ed_ta_A",
                      placeholder="A", label_visibility="collapsed")
    with cB:
        st.text_input(label="B", value=ta_b, key="ed_ta_B",
                      placeholder="B", label_visibility="collapsed")
    with cC:
        st.text_input(label="C", value=ta_c, key="ed_ta_C",
                      placeholder="C", label_visibility="collapsed")
    with cD:
        st.text_input(label="D", value=ta_d, key="ed_ta_D",
                      placeholder="D", label_visibility="collapsed")

    # Glossary + Explanation
    g1, g2 = st.columns([1, 2])
    with g1:
        st.text_input("சொல் அகராதி / Glossary (Type the word)", value="",
                      key="ed_glossary")
    with g2:
        st.text_area("விளக்கம் :", value=ta_ex, key="ed_ta_ex", height=110)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ---------- 2) TAMIL ORIGINAL (middle) ----------
    st.markdown("### Tamil Original / தமிழ் மூலப் பதிவு")
    ta_opts_line = _opts_line(ta_a, ta_b, ta_c, ta_d)
    st.markdown(
        f"""
        <div class="ta-card en-card" style="background:#eef9ee;padding:16px;border:1px solid #cfe8cf;border-radius:8px;">
          <p><b>Q:</b> {ta_q or "—"}</p>
          <p><b>Options (A–D):</b> {ta_opts_line}</p>
          <p><b>Answer:</b> {ta_ans or "—"}</p>
          <p><b>Explanation:</b> {ta_ex or "—"}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------- 3) ENGLISH VERSION (bottom) ----------
    st.markdown("### English Version / ஆங்கிலம்")
    en_opts_line = _opts_line(en_a, en_b, en_c, en_d)
    st.markdown(
        f"""
        <div class="en-card" style="background:#eef4ff;padding:16px;border:1px solid #d7e3ff;border-radius:8px;">
          <p><b>Q:</b> {en_q or "—"}</p>
          <p><b>Options (A–D):</b> {en_opts_line}</p>
          <p><b>Answer:</b> {en_ans or "—"}</p>
          <p><b>Explanation:</b> {en_ex or "—"}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
