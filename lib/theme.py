# lib/theme.py  (stub)
import streamlit as st

CSS = """
<style>
.box{border:2px solid #ddd;border-radius:12px;padding:1rem 1.1rem;margin:0.8rem 0;}
.box h4{margin:.2rem 0 .6rem;font-size:1.0rem}
.box.gloss{border-color:#000}
.box.en{background:#E6F0FF;border-color:#1F77B4}
.box.tao{background:#E8F5E9;border-color:#2CA02C}
.box.qc{background:#FFF3F0;border-color:#E57373}
.box.edit{background:#FFF8E1;border-color:#FFB300}
</style>
"""

def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)

def panel(title: str, color_class: str, body_html: str):
    """Tiny helper used by pages; safe to replace later."""
    st.markdown(f"<div class='box {color_class}'><h4>{title}</h4><div>{body_html}</div></div>", unsafe_allow_html=True)
