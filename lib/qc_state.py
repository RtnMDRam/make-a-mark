import re
import streamlit as st
import pandas as pd

# ----------------- helpers -----------------

_TAG_RE = re.compile(r"</?[^>]+>")
_WS_RE  = re.compile(r"\s+")

def _has_tamil(s: str) -> bool:
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
            parts = [p.strip(" '\"") for p in s.strip("[]").split(",")]
        else:
            parts = [s]
    parts = [p.strip() for p in parts if p.strip()]
    while len(parts) < 4:
        parts.append("—")
    parts = parts[:4]
    return " | ".join(f"{i}) {parts[i-1]}" for i in range(1, 5))

# ----------------- column picking -----------------

# Tamil headers
TA_KEYS = {
    "q":   ["கேள்வி", "வினா", "வினாக்கள்"],
    "opt": ["விருப்பங்கள்", "விருப்பம்"],
    "ans": ["பதில்", "விடை"],
    "ex":  ["விளக்கம்", "விளக்கங்கள்"],
}

# English headers (Latin)
EN_EXACT = {
    "q":   ["question"],
    "opt": ["questionOptions", "question_options"],
    "ans": ["answers", "answer"],
    "ex":  ["explanation", "explain"],
}
# extra loose aliases (still Latin-only)
EN_ALIASES = {
    "q":   ["en question", "ques", "q", "question text"],
    "opt": ["options", "options a d", "options a-d", "en options", "en opt"],
    "ans": ["en answer", "ans"],
    "ex":  ["en explanation", "exp"],
}

def _find_strict(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Match only among NON-Tamil headers."""
    latin_cols = [c for c in df.columns if not _has_tamil(c)]
    norm_map = {_norm(c): c for c in latin_cols}
    # exact/normalized
    for k in candidates:
        nk = _norm(k)
        if nk in norm_map:
            return norm_map[nk]
    # contains
    for k in candidates:
        nk = _norm(k)
        for n, orig in norm_map.items():
            if nk and nk in n:
                return orig
    return None

def _find_tamil(df: pd.DataFrame, candidates: list[str]) -> str | None:
    ta_cols = [c for c in df.columns if _has_tamil(c)]
    norm_map = {_norm(c): c for c in ta_cols}
    for k in candidates:
        nk = _norm(k)
        if nk in norm_map:
            return norm_map[nk]
    for k in candidates:
        nk = _norm(k)
        for n, orig in norm_map.items():
            if nk and nk in n:
                return orig
    return None

def _pick_fields(df: pd.DataFrame) -> dict:
    # Tamil: must pick Tamil-script headers
    ta_q   = _find_tamil(df, TA_KEYS["q"])
    ta_opt = _find_tamil(df, TA_KEYS["opt"])
    ta_ans = _find_tamil(df, TA_KEYS["ans"])
    ta_ex  = _find_tamil(df, TA_KEYS["ex"])

    # English: STRICT — must pick non-Tamil headers only
    en_q   = _find_strict(df, EN_EXACT["q"])   or _find_strict(df, EN_ALIASES["q"])
    en_opt = _find_strict(df, EN_EXACT["opt"]) or _find_strict(df, EN_ALIASES["opt"])
    en_ans = _find_strict(df, EN_EXACT["ans"]) or _find_strict(df, EN_ALIASES["ans"])
    en_ex  = _find_strict(df, EN_EXACT["ex"])  or _find_strict(df, EN_ALIASES["ex"])

    return {
        "ta_q": ta_q, "ta_opt": ta_opt, "ta_ans": ta_ans, "ta_ex": ta_ex,
        "en_q": en_q, "en_opt": en_opt, "en_ans": en_ans, "en_ex": en_ex,
    }

# ----------------- main renderer -----------------

def render_reference_and_editor():
    df: pd.DataFrame = st.session_state.get("qc_df")
    idx: int = int(st.session_state.get("qc_idx", 0))

    if df is None or df.empty:
        st.info("Upload a file and press Load to see reference cards.")
        return

    idx = max(0, min(idx, len(df) - 1))
    row = df.iloc[idx]
    cols = _pick_fields(df)

    # Tamil values
    ta_q   = _dash_if_empty(row.get(cols["ta_q"]))    if cols["ta_q"]   else "—"
    ta_opt = _format_options(row.get(cols["ta_opt"])) if cols["ta_opt"] else "— | — | — | —"
    ta_ans = _dash_if_empty(row.get(cols["ta_ans"]))  if cols["ta_ans"] else "—"
    ta_ex  = _dash_if_empty(row.get(cols["ta_ex"]))   if cols["ta_ex"]  else "—"

    # English values (strict + script safety)
    def _safe_en(val):
        s = _dash_if_empty(val)
        # *** Never show Tamil in English card ***
        return "—" if _has_tamil(s) else s

    en_q   = _safe_en(row.get(cols["en_q"]))    if cols["en_q"]   else "—"
    en_opt = _safe_en(_format_options(row.get(cols["en_opt"]))) if cols["en_opt"] else "— | — | — | —"
    en_ans = _safe_en(row.get(cols["en_ans"]))  if cols["en_ans"] else "—"
    en_ex  = _safe_en(row.get(cols["en_ex"]))   if cols["en_ex"]  else "—"

    # Tamil card
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

    # English card
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
