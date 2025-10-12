import re
import streamlit as st
import pandas as pd

# ====================== helpers ======================

_TAG_RE = re.compile(r"</?[^>]+>")
_WS_RE  = re.compile(r"\s+")

def _is_tamil(s: str) -> bool:
    return bool(re.search(r"[\u0B80-\u0BFF]", str(s or "")))

def _norm(s: str) -> str:
    s = str(s or "")
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"[:：|/.,\-–—_]+", " ", s)
    s = _WS_RE.sub(" ", s).strip().lower()
    return s

def _clean_html(text) -> str:
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

def _dash_if_empty(x) -> str:
    s = _clean_html(x)
    return s if s else "—"

def _format_options(raw) -> str:
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

# ====================== column picking ======================

# Tamil keywords (in Tamil script)
TA_KEYS = {
    "q":   ["கேள்வி", "வினா", "வினாக்கள்"],
    "opt": ["விருப்பங்கள்", "விருப்பம்"],
    "ans": ["பதில்", "விடை"],
    "ex":  ["விளக்கம்", "விளக்கங்கள்"],
}

# English keywords (Latin script)
EN_KEYS = {
    "q":   ["question", "en question", "q", "ques", "question text"],
    "opt": ["questionoptions", "options", "options a d", "options a-d", "en options", "en opt"],
    "ans": ["answer", "answers", "ans", "en answer"],
    "ex":  ["explanation", "explain", "exp", "en explanation"],
}

# exact common headers for English files
EN_EXACT = {
    "q":   ["question"],
    "opt": ["questionOptions"],
    "ans": ["answers"],
    "ex":  ["explanation"],
}

def _find(df: pd.DataFrame, keys: list[str], require_tamil: bool | None) -> str | None:
    """
    Find a column whose header matches keys, restricted by script if asked.
    require_tamil=True  -> header must contain Tamil script
    require_tamil=False -> header must NOT contain Tamil script
    None                -> no restriction
    """
    cols = list(df.columns)
    # 1) exact normalized match
    norm_map = {_norm(c): c for c in cols
                if (require_tamil is None) or (_is_tamil(c) == require_tamil)}
    for k in keys:
        nk = _norm(k)
        if nk in norm_map:
            return norm_map[nk]
    # 2) contains match
    for k in keys:
        nk = _norm(k)
        for n, orig in norm_map.items():
            if nk and nk in n:
                return orig
    return None

def _pick_fields(df: pd.DataFrame) -> dict:
    # Prefer Tamil-only headers for Tamil; English-only (non-Tamil) for English
    ta_q   = _find(df, TA_KEYS["q"],   require_tamil=True)
    ta_opt = _find(df, TA_KEYS["opt"], require_tamil=True)
    ta_ans = _find(df, TA_KEYS["ans"], require_tamil=True)
    ta_ex  = _find(df, TA_KEYS["ex"],  require_tamil=True)

    en_q   = _find(df, EN_KEYS["q"],   require_tamil=False) or _find(df, EN_EXACT["q"],   require_tamil=False)
    en_opt = _find(df, EN_KEYS["opt"], require_tamil=False) or _find(df, EN_EXACT["opt"], require_tamil=False)
    en_ans = _find(df, EN_KEYS["ans"], require_tamil=False) or _find(df, EN_EXACT["ans"], require_tamil=False)
    en_ex  = _find(df, EN_KEYS["ex"],  require_tamil=False) or _find(df, EN_EXACT["ex"],  require_tamil=False)

    return {
        "ta_q": ta_q, "ta_opt": ta_opt, "ta_ans": ta_ans, "ta_ex": ta_ex,
        "en_q": en_q, "en_opt": en_opt, "en_ans": en_ans, "en_ex": en_ex,
    }

# ====================== main renderer ======================

def render_reference_and_editor():
    """
    Shows the two non-editable reference cards (Tamil on top, English below).
    Data: st.session_state.qc_df (DataFrame), st.session_state.qc_idx (int)
    """
    df: pd.DataFrame = st.session_state.get("qc_df")
    idx: int = int(st.session_state.get("qc_idx", 0))

    if df is None or df.empty:
        st.info("Upload a file and press Load to see reference cards.")
        return

    idx = max(0, min(idx, len(df) - 1))
    row = df.iloc[idx]
    cols = _pick_fields(df)

    # Tamil
    ta_q   = _dash_if_empty(row.get(cols["ta_q"]))   if cols["ta_q"]   else "—"
    ta_opt = _format_options(row.get(cols["ta_opt"])) if cols["ta_opt"] else "— | — | — | —"
    ta_ans = _dash_if_empty(row.get(cols["ta_ans"])) if cols["ta_ans"] else "—"
    ta_ex  = _dash_if_empty(row.get(cols["ta_ex"]))  if cols["ta_ex"]  else "—"

    # English
    en_q   = _dash_if_empty(row.get(cols["en_q"]))   if cols["en_q"]   else "—"
    en_opt = _format_options(row.get(cols["en_opt"])) if cols["en_opt"] else "— | — | — | —"
    en_ans = _dash_if_empty(row.get(cols["en_ans"])) if cols["en_ans"] else "—"
    en_ex  = _dash_if_empty(row.get(cols["en_ex"]))  if cols["en_ex"]  else "—"

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
