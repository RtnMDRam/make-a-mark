# lib/top_strip.py
import re, pandas as pd, streamlit as st

__all__ = ["render_top_strip"]

def _clean_drive(url:str)->str:
    if "drive.google.com" not in url:
        return url.strip()
    m = re.search(r"/file/d/([^/]+)/", url)
    if m: return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    m = re.search(r"[?&]id=([^&]+)", url)
    if m: return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    return url.strip()

def _read_any(source):
    if hasattr(source, "read"):
        name = (getattr(source, "name","") or "").lower()
        if name.endswith(".csv"): return pd.read_csv(source)
        return pd.read_excel(source)
    if isinstance(source,str):
        u=_clean_drive(source)
        try: return pd.read_csv(u)
        except Exception: return pd.read_excel(u)
    raise RuntimeError("Unsupported source")

def render_top_strip():
    """Show compact top strip. Publishes qc_src, qc_work, qc_idx, cur_id on success."""
    ss = st.session_state

    st.markdown("""
    <style>
    .topstrip .stButton>button{padding:6px 14px; height:38px;}
    .topstrip .pill{background:#222832;color:#fff;border-radius:8px;padding:10px 14px;}
    [data-testid="stSidebar"]{display:none !important;}
    header, footer, [data-testid="collapsedControl"]{visibility:hidden;height:0;}
    .block-container{padding-top:8px !important; padding-bottom:8px !important;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="topstrip">', unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns([1.5,1.8,1.8,2.0])
    with c1: st.button("💾 Save", key="ts_save", use_container_width=True)
    with c2: st.button("✅ Mark Complete", key="ts_done", use_container_width=True)
    with c3: st.button("🗂️ Save & Next", key="ts_next", use_container_width=True)
    with c4: st.button("📥 Download QC", key="ts_dl", use_container_width=True, disabled=("qc_work" not in ss))

    u1, b, u2 = st.columns([6,1,6])
    with u1: link = st.text_input("Paste the CSV/XLSX link sent by admin (or upload). Quick & compact.",
                                  key="ts_link", placeholder="Paste the CSV/XLSX link")
    with b:  do_load = st.button("Load", key="ts_load", use_container_width=True)
    with u2: st.file_uploader("Upload the file here (Limit 200 MB per file)",
                              type=["csv","xlsx"], key="ts_file")

    st.markdown('</div>', unsafe_allow_html=True)

    if do_load:
        src=None
        if st.session_state.get("ts_file"): src=st.session_state["ts_file"]
        elif (link or "").strip(): src=link.strip()
        else:
            st.warning("Please provide a link or choose a file.")
            return

        try:
            df=_read_any(src)
            ss.qc_src=df.copy(); ss.qc_work=df.copy(); ss.qc_idx=0
            ss.cur_id = str(df.iloc[0].get("_id","—")) if not df.empty else "—"
            st.success("Loaded from file.")
        except Exception as e:
            st.error(f"Could not open. {e}")
