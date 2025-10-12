# lib/qc_state.py
import math, ast
import streamlit as st

# ==== CSS (layout + borders + compact headings) ==============================
_LAYOUT_CSS = """
<style>
.block-container{padding-top:12px;padding-bottom:12px;}
.section{border:2px solid #2f61c1;border-radius:12px;padding:12px 14px;margin:0;}
.section + .section{margin-top:8px;}     /* small fixed gap between boxes */
.section.ta{border-color:#2e7d32;}       /* Tamil reference = green */
.section.en{border-color:#2f61c1;}       /* English reference = blue */
.section.ed{border-color:#2f61c1;}       /* SME edit = blue */
.section .title{font-size:12px;font-weight:600;margin:0 0 4px 0;line-height:1;}
</style>
"""

# ==== helpers to open/close a bordered box ==================================
def _section_open(cls: str, title: str):
    st.markdown(f"""<div class="section {cls}"><div class="title">{title}</div>""",
                unsafe_allow_html=True)

def _section_close():
    st.markdown("</div>", unsafe_allow_html=True)

# ==== dataframe helpers ======================================================
_REQUIRED_EN = ["en.q", "en.o", "en.a", "en.e"]
_REQUIRED_TA = ["ta.q", "ta.o", "ta.a", "ta.e"]

# allow long EN names as an alternative
_ALT_EN_MAP = {
    "en.q": "question",
    "en.o": "questionOptions",
    "en.a": "answers",
    "en.e": "explanation",
}

def _get_df():
    df = st.session_state.get("qc_df", None)
    if df is None:
        st.info("No data loaded yet. Please upload a file and press **Load**.")
        return None

    cols = set(df.columns)
    colmap = {}

    # prefer short names if present
    if all(c in cols for c in _REQUIRED_EN + _REQUIRED_TA):
        for c in _REQUIRED_EN + _REQUIRED_TA:
            colmap[c] = c
    else:
        ok = True
        for short, longname in _ALT_EN_MAP.items():
            if longname in cols:
                colmap[short] = longname
            else:
                ok = False
        for c in _REQUIRED_TA:
            if c in cols:
                colmap[c] = c
            else:
                ok = False
        if not ok:
            st.warning("Could not find expected columns. Expected either "
                       "`en.q,en.o,en.a,en.e,ta.q,ta.o,ta.a,ta.e` OR "
                       "`question,questionOptions,answers,explanation` for English plus Tamil short form.")
            return None

    return df, colmap

def _get_row():
    out = _get_df()
    if out is None:
        return None, None, None
    df, colmap = out
    idx = int(st.session_state.get("qc_idx", 0))
    if idx < 0 or idx >= len(df):
        idx = 0
        st.session_state["qc_idx"] = idx
    row = df.iloc[idx]
    return row, colmap, idx

def _s(x):
    if x is None:
        return ""
    if isinstance(x, float) and math.isnan(x):
        return ""
    return str(x).strip()

def _parse_options(val):
    if val is None:
        return []
    if isinstance(val, list):
        return [_s(v) for v in val if _s(v)]
    s = _s(val)
    if not s:
        return []
    try:
        parsed = ast.literal_eval(s)
        if isinstance(parsed, list):
            return [_s(v) for v in parsed if _s(v)]
    except Exception:
        pass
    if "|" in s:
        parts = [p.strip() for p in s.split("|")]
    else:
        parts = [p.strip() for p in s.split(",")]
    return [p for p in parts if p]

def _fmt_options(opts):
    if not opts:
        return "—"
    return " | ".join([f"{i}) {o}" for i, o in enumerate(opts, 1)])

# ==== section bodies =========================================================
def _editor_tamil():
    # editable panel placeholder (kept empty for SME entry space)
    st.text_area("", "", height=280, label_visibility="collapsed")

def _reference_tamil():
    row, colmap, _ = _get_row()
    if row is None:
        return
    q = _s(row[colmap["ta.q"]])
    o = _fmt_options(_parse_options(row[colmap["ta.o"]]))
    a = _s(row[colmap["ta.a"]])
    e = _s(row[colmap["ta.e"]])
    st.markdown(
        f"**கேள்வி :** {q}\n\n"
        f"**விருப்பங்கள் (A–D) :** {o}\n\n"
        f"**பதில் :** {a}\n\n"
        f"**விளக்கம் :** {e}\n"
    )

def _reference_english():
    row, colmap, _ = _get_row()
    if row is None:
        return
    q = _s(row[colmap["en.q"]])
    o = _fmt_options(_parse_options(row[colmap["en.o"]]))
    a = _s(row[colmap["en.a"]])
    e = _s(row[colmap["en.e"]])
    st.markdown(
        f"**Q :** {q}\n\n"
        f"**Options (A–D) :** {o}\n\n"
        f"**Answer :** {a}\n\n"
        f"**Explanation :** {e}\n"
    )

# ==== final renderer (fixed order & single-line borders) =====================
def render_reference_and_editor():
    """
    1) TOP    : SME Edit (Tamil)     -> blue box
    2) MIDDLE : Tamil reference      -> green box
    3) BOTTOM : English reference    -> blue box
    """
    st.markdown(_LAYOUT_CSS, unsafe_allow_html=True)

    _section_open("ed", "SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி")
    _editor_tamil()
    _section_close()

    _section_open("ta", "தமிழ் மூலப் பதிவு")
    _reference_tamil()
    _section_close()

    _section_open("en", "English Version")
    _reference_english()
    _section_close()
