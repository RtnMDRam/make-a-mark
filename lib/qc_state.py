import re
import streamlit as st
import pandas as pd

# ---------------- formatting helpers ----------------

_TAG_RE = re.compile(r"</?[^>]+>")
_WS_RE  = re.compile(r"\s+")

def _clean_html(text: str) -> str:
    if text is None:
        return ""
    s = str(text)
    # convert common HTML breaks to spaces
    s = s.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
    s = s.replace("&nbsp;", " ")
    s = _TAG_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s

def _format_options(raw: str) -> str:
    """
    Accepts messy HTML / pipe / JSON-like option payloads and returns:
        "1) A | 2) B | 3) C | 4) D"
    If nothing found, returns em-dash placeholders.
    """
    if raw is None or str(raw).strip() == "":
        return "— | — | — | —"

    s = _clean_html(str(raw))

    # Try to split by common separators
    parts = None
    for sep in ["|", "||", "¶", "¦", "；", ";", " / ", "/", "\n", ","]:
        if sep in s:
            parts = [p.strip(" [](){}>").strip() for p in s.split(sep)]
            break

    if parts is None:
        # maybe JSON-like list?
        if "[" in s and "]" in s:
            s2 = s.strip("[]")
            parts = [p.strip(" '\"") for p in s2.split(",")]
        else:
            parts = [s]

    parts = [p for p in parts if p]  # remove empties
    # Keep max 4 for A–D; pad with em-dashes
    while len(parts) < 4:
        parts.append("—")
    parts = parts[:4]

    # prefix with 1..4)
    numbered = [f"{i}) {parts[i-1]}" for i in range(1, 5)]
    return " | ".join(numbered)

def _dash_if_empty(x) -> str:
    s = _clean_html(x)
    return s if s else "—"

# ---------------- public renderer ----------------

def render_reference_and_editor():
    """
    Shows the two non-editable reference cards (Tamil, then English).
    Uses st.session_state.qc_df and st.session_state.qc_idx.
    """
    df: pd.DataFrame = st.session_state.get("qc_df")
    idx: int = int(st.session_state.get("qc_idx", 0))

    if df is None or df.empty:
        st.info("Upload a file and press Load to see reference cards.")
        return

    idx = max(0, min(idx, len(df) - 1))
    row = df.iloc[idx]

    # English fields
    en_q   = _dash_if_empty(row.get("question"))
    en_opt = _format_options(row.get("questionOptions"))
    en_ans = _dash_if_empty(row.get("answers"))
    en_ex  = _dash_if_empty(row.get("explanation"))

    # Tamil fields
    ta_q   = _dash_if_empty(row.get("கேள்வி"))
    ta_opt = _format_options(row.get("விருப்பங்கள்"))
    ta_ans = _dash_if_empty(row.get("பதில்"))
    ta_ex  = _dash_if_empty(row.get("விளக்கம்"))

    # --- Tamil card (green) ---
    st.markdown(
        f"""
        <div class="ta-card">
          <div class="badge">தமிழ் மூலப் பதிப்பு</div>
          <p><span class="field-label">கேள்வி:</span> {ta_q}</p>
          <p><span class="field-label">விருப்பங்கள் (A–D):</span> {ta_opt}</p>
          <p><span class="field-label">பதில்:</span> {ta_ans}</p>
          <p><span class="field-label">விளக்கம்:</span> {ta_ex}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- English card (blue) ---
    st.markdown(
        f"""
        <div class="en-card">
          <div class="badge">English Version</div>
          <p><span class="field-label">Q:</span> {en_q}</p>
          <p><span class="field-label">Options (A–D):</span> {en_opt}</p>
          <p><span class="field-label">Answer:</span> {en_ans}</p>
          <p><span class="field-label">Explanation:</span> {en_ex}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
