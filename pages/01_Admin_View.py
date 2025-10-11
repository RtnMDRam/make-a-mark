# pages/01_Admin_View.py
import io
import math
import pandas as pd
import streamlit as st

# ---------- Page Setup ----------
st.set_page_config(page_title="Admin Dashboard", page_icon="📊", layout="wide")

if "alloc_df" not in st.session_state:
    st.session_state.alloc_df = pd.DataFrame()
if "total_rows" not in st.session_state:
    st.session_state.total_rows = 0

st.title("📘 Admin Dashboard – SME Allocation")
st.caption("English on top • Tamil below — coming from content files. This page lets you allocate work to SMEs efficiently.")

# ---------- Load File (Uploader or from Drive) ----------
df = None

# Option 1: Manual Upload
uploaded_file = st.file_uploader("📂 Upload bilingual QB file (.xlsx or .csv)", type=["xlsx", "csv"])

if uploaded_file is not None:
    st.info(f"📁 File uploaded: {uploaded_file.name}")
    try:
        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        else:
            df = pd.read_csv(uploaded_file)
        st.success("✅ File loaded successfully from manual upload.")
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")

# Option 2: Load file from Google Drive (from 05_Drive_Link_Input.py)
elif "qb_df" in st.session_state and st.session_state["qb_df"] is not None:
    df = st.session_state["qb_df"]
    st.success("✅ File loaded from Google Drive (via 'Load from Drive' page).")

# ---------- Helpers ----------
STATUS_CHOICES = ["Not Started", "In Progress", "Done", "Blocked"]

def build_alloc_df(smes, total_rows: int) -> pd.DataFrame:
    """
    Create near-equal contiguous row ranges for each SME.
    Rows are 1-indexed and inclusive: [start, end].
    """
    if total_rows <= 0 or len(smes) == 0:
        return pd.DataFrame(columns=["SME", "Email", "StartRow", "EndRow", "AssignedCount", "Status", "Notes/Link"])
    
    q, r = divmod(total_rows, len(smes))
    starts, ends = [], []
    start = 1
    for i in range(len(smes)):
        share = q + (1 if i < r else 0)
        end = start + share - 1 if share > 0 else 0
        starts.append(start if share > 0 else 0)
        ends.append(end if share > 0 else 0)
        start = end + 1

    data = []
    for (name, email), s, e in zip(smes, starts, ends):
        count = max(0, e - s + 1)
        data.append({
            "SME": name,
            "Email": email,
            "StartRow": s,
            "EndRow": e,
            "AssignedCount": count,
            "Status": "Not Started",
            "Notes/Link": ""
        })
    return pd.DataFrame(data)

# ---------- SME Allocation ----------
st.subheader("👥 SME Allocation")

num_smes = st.number_input("Number of SMEs", min_value=1, max_value=50, value=3)
smes = []
for i in range(num_smes):
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input(f"SME {i+1} Name", key=f"name_{i}")
    with c2:
        email = st.text_input(f"SME {i+1} Email", key=f"email_{i}")
    smes.append((name, email))

if df is not None:
    total_rows = len(df)
    st.write(f"📄 Total rows in file: **{total_rows}**")
    if st.button("Generate SME Allocation Table"):
        alloc_df = build_alloc_df(smes, total_rows)
        st.session_state.alloc_df = alloc_df
        st.session_state.total_rows = total_rows
        st.success("✅ Allocation table created successfully!")

# ---------- Display Allocation ----------
if not st.session_state.alloc_df.empty:
    st.subheader("📋 Current SME Allocation Table")
    st.dataframe(st.session_state.alloc_df, use_container_width=True)

    csv = st.session_state.alloc_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Allocation CSV",
        data=csv,
        file_name="sme_allocation.csv",
        mime="text/csv",
    )
