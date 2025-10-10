# pages/01_Admin_View.py
import io
import math
import pandas as pd
import streamlit as st

# ---------- Page Setup ----------
st.set_page_config(page_title="Admin Dashboard", page_icon="🗂️", layout="wide")

if "alloc_df" not in st.session_state:
    st.session_state.alloc_df = pd.DataFrame()
if "total_rows" not in st.session_state:
    st.session_state.total_rows = 0

st.title("🗂️ Admin Dashboard – SME Allocation")
st.caption("English on top • Tamil below – coming from content files. This page lets you allocate row ranges to SMEs and track status.")

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
        data.append(
            {"SME": name, "Email": email, "StartRow": s, "EndRow": e,
             "AssignedCount": count, "Status": "Not Started", "Notes/Link": ""}
        )
    return pd.DataFrame(data)

def validate_ranges(df: pd.DataFrame, total_rows: int) -> list[str]:
    """Return a list of validation messages (empty means all good)."""
    messages = []
    # empty?
    if df.empty:
        return ["No allocation found. Click **Auto-allocate** to generate ranges."]
    # type/NaN checks
    for col in ["StartRow", "EndRow"]:
        if df[col].isna().any():
            messages.append(f"Some rows have blank **{col}**.")
    # bounds & order
    bad_bounds = df[(df["StartRow"] < 0) | (df["EndRow"] < 0) |
                    (df["EndRow"] > total_rows) | (df["StartRow"] > df["EndRow"])]
    if not bad_bounds.empty:
        messages.append("Some ranges are out of bounds or StartRow > EndRow.")
    # overlap check
    used = []
    for _, row in df.sort_values(["StartRow", "EndRow"]).iterrows():
        s, e = int(row.StartRow), int(row.EndRow)
        if s == 0 and e == 0:
            continue
        for us, ue in used:
            if not (e < us or s > ue):
                messages.append(f"Overlap between [{s}, {e}] and [{us}, {ue}].")
                break
        used.append((s, e))
    # coverage (optional, we only warn)
    if total_rows > 0:
        covered = 0
        for s, e in used:
            if s == 0 and e == 0:
                continue
            covered += (e - s + 1)
        if covered != total_rows:
            messages.append(f"Coverage warning: allocated **{covered} / {total_rows}** rows.")
    return list(dict.fromkeys(messages))  # de-duplicate

def df_download_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")

# ---------- Source of Work (CSV or Manual) ----------
st.subheader("1) Source of work (rows to allocate)")

left, right = st.columns([2, 1])
with left:
    csv = st.file_uploader("Upload the master CSV (recommended) – we’ll use its row count", type=["csv"])
    if csv is not None:
        try:
            df_master = pd.read_csv(csv)
            st.session_state.total_rows = len(df_master)
            st.success(f"Loaded CSV with **{len(df_master)}** rows.")
            with st.expander("Preview (first 20 rows)", expanded=False):
                st.dataframe(df_master.head(20), use_container_width=True)
        except Exception as e:
            st.error(f"Could not read CSV: {e}")

with right:
    st.session_state.total_rows = st.number_input(
        "Or enter total rows manually",
        min_value=0, step=1, value=int(st.session_state.total_rows)
    )

st.caption("Rows are treated as **1..N** (inclusive). We’ll split them into contiguous blocks per SME.")

# ---------- SME List ----------
st.subheader("2) SMEs")

n = st.selectbox("Number of SMEs", options=list(range(1, 13)), index=2)  # default 3

# Option A: quick paste
with st.expander("Paste SME names & emails (one per line: Name,Email)", expanded=False):
    sample = "Priya,priya@example.com\nKarthik,karthik@example.com\nMeena,meena@example.com"
    pasted = st.text_area("Paste here", value=sample, height=110)
    paste_btn = st.button("Use pasted list")

# Input rows
sme_inputs = []
cols = st.columns(3)
for i in range(n):
    with cols[i % 3]:
        name = st.text_input(f"SME {i+1} Name", key=f"sme_name_{i}", value=f"SME {i+1}")
        email = st.text_input(f"SME {i+1} Email", key=f"sme_email_{i}", value=f"sme{i+1}@example.com")
        sme_inputs.append((name.strip(), email.strip()))

if paste_btn and pasted.strip():
    lines = [ln.strip() for ln in pasted.splitlines() if ln.strip()]
    parsed = []
    for ln in lines[:n]:
        parts = [p.strip() for p in ln.split(",")]
        if len(parts) >= 2:
            parsed.append((parts[0], parts[1]))
    for i, (nm, em) in enumerate(parsed):
        st.session_state[f"sme_name_{i}"] = nm
        st.session_state[f"sme_email_{i}"] = em
    st.rerun()

# Refresh SME list from session (after possible paste)
smes = []
for i in range(n):
    nm = st.session_state.get(f"sme_name_{i}", f"SME {i+1}")
    em = st.session_state.get(f"sme_email_{i}", f"sme{i+1}@example.com")
    smes.append((nm, em))

# ---------- Allocation ----------
st.subheader("3) Allocation")

c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    if st.button("⚡ Auto-allocate equally"):
        st.session_state.alloc_df = build_alloc_df(smes, st.session_state.total_rows)

with c2:
    if st.button("🗑️ Reset allocation"):
        st.session_state.alloc_df = pd.DataFrame()

with c3:
    st.info("Tip: You can edit StartRow/EndRow manually in the table below. Status has a dropdown.")

# Build empty table if needed
if st.session_state.alloc_df.empty and smes:
    st.session_state.alloc_df = build_alloc_df(smes, 0)

# Editable table
edited = st.data_editor(
    st.session_state.alloc_df,
    key="alloc_editor",
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Status": st.column_config.SelectboxColumn(options=STATUS_CHOICES, default="Not Started"),
        "StartRow": st.column_config.NumberColumn(min_value=0, step=1),
        "EndRow": st.column_config.NumberColumn(min_value=0, step=1),
        "AssignedCount": st.column_config.NumberColumn(disabled=True),
    }
)

# Recompute AssignedCount when user changes ranges
if not edited.empty:
    edited["AssignedCount"] = (edited["EndRow"] - edited["StartRow"] + 1).clip(lower=0)

# Validation
msgs = validate_ranges(edited.copy(), st.session_state.total_rows)
if msgs:
    for m in msgs:
        st.warning(m)
else:
    st.success("✅ Ranges look good. No overlaps; bounds OK.")

st.session_state.alloc_df = edited

# ---------- Summary & Exports ----------
st.subheader("4) Summary & Export")
total_assigned = int(edited["AssignedCount"].sum()) if not edited.empty else 0
colA, colB, colC, colD = st.columns(4)
colA.metric("Total rows", f"{st.session_state.total_rows}")
colB.metric("Allocated", f"{total_assigned}")
colC.metric("Unallocated", f"{max(0, st.session_state.total_rows - total_assigned)}")
done_count = int((edited["Status"] == "Done").sum()) if not edited.empty else 0
colD.metric("SMEs Done", f"{done_count} / {len(edited)}")

col1, col2 = st.columns([1, 3])
with col1:
    if not edited.empty:
        csv_bytes = df_download_bytes(edited)
        st.download_button("⬇️ Download Allocation (CSV)", data=csv_bytes,
                           file_name="sme_allocations.csv", mime="text/csv")
with col2:
    st.caption("Share the CSV with your team. Each SME gets their Start–End row range and can update status later.")

st.divider()
st.caption("© Make-A-Mark · Admin tools for NEET/JEE localization")
