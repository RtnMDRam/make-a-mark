# pages/00_SME_Master.py - Advanced SME Master Editor with Error Guard and Dropdowns

import streamlit as st
import pandas as pd

st.set_page_config(page_title="SME Master", page_icon="📝", layout="wide")

salutations = ["Tr.", "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Rev.", "Other"]
subjects = sorted([
    "Biology",
    "Chemistry",
    "English",
    "Maths",
    "Physics",
    "Tamil",
    "Others"
])

column_order = [
    "Subject",    # Dropdown
    "Salutation", # Default Tr. dropdown
    "SME Name",   # (auto-prefixed)
    "Initial",    # Optional
    "Email",
    "WhatsApp",
    "Address",    # Optional
    "Place",
    "Pincode",
    "Taluk",
    "District",
    "Block ID",
    "Block Name"
]

if "sme_df" not in st.session_state:
    st.session_state.sme_df = pd.DataFrame(columns=column_order)

st.title("📝 SME Master Detailed Editor")
st.caption(
    "Subject dropdown first, then salutation with default 'Tr.'. SME Name auto-prefixed if missing. "
    "Add initials, address, and other details. Download only when at least one SME is entered."
)

edited_df = st.data_editor(
    st.session_state.sme_df,
    column_order=column_order,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Salutation": st.column_config.SelectboxColumn("Salutation", options=salutations, required=True),
        "Subject": st.column_config.SelectboxColumn("Subject", options=subjects, required=True),
        "Address": st.column_config.TextColumn("Address (optional)", required=False),
        "SME Name": st.column_config.TextColumn("Name"),
        "Initial": st.column_config.TextColumn("Initial (optional)", required=False),
        "Email": st.column_config.TextColumn("Email"),
        "WhatsApp": st.column_config.TextColumn("WhatsApp"),
        "Place": st.column_config.TextColumn("Place"),
        "Pincode": st.column_config.TextColumn("Pincode"),
        "Taluk": st.column_config.TextColumn("Taluk"),
        "District": st.column_config.TextColumn("District"),
        "Block ID": st.column_config.TextColumn("Block ID"),
        "Block Name": st.column_config.TextColumn("Block Name"),
    },
    key="sme_editor"
)

# Ensure salutation at start of SME Name if missing
if not edited_df.empty:
    for idx, row in edited_df.iterrows():
        sal = row.get("Salutation", "Tr.")
        name = str(row.get("SME Name", "")).strip()
        if name and not name.startswith(sal):
            edited_df.at[idx, "SME Name"] = f"{sal} {name}"

if not edited_df.equals(st.session_state.sme_df):
    st.session_state.sme_df = edited_df

st.markdown("---")

if not st.session_state.sme_df.empty:
    excel_bytes = st.session_state.sme_df.to_excel(index=False, engine="openpyxl")
    st.download_button(
        "⬇️ Download SME Master as Excel",
        data=excel_bytes,
        file_name="sme_master.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    csv_bytes = st.session_state.sme_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ Download SME Master as CSV",
        data=csv_bytes,
        file_name="sme_master.csv",
        mime="text/csv"
    )
else:
    st.warning("Please add at least one SME row before downloading Excel/CSV.")

st.info(
    "Enter SME details row-wise. SME names auto-begin with your chosen salutation. Use dropdowns to prevent errors in subject or salutation."
)
