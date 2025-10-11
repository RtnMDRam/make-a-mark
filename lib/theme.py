import streamlit as st

CSS_LIGHT = """
<style>
:root{
  --bg:#ffffff; --text:#202020; --border:#dcdcdc;
  --gloss-bg:#EFEFEF; --gloss-b:#000000; --gloss-t:#222222;
  --en-bg:#E6F0FF; --en-b:#1F77B4; --en-t:#1B1B1B;
  --tao-bg:#E8F5E9; --tao-b:#2CA02C; --tao-t:#212121;
  --qc-bg:#FFF3F0; --qc-b:#E57373; --qc-t:#2A1A1A;
  --edit-bg:#FFFBE1; --edit-b:#FFBF00; --edit-t:#202020;
  --textarea-bg:#FAF9F6; --chip-on:#1F77B4; --chip-off:#dddddd;
}
html, body, .block-container { background:var(--bg); color:var(--text); }
.box{ border:2px solid var(--border); border-radius:12px; padding:1rem 1.1rem; margin:.8rem 0; }
.box h4{ margin:.6rem 0 .5rem; font-size:1.0rem; }
.box .fine{ font-size:.95rem; line-height:1.55rem; }
.box.gloss{ background:var(--gloss-bg); border-color:var(--gloss-b); color:var(--gloss-t); }
.box.en{    background:var(--en-bg);    border-color:var(--en-b);    color:var(--en-t); }
.box.tao{   background:var(--tao-bg);   border-color:var(--tao-b);   color:var(--tao-t); }
.box.qc{    background:var(--qc-bg);    border-color:var(--qc-b);    color:var(--qc-t); }
.box.edit{  background:var(--edit-bg);  border-color:var(--edit-b);  color:var(--edit-t); }
textarea, .stTextArea textarea { background:var(--textarea-bg)!important; }
.mono{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }
</style>
"""

CSS_NIGHT = """
<style>
:root{
  --bg:#111417; --text:#f1f1f1; --border:#3a3f45;
  --gloss-bg:#2a2e33; --gloss-b:#000000; --gloss-t:#e6e6e6;
  --en-bg:#213247; --en-b:#4da3ff; --en-t:#f1f6ff;
  --tao-bg:#1d3222; --tao-b:#6fd18a; --tao-t:#e9f7ed;
  --qc-bg:#412b2b; --qc-b:#ff8f8f; --qc-t:#ffecec;
  --edit-bg:#3a331d; --edit-b:#ffd166; --edit-t:#fff7d6;
  --textarea-bg:#2b2b2b; --chip-on:#7fb7ff; --chip-off:#555;
}
html, body, .block-container { background:var(--bg); color:var(--text); }
.box{ border:2px solid var(--border); border-radius:12px; padding:1rem 1.1rem; margin:.8rem 0; }
.box h4{ margin:.6rem 0 .5rem; font-size:1.0rem; }
.box .fine{ font-size:.95rem; line-height:1.55rem; }
.box.gloss{ background:var(--gloss-bg); border-color:var(--gloss-b); color:var(--gloss-t); }
.box.en{    background:var(--en-bg);    border-color:var(--en-b);    color:var(--en-t); }
.box.tao{   background:var(--tao-bg);   border-color:var(--tao-b);   color:var(--tao-t); }
.box.qc{    background:var(--qc-bg);    border-color:var(--qc-b);    color:var(--qc-t); }
.box.edit{  background:var(--edit-bg);  border-color:var(--edit-b);  color:var(--edit-t); }
textarea, .stTextArea textarea { background:var(--textarea-bg)!important; }
.mono{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }
</style>
"""

def inject_theme(night: bool, hide_sidebar: bool = True):
    st.markdown(CSS_NIGHT if night else CSS_LIGHT, unsafe_allow_html=True)
    if hide_sidebar:
        st.markdown(
            "<style>[data-testid='stSidebar']{display:none;} .main{padding-left:1rem!important}</style>",
            unsafe_allow_html=True,
        )

def panel(title: str, color_class: str, body_html: str):
    st.markdown(f"<div class='box {color_class}'><h4>{title}</h4><div class='fine'>{body_html}</div></div>",
                unsafe_allow_html=True)

def norm_html(s):
    return str(s or "").replace("\r\n", "\n").replace("\r", "").replace("\n", "<br>")
