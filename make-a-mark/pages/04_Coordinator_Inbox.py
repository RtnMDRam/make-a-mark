# pages/04_Coordinator_Inbox.py
# ----------------------------------------------------------
# Merge SME-returned CSV/XLSX files into one bilingual master
# ----------------------------------------------------------

import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Coordinator Inbox", page_icon="📂", layout="wide")
st.title("📂 Coordinator Inbox – Merge & Review Returned SME Files")

st.caption("Drop all SME-returned QC files below (CSV or XLSX). The system merges, color-codes, and exports a consolidated master.")

st.divider()

# ---------- 1) File uploader ----------
uploads = st.file_uploader("Upload multiple SME-returned files", type=["csv", "xlsx"], accept_multiple_files=True)

if not uploads:
    st.info("Upload two or more QC files to begin merging.")
    st.stop()

merged_list = []
for f in uploads:
    try:
        if f.name.lower().endswith(".csv"):
            df = pd.read_csv(f)
        else:
            df = pd.read_excel(f, engine="openpyxl")
        df["SourceFile"] = f.name
        merged_list.append(df)
    except Exception as e:
        st.error(f"❌ Error reading {f.name}: {e}")

if not merged_list:
    st.warning("No valid files processed.")
    st.stop()

# ---------- 2) Merge ----------
merged = pd.concat(merged_list, ignore_index=True)

# ensure columns exist
for c in ["English","Tamil","Status"]:
    if c not in merged.columns:
        merged[c] = ""

# normalize status text
merged["Status"] = merged["Status"].fillna("").str.title().replace({
    "Qc Done":"QC Done",
    "Done":"QC Done",
    "In Progress":"In Progress",
    "Not Started":"Not Started",
})

# ---------- 3) Summary metrics ----------
total = len(merged)
qc_done = int((merged["Status"] == "QC Done").sum())
in_prog = int((merged["Status"] == "In Progress").sum())
not_started = int((merged["Status"] == "Not Started").sum())
balance = total - qc_done

st.markdown(f"""
<div style="border:1px solid #eee;border-radius:8px;padding:10px;background:#f7f7f7;">
<b>Total Rows:</b> {total} &nbsp; | &nbsp;
<span style='background:#ffe58f;padding:3px 6px;border-radius:4px;'>In Progress: {in_prog}</span> &nbsp; | &nbsp;
<span style='background:#b7f7b0;padding:3px 6px;border-radius:4px;'>QC Done: {qc_done}</span> &nbsp; | &nbsp;
<span style='background:#ffd6d6;padding:3px 6px;border-radius:4px;'>Not Started: {not_started}</span> &nbsp; | &nbsp;
<b>Balance:</b> {balance}
</div>
""", unsafe_allow_html=True)

st.divider()

# ---------- 4) Color-coded preview ----------
def color_row(row):
    color = ""
    if row["Status"] == "QC Done":
        color = "background-color:#d9fbd9"
    elif row["Status"] == "In Progress":
        color = "background-color:#fff8b3"
    elif row["Status"] == "Not Started":
        color = "background-color:#ffd6d6"
    return [color]*len(row)

with st.expander("🔍 Preview merged dataset (first 200 rows)", expanded=False):
    st.dataframe(merged.head(200).style.apply(color_row, axis=1), use_container_width=True)

# ---------- 5) Export options ----------
st.subheader("📤 Export Merged Master")
out_xlsx = BytesIO()
with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
    merged.to_excel(writer, index=False, sheet_name="MergedQC")

st.download_button("⬇️ Download Master Excel", data=out_xlsx.getvalue(),
                   file_name="Merged_QC_Master.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

csv_bytes = merged.to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ Download Master CSV", data=csv_bytes,
                   file_name="Merged_QC_Master.csv", mime="text/csv")

st.success("✅ Merging complete. Use this master file for reports or archival.")
