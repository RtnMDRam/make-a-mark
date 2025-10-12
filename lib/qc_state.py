# lib/qc_state.py
import math, ast, re
import streamlit as st

# ===== CSS (strong, collision-proof) =====
_QC_CSS = """
<style>
:root{
  /* each reference block height in viewport %; 22+22 ≈ 44% total */
  --ref-vh: 22;
  --line: 1px;
  --line-top: #63d063;   /* divider above Tamil */
  --line-mid: #4f92ff;   /* divider between Tamil & English */
}

/* tighten the app chrome a bit */
.block-container{padding-top:10px !important; padding-bottom:10px !important;}

.qc-title{font-size:12px !important; font-weight:700 !important; line-height:1 !important; margin:0 0 4px 0 !important; color:#cfcfcf !important;}

.qc-edit{margin:0 0 6px 0 !important;}

.qc-ref{
  font-size:12px !important; line-height:1.12 !important; margin:0 !important; padding:0 !important;
  height: calc(var(--ref-vh) * 1vh) !important;   /* hard height, not max-height */
  overflow:auto !important; white-space:normal !important; word-break:break-word !important;
}
.qc-ref p, .qc-ref ul, .qc-ref ol{margin:2px 0 !important;}
.qc-ref ul, .qc-ref ol{padding-left:16px !important; margin-left:16px !important;}

.qc-hr{height:var(--line) !important; border:0 !important; margin:6px 0 !important;}
.qc-hr.top{background:var(--line-top) !important;}  /* between SME & Tamil */
.qc-hr.mid{background:var(--line-mid) !important;}  /* between Tamil & English */
</style>
"""

# ===== helpers =====
def _s(x):
    if x is None: return ""
    if isinstance(x, float) and math.isnan(x): return ""
    return str(x).strip()

def _clean(s: str) -> str:
    if not s: return ""
    # flatten hard wraps from source so English/Tamil read continuously
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
    except Exception:
        pass
    if "|" in s: parts = [p.strip() for p in s.split("|")]
    elif "," in s: parts = [p.strip() for p in s.split(",")]
    else: parts = [p.strip(" .)") for p in re.split(r"\d+\)\s*", s) if p.strip()]
    return [p for p in parts if p]

def _fmt_opts(opts): return "—" if not opts else " | ".join(f"{i}) {o}" for i,o in enumerate(opts,1))

# Column maps (accept both short and descriptive headers)
SHORT_EN = ["en.q","en.o","en.a","en.e"]
LONG_EN  = {"en.q":"question","en.o":"questionOptions","en.a":"answers","en.e":"explanation"}
TA_MAPS  = {
    "ta.q":["கேள்வி","வினா","தமிழ் கேள்வி"],
    "ta.o":["விருப்பங்கள் (A–D)","விருப்பங்கள் (A-D)","விருப்பங்கள்"],
    "ta.a":["பதில்"],
    "ta.e":["விளக்கம்"],
}

def _maps(df):
    cols=list(df.columns); low=[c.lower().strip() for c in cols]
    en={}
    if all(c in cols for c in SHORT_EN):
        en={c:c for c in SHORT_EN}
    elif all(LONG_EN[c] in cols for c in SHORT_EN):
        en={k:LONG_EN[k] for k in SHORT_EN}
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

# ===== sections =====
def _editor_tamil():
    st.markdown('<div class="qc-title">SME Panel / ஆசிரியர் அங்கீகாரம் வழங்கும் பகுதி</div>', unsafe_allow_html=True)
    st.text_area(label="", value="", height=340, label_visibility="collapsed")

def _ta_ref():
    st.markdown('<div class="qc-title">தமிழ் மூலப் பதிவு</div>', unsafe_allow_html=True)
    row,en,ta=_get_row()
    if row is None or not ta:
        st.markdown('<div class="qc-ref">Upload a bilingual file and press <b>Load</b>.</div>', unsafe_allow_html=True); return
    q=_clean(_s(row[ta["ta.q"]]))
    o=_fmt_opts(_parse_options(row[ta["ta.o"]]))
    a=_clean(_s(row[ta["ta.a"]]))
    e=_clean(_s(row[ta["ta.e"]]))
    st.markdown(
        f'<div class="qc-ref">'
        f'<p><strong>கேள்வி :</strong> {q}</p>'
        f'<p><strong>விருப்பங்கள் (A–D) :</strong> {o}</p>'
        f'<p><strong>பதில் :</strong> {a}</p>'
        f'<p><strong>விளக்கம் :</strong> {e}</p>'
        f'</div>', unsafe_allow_html=True)

def _en_ref():
    st.markdown('<div class="qc-title">English Version</div>', unsafe_allow_html=True)
    row,en,ta=_get_row()
    if row is None or not en:
        st.markdown('<div class="qc-ref">English columns not found in the file.</div>', unsafe_allow_html=True); return
    q=_clean(_s(row[en["en.q"]]))
    o=_fmt_opts(_parse_options(row[en["en.o"]]))
    a=_clean(_s(row[en["en.a"]]))
    e=_clean(_s(row[en["en.e"]]))
    st.markdown(
        f'<div class="qc-ref">'
        f'<p><strong>Q :</strong> {q}</p>'
        f'<p><strong>Options (A–D) :</strong> {o}</p>'
        f'<p><strong>Answer :</strong> {a}</p>'
        f'<p><strong>Explanation :</strong> {e}</p>'
        f'</div>', unsafe_allow_html=True)

# ===== main public function =====
def render_reference_and_editor():
    st.markdown(_QC_CSS, unsafe_allow_html=True)

    # TOP: SME editor
    _editor_tamil()

    # (1) single divider BETWEEN editor and Tamil reference
    st.markdown('<hr class="qc-hr top">', unsafe_allow_html=True)

    # MIDDLE: Tamil reference (fixed ~22vh)
    _ta_ref()

    # (2) single divider BETWEEN Tamil & English
    st.markdown('<hr class="qc-hr mid">', unsafe_allow_html=True)

    # BOTTOM: English reference (fixed ~22vh)
    _en_ref()
