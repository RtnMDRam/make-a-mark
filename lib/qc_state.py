# lib/qc_state.py
import ast
import math
import re
import streamlit as st

# ================= CSS (single-line borders, compact spacing) =================
_LAYOUT_CSS = """
<style>
.block-container{padding-top:12px;padding-bottom:12px;}
.section{border:2px solid #2f61c1;border-radius:12px;padding:14px 16px;margin-top:12px;}
.section.ta{border-color:#2e7d32;}  /* Tamil = green */
.section.en{border-color:#2f61c1;}  /* English = blue */
.section.ed{border-color:#2f61c1;}  /* SME edit = blue  */
.section .title{font-size:13px;font-weight:700;margin-bottom:6px;line-height:1.25;}
.note{opacity:.7;font-size:13px;margin:2px 0 2px;}
</style>
"""

# ================= Helpers =================
def _section_open(cls: str, title: str) -> None:
    st.markdown(f'<div class="section {cls}"><div class="title">{title}</div>', unsafe_allow_html=True)

def _section_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)

def _s(x):
    """safe to string, strip, drop NaN/None"""
    if x is None:
        return ""
    if isinstance(x, float) and math.isnan(x):
        return ""
    return str(x).strip()

def _clean_newlines(s: str) -> str:
    """collapse \\r\\n, \\n\\n etc. to single paragraph breaks"""
    if not s:
        return s
    s = s.replace("\\r\\n", "\n").replace("\\r", "\n")
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s

def _parse_options(val):
    """Accept list, JSON-like list, or text delimited by | or , or numbered pieces."""
    if val is None:
        return []
    if isinstance(val, list):
        return [_s(v) for v in val if _s(v)]
    s = _s(val)
    if not s:
        return []
    # try literal list
    try:
        obj = ast.literal_eval(s)
        if isinstance(obj, list):
            return [_s(v) for v in obj if _s(v)]
    except Exception:
        pass
    # split heuristics
    if "|" in s:
        parts = [p.strip() for p in s.split("|")]
    elif "," in s:
        parts = [p.strip() for p in s.split(",")]
    else:
        # break "1) aaa 2) bbb" etc.
        parts = [p.strip(" .)") for p in re.split(r"\d+\)\s*", s) if p.strip()]
    return [p for p in parts if p]

def _fmt_options(opts):
    if not opts:
        return "—"
    return " | ".join(f"{i}) {o}" for i, o in enumerate(opts, 1))

# ================= Column detection =================
SHORT_EN = ["en.q", "en.o", "en.a", "en.e"]
SHORT_TA = ["ta.q", "ta.o", "ta.a", "ta.e"]

# Tamil header fallbacks (case-insensitive contains match)
TA_FALLBACKS = {
    "ta.q": [
        "கேள்வி", "வினா", "தமிழ் கேள்வி", "ta.question", "ta_q", "tamil_q"
    ],
    "ta.o": [
        "விருப்பங்கள்", "விருப்பங்கள் (A–D)", "விருப்பங்கள் (A-D)", "ta.options", "ta_o", "tamil_options"
    ],
    "ta.a": [
        "பதில்", "ta.answer", "ta_a", "tamil_answer"
    ],
    "ta.e": [
        "விளக்கம்", "ta.explanation", "ta_e", "tamil_explanation"
    ],
}

LONG_EN_MAP = {  # English long names
    "en.q": "question",
    "en.o": "questionOptions",
    "en.a": "answers",
    "en.e": "explanation",
}

def _norm(s: str) -> str:
    return s.strip().lower()

def _resolve_column_maps(df):
    cols = list(df.columns)
    norm_cols = [_norm(c) for c in cols]

    # ---- English ----
    en_map = {}
    if all(c in df.columns for c in SHORT_EN):
        en_map = {c: c for c in SHORT_EN}
    elif all(v in df.columns for v in LONG_EN_MAP.values()):
        en_map = {k: LONG_EN_MAP[k] for k in SHORT_EN}

    # ---- Tamil (short or fallbacks) ----
    ta_map = {}
    if all(c in df.columns for c in SHORT_TA):
        ta_map = {c: c for c in SHORT_TA}
    else:
        tmp = {}
        for key, patterns in TA_FALLBACKS.items():
            hit = None
            for pat in patterns:
                pat_norm = _norm(pat)
                for i, nc in enumerate(norm_cols):
                    if pat_norm in nc:  # contains is lenient and helps with mixed headers
                        hit = cols[i]
                        break
                if hit:
                    break
            if hit:
                tmp[key] = hit
        if len(tmp) == 4:
            ta_map = tmp

    return en_map, ta_map

def _get_row():
    df = st.session_state.get("qc_df", None)
    if df is None or df.empty:
        return None, {}, {}
    en_map, ta_map = _resolve_column_maps(df)
    idx = int(st.session_state.get("qc_idx", 0))
    if idx < 0 or idx >= len(df):
        idx = 0
        st.session_state["qc_idx"] = idx
    return df.iloc[idx], en_map, ta_map

# ================= Content renderers =================
def _editor_tamil():
    st.text_area("", "", height=340, label_visibility="collapsed")

def _render_ta_box():
    row, en_map, ta_map = _get_row()
    if row is None:
        st.markdown('<div class="note">Upload an Excel/CSV and press <b>Load</b>.</div>', unsafe_allow_html=True)
        return
    if not ta_map:
        st.markdown('<div class="note">Tamil columns not found. Expected <code>ta.q, ta.o, ta.a, ta.e</code> or headers like <b>கேள்வி / விருப்பங்கள் / பதில் / விளக்கம்</b>.</div>', unsafe_allow_html=True)
        return
    q = _clean_newlines(_s(row[ta_map["ta.q"]]))
    o = _fmt_options(_parse_options(row[ta_map["ta.o"]]))
    a = _clean_newlines(_s(row[ta_map["ta.a"]]))
    e = _clean_newlines(_s(row[ta_map["ta.e"]]))
    st.markdown(
        f"**கேள்வி :** {q}\n\n"
        f"**விருப்பங்கள் (A–D) :** {o}\n\n"
        f"**பதில் :** {a}\n\n"
        f"**விளக்கம் :** {e}\n"
    )

def _render_en_box():
    row, en_map, ta_map = _get_row()
    if row is None:
        st.markdown('<div class="note">Upload an Excel/CSV and press <b>Load</b>.</div>', unsafe_allow_html=True)
        return
    if not en_map:
        st.markdown('<div class="note">English columns not found. Expected <code>en.q, en.o, en.a, en.e</code> or <code>question, questionOptions, answers, explanation</code>.</div>', unsafe_allow_html=True)
        return
    q = _clean_newlines(_s(row[en_map["en.q"]]))
    o = _fmt_options(_parse_options(row[en_map["en.o"]]))
    a = _clean_newlines(_s(row[en_map["en.a"]]))
    e = _clean_newlines(_s(row[en_map["en.e"]]))
    st.markdown(
        f"**Q :** {q}\n\n"
        f"**Options (A–D) :** {o}\n\n"
        f"**Answer :** {a}\n\n"
        f"**Explanation :** {e}\n"
    )

# ================= Final layout renderer =================
def render_reference_and_editor():
    st.markdown(_LAYOUT_CSS, unsafe_allow_html=True)

    # TOP: SME Edit (Tamil)
    _section_open("ed", "SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி")
    _editor_tamil()
    _section_close()

    # MIDDLE: Tamil reference
    _section_open("ta", "தமிழ் மூலப் பதிவு")
    _render_ta_box()
    _section_close()

    # BOTTOM: English reference
    _section_open("en", "English Version")
    _render_en_box()
    _section_close()
