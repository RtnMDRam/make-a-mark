import re
import streamlit as st
import pandas as pd

# ---------- one-time CSS (keeps order + spacing stable) ----------
def _css_once():
    if st.session_state.get("_qc_css_done"):  # don’t re-inject
        return
    st.session_state["_qc_css_done"] = True
    st.markdown(
        """
        <style>
          .ta-card, .en-card{
            border-radius: 10px; padding:16px 18px; margin:0; 
          }
          .ta-card{ background:#eaf6e9; }
          .en-card{ background:#e8efff; margin-top:14px; } /* fixes the gap & keeps EN below */
          .badge{
            display:inline-block; background:#e9eef4; padding:4px 10px; 
            border-radius:12px; font-size:13px; color:#3b4a5a; margin-bottom:6px;
          }
          .field-label{ font-weight:700; }
          p{ margin:8px 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ---------- helpers ----------
_TAG_RE = re.compile(r"</?[^>]+>")
_WS_RE  = re.compile(r"\s+")

def _has_tamil(s: str) -> bool:
    return bool(re.search(r"[\u0B80-\u0BFF]", str(s or "")))

def _norm(s: str) -> str:
    s = str(s or "")
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"[:：|/.,\\-–—_]+", " ", s)
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
    # show as A/B/C/D lines like your screenshot
    return " | ".join(parts)

# ---------- header picking ----------
# Tamil headers
TA_MAP = {
    "q":   ["கேள்வி", "வினா", "வினாக்கள்"],
    "opt": ["விருப்பங்கள்", "விருப்பம்"],
    "ans": ["பதில்", "விடை"],
    "ex":  ["விளக்கம்", "விளக்கங்கள்"],
}

# English headers (Latin only)
EN_EXACT = {
    "q":   ["question"],
    "opt": ["questionOptions", "question_options"],
    "ans": ["answers", "answer"],
    "ex":  ["explanation", "explain"],
}
EN_ALIASES = {
    "q":   ["en question", "ques", "q", "question text"],
    "opt": ["options", "options a d", "options a-d", "en options", "en opt"],
    "ans": ["en answer", "ans"],
    "ex":  ["en explanation", "exp"],
}

def _find_from(df: pd.DataFrame, cols: list[str], *, tamil: bool) -> str | None:
    pool = [c for c in df.columns if _has_tamil(c) == tamil]
    norm = {_norm(c): c for c in pool}
    for k in cols:
        nk = _norm(k)
        if nk in norm:
            return norm[nk]
    for k in cols:
        nk = _norm(k)
        for n, orig in norm.items():
            if nk and nk in n:
                return orig
    return None

def _pick_fields(df: pd.DataFrame) -> dict:
    ta_q   = _find_from(df, TA_MAP["q"],   tamil=True)
    ta_opt = _find_from(df, TA_MAP["opt"], tamil=True)
    ta_ans = _find_from(df, TA_MAP["ans"], tamil=True)
    ta_ex  = _find_from(df, TA_MAP["ex"],  tamil=True)

    en_q   = _find_from(df, EN_EXACT["q"]  + EN_ALIASES["q"],   tamil=False)
    en_opt = _find_from(df, EN_EXACT["opt"]+ EN_ALIASES["opt"], tamil=False)
    en_ans = _find_from(df, EN_EXACT["ans"]+ EN_ALIASES["ans"], tamil=False)
    en_ex  = _find_from(df, EN_EXACT["ex"] + EN_ALIASES["ex"],  tamil=False)

    return dict(ta_q=ta_q, ta_opt=ta_opt, ta_ans=ta_ans, ta_ex=ta_ex,
                en_q=en_q, en_opt=en_opt, en_ans=en_ans, en_ex=en_ex)

# ---------- main renderer ----------
def render_reference_and_editor():
    _css_once()

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

    # English values (strict Latin, never show Tamil script)
    def _safe_en(val):
        s = _dash_if_empty(val)
        return "—" if _has_tamil(s) else s

    en_q   = _safe_en(row.get(cols["en_q"]))    if cols["en_q"]   else "—"
    en_opt = _safe_en(_format_options(row.get(cols["en_opt"]))) if cols["en_opt"] else "— | — | — | —"
    en_ans = _safe_en(row.get(cols["en_ans"]))  if cols["en_ans"] else "—"
    en_ex  = _safe_en(row.get(cols["en_ex"]))   if cols["en_ex"]  else "—"

    # ----- Tamil card (always first) -----
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

    # ----- English card (always second, fixed gap via CSS) -----
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
