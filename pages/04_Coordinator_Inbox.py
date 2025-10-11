# ================================
# 04_Coordinator_Inbox.py
# ================================

import streamlit as st
import pandas as pd
from datetime import datetime

st.title("📥 Coordinator Inbox")
st.caption("Track SME QC submissions, deadlines, and file uploads.")

# --- 1️⃣ Upload SME Master Allocation File ---
uploaded_allocation = st.file_uploader(
    "Upload Master SME Allocation File (.xlsx or .csv)", 
    type=["xlsx", "csv"]
)

if uploaded_allocation:
    try:
        if uploaded_allocation.name.endswith(".csv"):
            df = pd.read_csv(uploaded_allocation)
        else:
            df = pd.read_excel(uploaded_allocation, engine="openpyxl")

        if "SME Name" not in df.columns:
            st.error("Missing 'SME Name' column in uploaded file.")
            st.stop()

        st.success(f"Loaded {len(df)} SME allocation rows.")
        st.dataframe(df.head(10), use_container_width=True)
    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()

    # --- 2️⃣ SME Submission Tracker ---
    st.subheader("🧾 Submission Status")

    if "Status" not in df.columns:
        df["Status"] = "Pending"
    if "Last Updated" not in df.columns:
        df["Last Updated"] = ""

    # Table color-coding
    def highlight_status(val):
        color = (
            "#f4cccc" if val == "Pending"
            else "#ffe599" if val == "In Progress"
            else "#b6d7a8" if val == "Completed"
            else ""
        )
        return f"background-color: {color}"

    st.dataframe(df.style.applymap(highlight_status, subset=["Status"]), use_container_width=True)

    # --- 3️⃣ SME File Upload (QC Submission) ---
    st.divider()
    st.subheader("📤 Upload SME QC File")

    sme_selected = st.selectbox("Select SME", sorted(df["SME Name"].unique()))
    qc_file = st.file_uploader("Upload QC Verified File", type=["xlsx", "csv"])

    if st.button("Mark as Submitted") and sme_selected:
        df.loc[df["SME Name"] == sme_selected, "Status"] = "Completed"
        df.loc[df["SME Name"] == sme_selected, "Last Updated"] = datetime.now().strftime("%d-%b-%Y %H:%M")
        st.success(f"✅ {sme_selected}'s QC marked as Completed.")

    # --- 4️⃣ Export Updated Tracker ---
    st.divider()
    st.subheader("📊 Export Updated Tracker")

    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ Download Updated SME Tracker",
        data=csv_bytes,
        file_name="sme_qc_tracker_updated.csv",
        mime="text/csv",
    )

else:
    st.info("Please upload the master SME allocation file to begin tracking.")
