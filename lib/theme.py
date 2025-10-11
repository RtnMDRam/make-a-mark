# lib/theme.py
import streamlit as st

CSS_LIGHT = """
<style>
:root{
  --bg:#ffffff; --text:#202020; --border:#dcdcdc;
  --gloss-bg:#EFEFEF; --gloss-b:#000;  --gloss-t:#222;
  --en-bg:#E6F0FF;   --en-b:#1F77B4;  --en-t:#1B1B1B;
  --tao-bg:#E8F5E9;  --tao-b:#2CA02C; --tao-t:#212121;
  --qc-bg:#FFF3F0;   --qc-b:#E57373;  --qc-t:#2A1A1A;
  --edit-bg:#FFF8E1; --edit-b:#FFBf00;--edit-t:#202020;
  --textarea-bg:#FAF9F6;
}
html, body, .block-container { background:var(--bg); color:var(--text); }
.box { border:2px solid var(--border); border-radius:12px; padding:1rem 1.1rem; margin:.8rem 0; }
.box h4 { margin:0 .5rem 0; font-size:1.0rem; }
.box .fine { font-size:.95rem; line-height:1.5rem; }
.box .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; font-size:1rem; line-height:1.6rem; }
.box.gloss{ background:var(--gloss-bg); border-color:var(--gloss-b); color:var(--gloss-t); }
.box.en   { background:var(--en-bg);    border-color:var(--en-b);    color:var(--en-t);   }
.box.tao  { background:var(--tao-bg);   border-color:var(--tao-b);   color:var(--tao-t);  }
.box.qc   { background:var(--qc-bg);    border-color:var(--qc-b);    color:var(--qc-t);   }
.box.edit { background:var(--edit-bg);  border-color:var(--edit-b);  color:var(--edit-t); }
textarea, .stTextArea textarea { background:var(--textarea-bg) !important; }
.idtag{display:inline-block;border:1px solid var(--border);border-radius:8px;padding:.25rem .6rem;font-weight:600;}
.tip{ color:#666; padding:.6rem 0; }
</style>
"""

CSS_NIGHT = """
<style>
:root{
  --bg:#111417; --text:#f1f1f1; --border:#3a3f45;
  --gloss-bg:#2a2e33; --gloss-b:#000;  --gloss-t:#e6e6e6;
  --en-bg:#213247;   --en-b:#4da3ff;  --en-t:#f1f6ff;
  --tao-bg:#1d3222;  --tao-b:#6fd18a; --tao-t:#e9f7ed;
  --qc-bg:#412b2b;   --qc-b:#ff8f8f;  --qc-t:#ffecec;
  --edit-bg:#3a331d; --edit-b:#ffd166;--edit-t:#fff7d6;
  --textarea-bg:#2b2b2b;
}
html, body, .block-container { background:var(--bg); color:var(--text); }
.box { border:2px solid var(--border); border-radius:12px; padding:1rem 1.1rem; margin:.8rem 0; }
.box h4 { margin:0 .5rem 0; font-size:1.0rem; }
.box .fine { font-size:.95rem; line-height:1.5rem; }
.box .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; font-size:1rem; line-height:1.6rem; }
.box.gloss{ background:var(--gloss-bg); border-color:var(--gloss-b); color:var(--gloss-t); }
.box.en   { background:var(--en-bg);    border-color:var(--en-b);    color:var(--en-t);   }
.box.tao  { background:var(--tao-bg);   border-color:var(--tao-b);   color:var(--tao-t);  }
.box.qc   { background:var(--qc-bg);    border-color:var(--qc-b);    color:var(--qc-t);   }
.box.edit { background:var(--edit-bg);  border-color:var(--edit-b);  color:var(--edit-t); }
textarea, .stTextArea textarea { background:var(--textarea-bg) !important; }
.idtag{display:inline-block;border:1px solid var(--border);border-radius:8px;padding:.25rem .6rem;font-weight:600;}
.tip{ color:#bbb; padding:.6rem 0; }
</style>
"""

def apply_theme(night: bool, hide_sidebar: bool=False):
    """Inject CSS and optionally hide Streamlit’s sidebar."""
    st.markdown(CSS_NIGHT if night else CSS_LIGHT, unsafe_allow_html=True)
    if hide_sidebar:
        st.markdown(
            "<style>[data-testid='stSidebar']{display:none;} .block-container{padding-left:2rem;padding-right:2rem;}</style>",
            unsafe_allow_html=True
        )
    # base CSS (shared) could be added here if needed
