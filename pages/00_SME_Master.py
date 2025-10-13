# pages/00_SME_Master.py - Advanced SME Master Editor with Custom Logic

import streamlit as st
import pandas as pd

st.set_page_config(page_title="SME Master", page_icon="📝", layout="wide")

# Allowed salutations and subjects
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
    "Subject",    # For easy selection first
    "Salutation", # Dropdown with default "Tr."
    "SME Name",   # Main name, with/without initials - will auto-prepend prefix for new rows
    "Initial",    # Middle/last name or initial, optional
    "Email",
    "WhatsApp",
    "Address",    # Optional (can leave blank)
    "Place",
    "Pincode",
    "Taluk",
    "District",
    "Block ID",
    "Block Name"
]

# Initialize
if "sme_df" not in st.session_state:
    # Set up an empty DataFrame with the correct columns
    st.session_state.sme_df = pd.DataFrame(columns=column_order)

st.title("📝 SME Master Detailed Editor")
st.caption("All SME names default to 'Tr.' and salutations. You can add initials/middle names. Most address fields are optional.")

# SME table editor
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

# Force 'Tr.' or allowed salutation at start of every SME Name, if missing
if not edited_df.empty:
    for idx, row in edited_df.iterrows():
        sal = row.get("Salutation", "Tr.")
        if sal and not str(row["SME Name"]).startswith(sal):
            edited_df.at[idx, "SME Name"] = f"{sal} {row['SME Name']}".strip()

if not edited_df.equals(st.session_state.sme_df):
    st.session_state.sme_df = edited_df

st.markdown("---")

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

st.info(
    "Enter new SME rows with all required columns. SME name will always begin with 'Tr.' or your chosen salutation. "
    "Most address fields are optional for convenience. Use dropdowns for subject and salutation."
)
