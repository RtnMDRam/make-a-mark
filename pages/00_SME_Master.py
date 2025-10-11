# pages/00_SME_Master.py
import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SME Master", page_icon="🧑‍🏫", layout="wide")
st.title("🧑‍🏫 SME Master")
st.caption("Maintain the master list of Subject Matter Experts (subject-wise, location, and WhatsApp).")

# ---------- Init ----------
COLUMNS = ["Name", "Email", "Subject", "Status", "Place", "Taluk", "District", "WhatsApp"]

if "sme_master" not in st.session_state:
    st.session_state.sme_master = pd.DataFrame(columns=COLUMNS)

# ---------- Small helpers ----------
def clean_phone(s: str) -> str:
    """Keep digits only, allow 10–15 digits."""
    digits = re.sub(r"\D", "", s or "")
    return digits[:15]

SUBJECTS = ["Biology", "Physics", "Chemistry", "Maths", "English", "Others"]
STATUSES = ["Active", "Inactive"]

# ---------- Add / Update ----------
st.subheader("➕ Add / Update SME")

with st.form("sme_form", clear_on_submit=True):
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Name*")
        email = st.text_input("Email*")
        subject = st.selectbox("Subject*", SUBJECTS)
        status = st.selectbox("Status*", STATUSES, index=0)
    with c2:
        place = st.text_input("Place")
        taluk = st.text_input("Taluk")
        district = st.text_input("District")
        whatsapp = st.text_input("WhatsApp (digits only)")

    submitted = st.form_submit_button("Save SME")

if submitted:
    if not name or not email:
        st.warning("Please fill **Name** and **Email**.")
    else:
        row = {
            "Name": name.strip(),
            "Email": email.strip(),
            "Subject": subject,
            "Status": status,
            "Place": place.strip(),
            "Taluk": taluk.strip(),
            "District": district.strip(),
            "WhatsApp": clean_phone(whatsapp),
        }
        df = st.session_state.sme_master

        # If same Email exists, update; else append
        if not df[df["Email"].str.lower() == row["Email"].lower()].empty:
            st.session_state.sme_master.loc[
                df["Email"].str.lower() == row["Email"].lower(), :
            ] = row
            st.success(f"✅ Updated existing SME: {name}")
        else:
            st.session_state.sme_master = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            st.success(f"✅ Added SME: {name}")

# ---------- Filters ----------
st.subheader("🔎 Filter")
fc1, fc2, fc3 = st.columns(3)
with fc1:
    f_subject = st.multiselect("Subject", SUBJECTS)
with fc2:
    f_district = st.text_input("District contains…")
with fc3:
    f_status = st.multiselect("Status", STATUSES, default=["Active"])

view = st.session_state.sme_master.copy()

if f_subject:
    view = view[view["Subject"].isin(f_subject)]
if f_status:
    view = view[view["Status"].isin(f_status)]
if f_district:
    view = view[view["District"].str.contains(f_district, case=False, na=False)]

# ---------- Editable table ----------
st.subheader("📋 SME Master Table")
edited = st.data_editor(
    view,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "WhatsApp": st.column_config.TextColumn("WhatsApp (digits)"),
    },
    key="sme_editor",
)

# Write edits back into the session master (by Email as key)
if not edited.empty:
    base = st.session_state.sme_master.set_index("Email")
    edited_ix = edited.set_index("Email")
    base.update(edited_ix)
    st.session_state.sme_master = base.reset_index()

# ---------- Download ----------
csv_bytes = st.session_state.sme_master[COLUMNS].to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ Download SME Master CSV", data=csv_bytes, file_name="sme_master.csv", mime="text/csv")
