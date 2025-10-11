# pages/00_SME_Master.py
import re
import pandas as pd
import streamlit as st

# ---------- Page Setup ----------
st.set_page_config(page_title="SME Master", page_icon="🧑‍🏫", layout="wide")
st.title("🧑‍🏫 SME Master")
st.caption(
    "Maintain the master list of Subject Matter Experts (subject-wise, location, "
    "pin code, WhatsApp) and reuse across the app."
)

# ---------- Init ----------
COLUMNS = [
    "Name", "Email", "Subject", "Status",
    "Place", "Taluk", "District", "PinCode", "WhatsApp"
]

if "sme_master" not in st.session_state:
    st.session_state.sme_master = pd.DataFrame(columns=COLUMNS)

# ---------- Helpers ----------
def clean_phone(s: str) -> str:
    """Keep digits only, allow up to 15 digits."""
    digits = re.sub(r"\D", "", s or "")
    return digits[:15]

def clean_pincode(s: str) -> str:
    """Keep digits only for pin code; keep up to 10 to be safe."""
    digits = re.sub(r"\D", "", s or "")
    return digits[:10]

SUBJECTS = ["Biology", "Physics", "Chemistry", "Maths", "English", "Tamil", "Others"]
STATUSES = ["Active", "Inactive"]

# ---------- Add / Update ----------
st.subheader("➕ Add / Update SME")

with st.form("sme_form", clear_on_submit=True):
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Name*")
        email = st.text_input("Email*")
        subject = st.selectbox("Subject*", SUBJECTS, index=0)
        status = st.selectbox("Status*", STATUSES, index=0)
    with c2:
        place = st.text_input("Place")
        taluk = st.text_input("Taluk")
        district = st.text_input("District")
        pincode = st.text_input("Pin code")
        whatsapp = st.text_input("WhatsApp (digits only)")

    submitted = st.form_submit_button("Save SME")

if submitted:
    if not name.strip() or not email.strip():
        st.warning("Please fill **Name** and **Email**.")
    else:
        df = st.session_state.sme_master
        row = {
            "Name": name.strip(),
            "Email": email.strip(),
            "Subject": subject,
            "Status": status,
            "Place": place.strip(),
            "Taluk": taluk.strip(),
            "District": district.strip(),
            "PinCode": clean_pincode(pincode),
            "WhatsApp": clean_phone(whatsapp),
        }

        # Update if email already exists, else append
        if not df.empty and (df["Email"].str.lower() == row["Email"].lower()).any():
            idx = df.index[df["Email"].str.lower() == row["Email"].lower()][0]
            for k, v in row.items():
                df.at[idx, k] = v
            st.success(f"✅ Updated SME: {row['Name']}")
        else:
            st.session_state.sme_master = pd.concat(
                [df, pd.DataFrame([row])], ignore_index=True
            )
            st.success(f"✅ Added SME: {row['Name']}")

# ---------- Filters ----------
st.subheader("🔎 Filter")
fc1, fc2, fc3, fc4 = st.columns([1.1, 1.1, 1.0, 1.0])
with fc1:
    subj_filter = st.multiselect("Subject", options=SUBJECTS)
with fc2:
    dist_filter = st.text_input("District contains…")
with fc3:
    status_filter = st.multiselect("Status", options=STATUSES, default=["Active"])
with fc4:
    pin_filter = st.text_input("Pin code contains…")

df_view = st.session_state.sme_master.copy()

if subj_filter:
    df_view = df_view[df_view["Subject"].isin(subj_filter)]
if dist_filter:
    df_view = df_view[df_view["District"].str.contains(dist_filter, case=False, na=False)]
if status_filter:
    df_view = df_view[df_view["Status"].isin(status_filter)]
if pin_filter:
    df_view = df_view[df_view["PinCode"].astype(str).str.contains(pin_filter, na=False)]

# ---------- Status Badges (Green/Red) ----------
def status_badge(s: str) -> str:
    return "🟢 Active" if s == "Active" else "🔴 Inactive"

df_show = df_view.copy()
if not df_show.empty:
    df_show["Status"] = df_show["Status"].map(status_badge)

# Reorder columns for display
order = ["Email", "Name", "Subject", "Status", "Place", "Taluk", "District", "PinCode", "WhatsApp"]
df_show = df_show[[c for c in order if c in df_show.columns]]

st.subheader("📋 SME Master Table")
st.dataframe(df_show, use_container_width=True)

# ---------- Download ----------
c_dl1, c_dl2 = st.columns([1, 3])
with c_dl1:
    if not st.session_state.sme_master.empty:
        csv_bytes = st.session_state.sme_master.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ Download Master CSV",
            data=csv_bytes,
            file_name="sme_master.csv",
            mime="text/csv",
        )
