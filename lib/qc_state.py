# lib/qc_state.py  — simple dividers + 20vh + 20vh for TA/EN
import math, ast, re
import streamlit as st

# ---------- CSS ----------
_MM_CSS = """
<style>
:root{
  --mm-ref-vh: 20;               /* each reference block = 20vh (TA + EN ≈ 40%) */
  --mm-line: 1px;
  --mm-line-color-top: #6bd36b;  /* divider above Tamil reference (between SME & TA) */
  --mm-line-color-mid: #5aa3ff;  /* divider between Tamil & English */
}
.block-container{padding-top:10px;padding-bottom:10px;}
.mm-title{font-size:12px;font-weight:700;line-height:1;margin:0 0 4px 0;color:#cfcfcf;}
.mm-edit{margin:0 0 6px 0;}
.mm-ref{
  font-size:12px; line-height:1.12; margin:0; padding:0;
  max-height: calc(var(--mm-ref-vh) * 1vh);
  overflow:auto; white-space:normal; word-break:break-word;
}
.mm-ref p, .mm-ref ul, .mm-ref ol{margin:2px 0 !important;}
.mm-ref ul, .mm-ref ol{padding-left:16px;margin-left:16px !important;}
.mm-hr-top{height:var(--mm-line);background:var(--mm-line-color-top);border:0;margin:6px 0;}
.mm-hr-mid{height:var(--mm-line);background:var(--mm-line-color-mid);border:0;margin:6px 0;}
</style>
"""

# ---------- tiny helpers ----------
def _s(x):
    if x is None: return ""
    if isinstance(x, float) and math.isnan(x): return ""
    return str(x).strip()

def _clean(s: str) -> str:
    if not s: return ""
    s = s.replace("\\r\\n"," ").replace("\\n"," ").replace("\\r"," ")
    s = s.replace("\r\n"," ").replace("\n"," ").replace("\r"," ")
    return re.sub(r"[ \t]{2,}", " ", s).strip()

def _parse_options(val):
    if val is None: return []
    if isinstance(val, list): return [_s(v) for v in val if _s(v)]
    s = _s(val)
    try:
        obj = ast.literal_eval(s)
        if isinstance(obj, list): return [_s(v) for v in obj if _s(v)]
    except Exception: pass
    if "|" in s: parts = [p.strip() for p in s.split("|")]
    elif "," in s: parts = [p.strip() for p in s.split(",")]
    else: parts = [p.strip(" .)") for p in re.split(r"\d+\)\s*", s) if p.strip()]
    return [p for p in parts if p]

def _fmt_opts(opts): return "—" if not opts else " | ".join(f"{i}) {o}" for i,o in enumerate(opts,1))

# column resolution (accepts short or descriptive headers)
SHORT_EN = ["en.q","en.o","en.a","en.e"]
LONG_EN = {"en.q":"question","en.o":"questionOptions","en.a":"answers","en.e":"explanation"}
TA_MAPS = {
    "ta.q":["கேள்வி","வினா","தமிழ் கேள்வி"],
    "ta.o":["விருப்பங்கள்","விருப்பங்கள் (A–D)","விருப்பங்கள் (A-D)"],
    "ta.a":["பதில்"],
    "ta.e":["விளக்கம்"],
}

def _maps(df):
    cols=list(df.columns); low=[c.lower().strip() for c in cols]
    en={}
    if all(c in cols for c in SHORT_EN): en={c:c for c in SHORT_EN}
    elif all(LONG_EN[c] in cols for c in SHORT_EN): en={k:LONG_EN[k] for k in SHORT_EN}
    ta={}
    for key, labels in TA_MAPS.items():
        for lab in labels:
            if lab.lower() in low:
                ta[key]=cols[low.index(lab.lower())]; break
    return en, ta

def _get_row():
    df=st.session_state.get("qc_df")
    if df is None or df.empty: return None,{},{}
    en, ta = _maps(df)
    i=int(st.session_state.get("qc_idx",0))
    i = max(0, min(i, len(df)-1))
    return df.iloc[i], en, ta

# ---------- per-section render ----------
def _editor_tamil():
    st.markdown('<div class="mm-title">SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி</div>', unsafe_allow_html=True)
    st.text_area(label="", value="", height=340, label_visibility="collapsed")

def _ta_ref():
    st.markdown('<div class="mm-title">தமிழ் மூலப் பதிவு</div>', unsafe_allow_html=True)
    row,en,ta=_get_row()
    if row is None or not ta:
        st.markdown('<div class="mm-ref">Upload a bilingual file and press <b>Load</b>.</div>', unsafe_allow_html=True); return
    q=_clean(_s(row[ta["ta.q"]]))
    o=_fmt_opts(_parse_options(row[ta["ta.o"]]))
    a=_clean(_s(row[ta["ta.a"]]))
    e=_clean(_s(row[ta["ta.e"]]))
    st.markdown(
        f'<div class="mm-ref">'
        f'<p><strong>கேள்வி :</strong> {q}</p>'
        f'<p><strong>விருப்பங்கள் (A–D) :</strong> {o}</p>'
        f'<p><strong>பதில் :</strong> {a}</p>'
        f'<p><strong>விளக்கம் :</strong> {e}</p>'
        f'</div>', unsafe_allow_html=True)

def _en_ref():
    st.markdown('<div class="mm-title">English Version</div>', unsafe_allow_html=True)
    row,en,ta=_get_row()
    if row is None or not en:
        st.markdown('<div class="mm-ref">English columns not found in the file.</div>', unsafe_allow_html=True); return
    q=_clean(_s(row[en["en.q"]]))
    o=_fmt_opts(_parse_options(row[en["en.o"]]))
    a=_clean(_s(row[en["en.a"]]))
    e=_clean(_s(row[en["en.e"]]))
    st.markdown(
        f'<div class="mm-ref">'
        f'<p><strong>Q :</strong> {q}</p>'
        f'<p><strong>Options (A–D) :</strong> {o}</p>'
        f'<p><strong>Answer :</strong> {a}</p>'
        f'<p><strong>Explanation :</strong> {e}</p>'
        f'</div>', unsafe_allow_html=True)

# ---------- public entry ----------
def render_reference_and_editor():
    st.markdown(_MM_CSS, unsafe_allow_html=True)

    # 1) SME editable (top)
    _editor_tamil()

    # 2) single thin divider BETWEEN editor and Tamil reference
    st.markdown('<hr class="mm-hr-top">', unsafe_allow_html=True)

    # 3) Tamil reference (≈20vh)
    _ta_ref()

    # 4) single thin divider BETWEEN Tamil & English
    st.markdown('<hr class="mm-hr-mid">', unsafe_allow_html=True)

    # 5) English reference (≈20vh)
    _en_ref()
