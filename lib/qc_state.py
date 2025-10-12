import re
import streamlit as st
import pandas as pd

# --------- cleaning helpers ----------
_TAG_RE = re.compile(r"</?[^>]+>")
_WS_RE  = re.compile(r"\s+")

def _clean_html(text: str) -> str:
    if text is None:
        return ""
    s = str(text)
    s = (s.replace("<br>", " ")
           .replace("<br/>", " ")
           .replace("<br />", " ")
           .replace("&nbsp;", " "))
    s = _TAG_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s

def _format_options(raw: str) -> str:
    if raw is None or str(raw).strip() == "":
        return "— | — | — | —"
    s = _clean_html(str(raw))

    # try common separators
    parts = None
    for sep in ["|", "||", "¶", "¦", "；", ";", " / ", "/", "\n", ","]:
        if sep in s:
            parts = [p.strip(" [](){}>") for p in s.split(sep)]
            break
    if parts is None:
        # JSON-like list?
        if "[" in s and "]" in s:
            s2 = s.strip("[]")
            parts = [p.strip(" '\"") for p in s2.split(",")]
        else:
            parts = [s]

    parts = [p.strip() for p in parts if p.strip()]
    while len(parts) < 4:
        parts.append("—")
    parts = parts[:4]
    return " | ".join(f"{i}) {parts[i-1]}" for i in range(1, 5))

def _dash_if_empty(x) -> str:
    s = _clean_html(x)
    return s if s else "—"

# --------- fuzzy header matcher ----------

def _norm(h: str) -> str:
    # normalize to compare headers; remove punctuation/parentheses and lower-case
    h = str(h or "")
    h = re.sub(r"\(.*?\)", "", h)   # drop things like (A–D)
    h = re.sub(r"[:：|/.,\-–—_]+", " ", h)
    h = _WS_RE.sub(" ", h).strip().lower()
    return h

ALIASES = {
    # English
    "en_q": [
        "question", "q", "ques", "question text", "en q", "en question"
    ],
    "en_opt": [
        "questionoptions", "options", "opts", "options a d", "options a-d",
        "en options", "en opt"
    ],
    "en_ans": ["answers", "answer", "ans", "en answer"],
    "en_ex":  ["explanation", "explain", "exp", "en explanation"],

    # Tamil (common labels you use)
    "ta_q":  ["கேள்வி", "வினா", "வினாக்கள்", "கேள்வி உரை"],
    "ta_opt":["விருப்பங்கள்", "விருப்பங்கள் a d", "விருப்பங்கள் a-d", "விருப்பம்"],
    "ta_ans":["பதில்", "விடை"],
    "ta_ex": ["விளக்கம்", "விளக்கங்கள்"],
}

def _find_col(df: pd.DataFrame, keys: list[str]) -> str | None:
    # try exact normalized matches first
    norm_map = {_norm(c): c for c in df.columns}
    for k in keys:
        nk = _norm(k)
        if nk in norm_map:
            return norm_map[nk]
    # fuzzy contains match
    for k in keys:
        nk = _norm(k)
        for n, orig in norm_map.items():
            if nk and nk in n:
                return orig
    return None

def _pick_fields(df: pd.DataFrame) -> dict:
    return {
        "en_q":   _find_col(df, ALIASES["en_q"]),
        "en_opt": _find_col(df, ALIASES["en_opt"]),
        "en_ans": _find_col(df, ALIASES["en_ans"]),
        "en_ex":  _find_col(df, ALIASES["en_ex"]),
        "ta_q":   _find_col(df, ALIASES["ta_q"]),
        "ta_opt": _find_col(df, ALIASES["ta_opt"]),
        "ta_ans": _find_col(df, ALIASES["ta_ans"]),
        "ta_ex":  _find_col(df, ALIASES["ta_ex"]),
    }

# --------- main renderer ----------

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
    cols = _pick_fields(df)

    # English
    en_q   = _dash_if_empty(row.get(cols["en_q"]))   if cols["en_q"]   else "—"
    en_opt = _format_options(row.get(cols["en_opt"])) if cols["en_opt"] else "— | — | — | —"
    en_ans = _dash_if_empty(row.get(cols["en_ans"])) if cols["en_ans"] else "—"
    en_ex  = _dash_if_empty(row.get(cols["en_ex"]))  if cols["en_ex"]  else "—"

    # Tamil
    ta_q   = _dash_if_empty(row.get(cols["ta_q"]))   if cols["ta_q"]   else "—"
    ta_opt = _format_options(row.get(cols["ta_opt"])) if cols["ta_opt"] else "— | — | — | —"
    ta_ans = _dash_if_empty(row.get(cols["ta_ans"])) if cols["ta_ans"] else "—"
    ta_ex  = _dash_if_empty(row.get(cols["ta_ex"]))  if cols["ta_ex"]  else "—"

    # Tamil card (green)
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

    # English card (blue)
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
