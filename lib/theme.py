# lib/theme.py
import streamlit as st

CSS_BASE = """
<style>
:root{
  --bg:#ffffff; --text:#202020; --border:#dcdcdc;
  --gloss-bg:#EFEFEF; --gloss-b:#000;     --gloss-t:#222;
  --en-bg:#E6F0FF;   --en-b:#1F77B4;      --en-t:#1B1B1B;
  --tao-bg:#E8F5E9;  --tao-b:#2CA02C;      --tao-t:#212121;
  --qc-bg:#FFF3F0;   --qc-b:#E57373;       --qc-t:#2A1A1A;
  --edit-bg:#FFF8E1; --edit-b:#FFBF00;     --edit-t:#202020;
  --textarea-bg:#FAF9F6;
  --chip-on:#1F77B4; --chip-off:#ddd;
}
html, body, .block-container { background:var(--bg); color:var(--text); }
.block-container { padding-top:.6rem; padding-bottom:2rem; max-width:1200px; margin:0 auto; }
.box { border:2px solid var(--border); border-radius:12px; padding:.8rem 1rem; margin:.7rem 0; }
.box h4 { margin:.15rem 0 .55rem; font-size:1.0rem; }  /* tighter headings */
.box .fine { font-size:.95rem; line-height:1.45rem; }
.box .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }
.box.gloss { background:var(--gloss-bg); border-color:var(--gloss-b); color:var(--gloss-t); }
.box.en    { background:var(--en-bg);    border-color:var(--en-b);    color:var(--en-t); }
.box.tao   { background:var(--tao-bg);   border-color:var(--tao-b);   color:var(--tao-t); }
.box.qc    { background:var(--qc-bg);    border-color:var(--qc-b);    color:var(--qc-t); }
.box.edit  { background:var(--edit-bg);  border-color:var(--edit-b);  color:var(--edit-t); }
textarea, .stTextArea textarea { background:var(--textarea-bg) !important; }
.idtag{display:inline-block;border:1px solid var(--border);border-radius:8px;padding:.3rem .6rem;}
.tip{color:#666; font-size:.92rem; padding:.45rem .6rem;}
/* Remove top-right Streamlit toolbar + star + share */
header [data-testid="stActionButtonIcon"], 
header [data-testid="StyledFullScreenButton"],
header [data-testid="stToolbar"],
header svg[aria-label="star"] { display:none !important; }
/* Slightly reduce gaps around expanders */
[data-testid="stExpander"] { margin:.4rem 0; }
</style>
"""

CSS_COMPACT = """
<style>
.block-container { max-width: 1500px; padding-top:.4rem; }
</style>
"""

CSS_NIGHT = """
<style>
:root{
  --bg:#111417; --text:#f1f1f1; --border:#3a3f45;
  --gloss-bg:#2a2e33; --gloss-b:#000;   --gloss-t:#e6e6e6;
  --en-bg:#213247;    --en-b:#4da3ff;   --en-t:#f1f6ff;
  --tao-bg:#1d3222;   --tao-b:#6fd18a;  --tao-t:#e9f7ed;
  --qc-bg:#412b2b;    --qc-b:#ff8f8f;   --qc-t:#ffecec;
  --edit-bg:#3a331d;  --edit-b:#ffd166; --edit-t:#fff7d6;
  --textarea-bg:#2b2b2b;
}
</style>
"""

CSS_HIDE_SIDEBAR = """
<style>
/* Hide left app menu and reclaim width */
section[data-testid="stSidebar"] { display:none !important; }
div[data-testid="stSidebarNav"] { display:none !important; }
@media (min-width: 0px){
  div.block-container { padding-left: 1rem; padding-right: 1rem; }
}
</style>
"""

def apply_theme(night: bool=False, *, hide_sidebar: bool=False, compact: bool=True):
    st.markdown(CSS_BASE, unsafe_allow_html=True)
    if compact: st.markdown(CSS_COMPACT, unsafe_allow_html=True)
    if night:   st.markdown(CSS_NIGHT, unsafe_allow_html=True)
    if hide_sidebar: st.markdown(CSS_HIDE_SIDEBAR, unsafe_allow_html=True)
