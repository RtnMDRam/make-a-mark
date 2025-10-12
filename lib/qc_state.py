# lib/qc_state.py
import re
import streamlit as st

# ---------- tiny CSS once ----------
def _css_once():
    if "_qc_css_done" in st.session_state:
        return
    st.session_state["_qc_css_done"] = True
    st.markdown(
        """
<style>
.ta-card, .en-card{
  border-radius:12px; padding:16px 18px; margin:14px 0 26px 0;
  border:1px solid rgba(0,0,0,0.06);
}
.ta-card{ background:#eaf6ea; }     /* light green */
.en-card{ background:#eaf0ff; }     /* light blue */

.pill{ display:inline-block; font-size:13px; line-height:1;
  padding:6px 10px; border-radius:12px; background:rgba(0,0,0,.08);
  margin-bottom:10px; font-weight:600;
}
.pill.ta{ background:#d9f0d9; }
.pill.en{ background:#dbe6ff; }

.ta-card p, .en-card p { margin: 8px 0; }
.ta-card b, .en-card b { font-weight: 700; }
</style>
        """,
        unsafe_allow_html=True,
    )

# ---------- helpers ----------
def _first_nonempty(df, idx, names):
    """Return first nonempty value for row idx among normalized column names."""
    want = [n.strip().lower() for n in names]
    for col in df.columns:
        if col.strip().lower() in want:
            val = str(df.iloc[idx].get(col, "")).strip()
            if val and val.lower() not in ("nan", "none"):
                return val
    return ""

def _opts_from_row(df, idx, a_names, b_names, c_names, d_names, merged_names):
    """Build 'A | B | C | D' string from split (A/B/C/D) or a merged options column."""
    A = _first_nonempty(df, idx, a_names)
    B = _first_nonempty(df, idx, b_names)
    C = _first_nonempty(df, idx, c_names)
    D = _first_nonempty(df, idx, d_names)
    parts = [p for p in (A, B, C, D) if p]
    if parts:
        return " | ".join(parts)

    merged = _first_nonempty(df, idx, merged_names)
    if merged:
        txt = str(merged).strip()

        # Split patterns like: A) foo B) bar C) baz D) qux
        m = re.split(r"\b[Aa]\)\s*|\b[Bb]\)\s*|\b[Cc]\)\s*|\b[Dd]\)\s*", txt)
        if len(m) == 5:
            parts = [s.strip(" .;|") for s in m[1:]]
            return " | ".join(parts)

        # Split patterns like: 1) foo 2) bar 3) baz 4) qux
        n = re.split(r"\b1\)\s*|\b2\)\s*|\b3\)\s*|\b4\)\s*", txt)
        if len(n) == 5:
            parts = [s.strip(" .;|") for s in n[1:]]
            return " | ".join(parts)

        # Final fallback: split by common separators
        parts = [p.strip(" .;|") for p in re.split(r"\s*[|•;]\s*", txt) if p.strip()]
        if len(parts) == 4:
            return " | ".join(parts)

    return "—"

# ---------- main renderer (cards) ----------
def render_reference_and_editor():
    """
    Renders the read-only Tamil and English reference cards (no cross-language fallback).
    Expects:
      st.session_state['qc_df']  - pandas DataFrame
      st.session_state['qc_idx'] - current row index (int)
    """
    _css_once()

    df = st.session_state.get("qc_df")
    idx = st.session_state.get("qc_idx", 0)

    if df is None or len(df) == 0 or idx >= len(df):
        st.info("Paste a link or upload a file at the top strip, then press **Load**.")
        return False

    # ---- alias sets (expandable) ----
    TA_Q   = ["ta_q", "ta_question", "question_ta", "q_ta", "கேள்வி", "கேள்வி :"]
    TA_A   = ["ta_ans", "ta_answer", "ta_key", "answer_ta", "சரியான பதில்", "பதில்", "பதில் / answer"]
    TA_EX  = ["ta_explanation", "explanation_ta", "ta_exp", "விளக்கம்", "விளக்கங்கள்", "விளக்கங்கள் :"]

    TA_AA  = ["ta_a", "ta_opt_a", "ta_option_a", "விருப்பம் a", "விருப்பம் அ", "விருப்பம் A"]
    TA_BB  = ["ta_b", "ta_opt_b", "ta_option_b", "விருப்பம் b", "விருப்பம் B"]
    TA_CC  = ["ta_c", "ta_opt_c", "ta_option_c", "விருப்பம் c", "விருப்பம் C"]
    TA_DD  = ["ta_d", "ta_opt_d", "ta_option_d", "விருப்பம் d", "விருப்பம் D"]
    TA_MERGED = ["ta_options", "ta_option", "options_ta", "options (ta)", "விருப்பங்கள்", "விருப்பங்கள் (a–d)"]

    EN_Q   = ["en_q", "en_question", "question_en", "q_en", "question", "q"]
    EN_A   = ["en_ans", "en_answer", "answer_en", "key", "correct", "correct_answer", "answer"]
    EN_EX  = ["en_explanation", "explanation_en", "en_exp", "explanation", "reason"]

    EN_AA  = ["en_a", "opt_a", "option_a", "a"]
    EN_BB  = ["en_b", "opt_b", "option_b", "b"]
    EN_CC  = ["en_c", "opt_c", "option_c", "c"]
    EN_DD  = ["en_d", "opt_d", "option_d", "d"]
    EN_MERGED = ["en_options", "options_en", "options", "choices", "option_list"]

    # ---- STRICT per-language extraction (no cross fallback) ----
    ta_q   = _first_nonempty(df, idx, TA_Q)  or "—"
    ta_ans = _first_nonempty(df, idx, TA_A)  or "—"
    ta_ex  = _first_nonempty(df, idx, TA_EX) or "—"
    ta_ops = _opts_from_row(df, idx, TA_AA, TA_BB, TA_CC, TA_DD, TA_MERGED) or "—"

    en_q   = _first_nonempty(df, idx, EN_Q)  or "—"
    en_ans = _first_nonempty(df, idx, EN_A)  or "—"
    en_ex  = _first_nonempty(df, idx, EN_EX) or "—"
    en_ops = _opts_from_row(df, idx, EN_AA, EN_BB, EN_CC, EN_DD, EN_MERGED) or "—"

    # ---- render the two reference cards ----
    st.markdown(
        f"""
<div class="ta-card">
  <span class="pill ta">தமிழ் மூலப் பதிப்பு</span>
  <p><b>Q:</b> {ta_q}</p>
  <p><b>Options (A–D):</b> {ta_ops}</p>
  <p><b>Answer:</b> {ta_ans}</p>
  <p><b>Explanation:</b> {ta_ex}</p>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="en-card">
  <span class="pill en">English Version</span>
  <p><b>Q:</b> {en_q}</p>
  <p><b>Options (A–D):</b> {en_ops}</p>
  <p><b>Answer:</b> {en_ans}</p>
  <p><b>Explanation:</b> {en_ex}</p>
</div>
        """,
        unsafe_allow_html=True,
    )

    return True
