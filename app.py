# app.py
import pandas as pd
import streamlit as st

# ---------- Page setup ----------
st.set_page_config(page_title="Make-A-Mark", page_icon="🎓", layout="wide")

st.title("🎓 Make-A-Mark Academy")
st.caption("Mission Aspire | Bilingual NEET & JEE Program")

st.markdown(
    """
Welcome to the **Admin & Content Processing Dashboard**.

Use the pages in the left sidebar to do your work:

- **Admin View** — Upload the QB file and allocate rows to SMEs (auto or manual), then save/export.
- **Drive Link Input** — Paste a Google Drive share link (set *Anyone with the link → Viewer*) to load a QB file.
- **Email QC Generator** — Generate reviewer/coordinator emails from the allocation table.
- **SME Master** — Maintain the master list of SMEs (name, email, subject, place, taluk, district, WhatsApp).
"""
)

st.divider()

# ---------- Quick links (if your Streamlit version supports it) ----------
# (If not supported, these will silently fall back to the sidebar instruction.)
linked = False
try:
    st.subheader("Quick links")
    st.page_link("pages/01_Admin_View.py", label="🗂️ Admin View")
    st.page_link("pages/05_Drive_Link_Input.py", label="🔗 Drive Link Input")
    st.page_link("pages/03_Email_QC_Generator.py", label="✉️ Email QC Generator")
    st.page_link("pages/00_SME_Master.py", label="📒 SME Master")
    linked = True
except Exception:
    pass

if not linked:
    st.info("Use the **left sidebar** to open Admin View, Drive Link Input, Email QC Generator, or SME Master.")

st.divider()

# ---------- Status snapshot (helpful for admins) ----------
with st.expander("🔎 Session status (debug)"):
    qb_rows = len(st.session_state.get("qb_df", pd.DataFrame()))
    alloc_rows = len(st.session_state.get("alloc_df", pd.DataFrame()))
    master_rows = len(st.session_state.get("sme_master", pd.DataFrame()))

    c1, c2, c3 = st.columns(3)
    c1.metric("QB rows loaded", qb_rows)
    c2.metric("Allocation rows", alloc_rows)
    c3.metric("SME master entries", master_rows)

    st.write("Session keys:", list(st.session_state.keys()))
