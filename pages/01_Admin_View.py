# pages/01_Admin_View.py
import io
import math
import pandas as pd
import streamlit as st

# ---------- Page Setup ----------
st.set_page_config(page_title="Admin Dashboard", page_icon="📊", layout="wide")

# --- Mobile / iPad keyboard-friendly layout ---
from streamlit.components.v1 import html
enable_mobile = True  # set False to disable if not needed

if enable_mobile:
    # Add extra bottom padding so keyboard doesn't hide inputs
    st.markdown(
        """
        <style>
          .block-container { padding-bottom: 40vh; }
          section[data-testid="stSidebar"] .block-container { padding-bottom: 20vh; }
          .stTextInput, .stNumberInput, .stSelectbox, .stTextArea { margin-bottom: 0.25rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    # Scroll focused field into view automatically
    html(
        """
        <script>
          (function () {
            function bringIntoView(e) {
              try {
                const el = e.target;
                const rect = el.getBoundingClientRect();
                const bottomSafe = window.innerHeight * 0.30;
                if (rect.bottom > window.innerHeight - bottomSafe) {
                  el.scrollIntoView({ block: "center", behavior: "smooth" });
                }
              } catch (err) {}
            }
            document.addEventListener('focusin', bringIntoView, { passive: true });
          })();
        </script>
        """,
        height=0,
    )

# ---------- Session state ----------
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
elif st.session_state.get("qb_df") is not None:
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
    rows = []
    start = 1
    for i, (name, email) in enumerate(smes):
        share = q + (1 if i < r else 0)
        end = start + share - 1 if share > 0 else 0
        count = max(0, end - start + 1)
        rows.append(
            {
                "SME": name,
                "Email": email,
                "StartRow": start if share > 0 else 0,
                "EndRow": end if share > 0 else 0,
                "AssignedCount": count,
                "Status": "Not Started",
                "Notes/Link": "",
            }
        )
        start = end + 1
    return pd.DataFrame(rows)

# ----------- SME Allocation -----------
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
    st.write(f"📄 **Total rows in file:** {total_rows}")

    # Auto allocation
    if st.button("⚙️ Generate SME Allocation (Auto)"):
        alloc_df = build_alloc_df(smes, total_rows)
        st.session_state.alloc_df = alloc_df
        st.session_state.total_rows = total_rows
        st.success("✅ Allocation table created automatically!")

    # --- Manual Assignment Mode ---
    st.markdown("### ✋ Manual Assignment Mode")
    if not st.session_state.alloc_df.empty:
        alloc_df = st.session_state.alloc_df.copy()
        total_rows = st.session_state.total_rows

        st.info("Adjust row distribution manually below. Totals will auto-update.")
        remaining = total_rows
        manual_counts = []

        for i, (name, email) in enumerate(smes):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**{name or f'SME {i+1}'}** ({email})")
            with c2:
                count = st.number_input(
                    "Rows",
                    key=f"manual_{i}",
                    min_value=0,
                    max_value=remaining,
                    value=int(alloc_df.loc[i, "AssignedCount"]) if i < len(alloc_df) else 0,
                )
                manual_counts.append(count)
                remaining -= count

        if remaining > 0:
            st.warning(f"{remaining} rows unassigned.")
        elif remaining < 0:
            st.error("Too many rows assigned — reduce one SME’s count.")

        # Apply manual counts -> convert to contiguous ranges
        if st.button("🔁 Apply Manual Assignment"):
            start = 1
            rows = []
            for (name, email), count in zip(smes, manual_counts):
                end = start + count - 1 if count > 0 else 0
                rows.append(
                    {
                        "SME": name,
                        "Email": email,
                        "StartRow": start if count > 0 else 0,
                        "EndRow": end if count > 0 else 0,
                        "AssignedCount": max(0, end - start + 1) if count > 0 else 0,
                        "Status": "Not Started",
                        "Notes/Link": "",
                    }
                )
                start = (end + 1) if count > 0 else start
            st.session_state.alloc_df = pd.DataFrame(rows)
            st.success("✅ Manual assignment applied successfully!")

# ---- Display Editable Allocation Table ----
if not st.session_state.alloc_df.empty:
    st.subheader("📋 Current SME Allocation Table")
    df_view = st.session_state.alloc_df.copy()

    edited = st.data_editor(
        df_view,
        num_rows="fixed",
        use_container_width=True,
        height=420,   # keeps editor visible above iPad keyboard
        key="alloc_editor",
        column_config={
            "SME": st.column_config.TextColumn("SME", help="SME Name"),
            "Email": st.column_config.TextColumn("Email", help="SME Email", disabled=True),
            "StartRow": st.column_config.NumberColumn("Start Row", min_value=1, help="Starting row index"),
            "EndRow": st.column_config.NumberColumn("End Row", min_value=1, help="Ending row index"),
            "AssignedCount": st.column_config.NumberColumn("Assigned Count", disabled=True),
            "Status": st.column_config.SelectboxColumn("Status", options=STATUS_CHOICES),
            "Notes/Link": st.column_config.TextColumn("Notes/Link", help="Notes or progress link"),
        },
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Save Allocation Changes"):
            # Recompute AssignedCount from Start/End on save
            ed = edited.copy()
            def _recount(row):
                s = int(row.get("StartRow", 0) or 0)
                e = int(row.get("EndRow", 0) or 0)
                return max(0, e - s + 1) if s > 0 and e >= s else 0
            ed["AssignedCount"] = ed.apply(_recount, axis=1)
            st.session_state.alloc_df = ed
            st.success("Changes saved successfully!")

    with c2:
        csv_bytes = st.session_state.alloc_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ Download Allocation CSV",
            data=csv_bytes,
            file_name="sme_allocation.csv",
            mime="text/csv",
        )
