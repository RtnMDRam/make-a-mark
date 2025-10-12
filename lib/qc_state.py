# --- helpers ---------------------------------------------------------------

import re
import pandas as pd
import streamlit as st

def _norm(s: str) -> str:
    """normalize a header/value for robust matching"""
    if s is None:
        return ""
    s = str(s)
    s = re.sub(r"<[^>]+>", " ", s)          # drop simple html tags
    s = s.replace("\xa0", " ")              # nbsp
    s = s.strip()
    return s

def _norm_hdr(s: str) -> str:
    """normalize header names for matching"""
    s = _norm(s).lower()
    # collapse spaces and punctuation
    s = re.sub(r"[\s\-\_\/\:\(\)]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _cols_detect(df: pd.DataFrame) -> dict:
    """
    Detect English (en.*) and Tamil (ta.*) columns from many possible header names.
    Returns a dict with keys: en.q, en.o, en.a, en.e, ta.q, ta.o, ta.a, ta.e (missing keys omitted).
    """
    # Build normalized header map: norm_name -> real_name
    hdr_map = { _norm_hdr(c): c for c in df.columns }

    # Known variants for each target key
    VARS = {
        # English
        "en.q": ["en q", "q", "question", "eng question", "english question"],
        "en.o": ["en o", "o", "options", "opts", "choices", "questionoptions", "options a d", "english options"],
        "en.a": ["en a", "a", "answer", "answers", "correct answer", "english answer"],
        "en.e": ["en e", "e", "explanation", "exp", "english explanation"],

        # Tamil (we'll keep them optional for now)
        "ta.q": ["ta q", "கேள்வி", "tamil question"],
        "ta.o": ["ta o", "விருப்பங்கள்", "விருப்பங்கள் a d", "tamil options"],
        "ta.a": ["ta a", "பதில்", "tamil answer"],
        "ta.e": ["ta e", "விளக்கம்", "tamil explanation"],
    }

    found = {}
    for key, candidates in VARS.items():
        for cand in candidates:
            norm = _norm_hdr(cand)
            if norm in hdr_map:
                found[key] = hdr_map[norm]
                break

    return found

def _get_cell(df: pd.DataFrame, row_idx: int, col_name: str) -> str:
    """Safe cell fetch as text, cleaning simple html / whitespace."""
    try:
        val = df.at[row_idx, col_name]
    except Exception:
        return ""
    return _norm(val)

def render_boxes_with_content():
    """
    - Expects st.session_state.qc_df (DataFrame) and st.session_state.qc_idx (int)
    - Fills English box now (Tamil later). Shows a gentle note only if English columns missing.
    """
    df: pd.DataFrame = st.session_state.get("qc_df")
    idx: int = int(st.session_state.get("qc_idx", 0))

    if df is None or df.empty:
        return

    # Detect columns
    cols = _cols_detect(df)

    # Build English block (use empty strings if not present)
    en_q = _get_cell(df, idx, cols["en.q"]) if "en.q" in cols else ""
    en_o = _get_cell(df, idx, cols["en.o"]) if "en.o" in cols else ""
    en_a = _get_cell(df, idx, cols["en.a"]) if "en.a" in cols else ""
    en_e = _get_cell(df, idx, cols["en.e"]) if "en.e" in cols else ""

    # Tamil (optional for this step)
    ta_q = _get_cell(df, idx, cols["ta.q"]) if "ta.q" in cols else ""
    ta_o = _get_cell(df, idx, cols["ta.o"]) if "ta.o" in cols else ""
    ta_a = _get_cell(df, idx, cols["ta.a"]) if "ta.a" in cols else ""
    ta_e = _get_cell(df, idx, cols["ta.e"]) if "ta.e" in cols else ""

    # If English is missing entirely, show a small note (bottom of page)
    missing_en = [k for k in ["en.q","en.o","en.a","en.e"] if k not in cols]
    if len(missing_en) == 4:
        st.info("Could not find English columns. Expected something like: "
                "`question`, `questionOptions`, `answers`, `explanation` "
                "(or en.q / en.o / en.a / en.e). Please check the header row.")
        return

    # ---- Render the three boxes (we already have the containers created above) ----
    # They’re just markdown right now—fill content with bold labels, respecting your compact style
    # Tamil (middle)
    with st.container():
        st.markdown(
            f"""
<div class="card ta-card">
  <div class="row"><div class="label">தமிழ் மூலப் பதிப்பு</div></div>
  <div class="row"><div>கேள்வி : {ta_q or "—"}</div></div>
  <div class="row"><div>விருப்பங்கள் (A–D) : {ta_o or "—"}</div></div>
  <div class="row"><div>பதில் : {ta_a or "—"}</div></div>
  <div class="row"><div>விளக்கம் : {ta_e or "—"}</div></div>
</div>
""",
            unsafe_allow_html=True,
        )

    # English (bottom)
    with st.container():
        st.markdown(
            f"""
<div class="card en-card">
  <div class="row"><div class="label">English Version</div></div>
  <div class="row"><div>Q : {en_q or "—"}</div></div>
  <div class="row"><div>Options (A–D) : {en_o or "—"}</div></div>
  <div class="row"><div>Answer : {en_a or "—"}</div></div>
  <div class="row"><div>Explanation : {en_e or "—"}</div></div>
</div>
""",
            unsafe_allow_html=True,
        )
