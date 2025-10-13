import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SME Master", page_icon="📝", layout="wide")

prefixes = ["Tr.", "Ta."]
salutations = ["Mr.", "Mrs.", "Miss", "Ms.", "Dr.", "Prof.", "Lect.", "Rev.", "Other"]
subjects = sorted(["Biology", "Chemistry", "English", "Maths", "Physics", "Tamil", "Others"])
genders = ["Male", "Female", "Other", "Prefer not to say"]

column_order = [
    "Prefix", "Salutation", "SME Name", "Initial", "Email", "WhatsApp",
    "Subject 1", "Subject 2", "Subject 3", "Date of Birth", "Gender", "Photo",
    "Address", "Place", "Pincode", "Taluk", "District", "Block ID", "Block Name",
    "Education", "Experience"
]

if "sme_df" not in st.session_state:
    st.session_state.sme_df = pd.DataFrame(columns=column_order)

st.title("📝 SME Master – Add, Edit, Delete")

with st.form("add_sme_form", clear_on_submit=True):
    prefix = st.selectbox("Prefix (required)", prefixes, index=0)
    salu = st.selectbox("Salutation", salutations, index=0)
    name = st.text_input("Name (required)")
    initial = st.text_input("Initial")
    email = st.text_input("Email (required)")
    whatsapp = st.text_input("WhatsApp (required)")
    subj1 = st.selectbox("Subject 1 (required)", subjects)
    subj2 = st.selectbox("Subject 2", [""] + subjects)
    subj3 = st.selectbox("Subject 3", [""] + subjects)
    dob = st.date_input("Date of Birth", value=None,
                        min_value=datetime(1947, 1, 1), max_value=datetime(2025, 12, 31))
    gender = st.selectbox("Gender", [""] + genders)
    photo = st.file_uploader("Photo (optional, jpg/png/jpeg)", type=["jpg", "jpeg", "png"])
    address = st.text_input("Address")
    place = st.text_input("Place")
    pincode = st.text_input("Pincode")
    taluk = st.text_input("Taluk")
    district = st.text_input("District")
    block_id = st.text_input("Block ID")
    block_name = st.text_input("Block Name")
    edu = st.text_area("Education/Qualifications (optional, freeform)")
    exp = st.text_area("Employment/Experience (optional, freeform)")
    submitted = st.form_submit_button("Add SME to Table")

    if submitted:
        if not (name.strip() and email.strip() and whatsapp.strip() and subj1 and prefix):
            st.error("Please fill in all required fields: prefix, name, whatsapp, email, and subject.")
        else:
            sme_fullname = f"{prefix} {salu} {name.strip()}"
            dob_str = dob.strftime("%Y-%m-%d") if dob else ""
            photo_name = photo.name if photo else ""
            row_values = [
                prefix, salu, sme_fullname, initial, email, whatsapp,
                subj1, subj2, subj3, dob_str, gender, photo_name,
                address, place, pincode, taluk, district, block_id, block_name,
                edu, exp
            ]
            new_row = dict(zip(column_order, row_values))
            st.session_state.sme_df = pd.concat([
                st.session_state.sme_df, pd.DataFrame([new_row])
            ], ignore_index=True)
            st.success(f"SME {sme_fullname} added.")

st.markdown("---")
st.subheader("Current SME Table (Editable, Deletable)")

if not st.session_state.sme_df.empty:
    # Inline edit
    edited_df = st.data_editor(
        st.session_state.sme_df,
        use_container_width=True,
        num_rows="dynamic",
        key="sme_editor_main"
    )
    if not edited_df.equals(st.session_state.sme_df):
        st.session_state.sme_df = edited_df
        st.success("Your SME table changes were saved.")

    # Row delete
    del_idx = st.number_input(
        "Row number to delete (top row is 0):",
        min_value=0, max_value=len(st.session_state.sme_df)-1, step=1, value=0
    )
    if st.button("❌ Delete SME Row"):
        st.session_state.sme_df = st.session_state.sme_df.drop(del_idx).reset_index(drop=True)
        st.success("SME row deleted.")

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
    st.warning("Please add at least one SME before downloading/export.")

st.info(
    "Edit any SME cell directly in the table above. Delete a row by its number. Changes apply immediately and are shown in export."
)
