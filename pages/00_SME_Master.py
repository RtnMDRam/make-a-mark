# pages/00_SME_Master.py
import os
import re
import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SME Master", page_icon="🧑‍🏫", layout="wide")
st.title("🧑‍🏫 SME Master")
st.caption("Maintain the master list of Subject Matter Experts (subject, location, WhatsApp, etc.).")

DATA_DIR = "data"
MASTER_PATH = os.path.join(DATA_DIR, "sme_master.csv")
os.makedirs(DATA_DIR, exist_ok=True)

COLUMNS = [
    "Prefix", "Salutation", "Name", "Email", "Subject", "Status",
    "District", "Taluk", "Place", "Pin", "WhatsApp"
]
SUBJECTS = sorted(["Biology", "Chemistry", "English", "Maths", "Physics", "Tamil", "Others"])
SALUTATIONS = sorted(["Mr.", "Ms.", "Mrs.", "Dr.", "Prof."])
PREFIXES = ["Tr.", "Sr.", "Fr.", "Er.", ""]  # put your common teaching prefixes first
STATUSES = ["Active", "Inactive"]

def load_master() -> pd.DataFrame:
    if os.path.exists(MASTER_PATH):
        df = pd.read_csv(MASTER_PATH)
        # guarantee all columns present
        for c in COLUMNS:
            if c not in df.columns:
                df[c] = ""
        return df[COLUMNS]
    return pd.DataFrame(columns=COLUMNS)

def save_master(df: pd.DataFrame):
    df[COLUMNS].to_csv(MASTER_PATH, index=False, encoding="utf-8-sig")

def clean_digits(s: str, max_len=15) -> str:
    return re.sub(r"\D", "", s or "")[:max_len]

# ---------- Add / Update ----------
st.subheader("➕ Add / Update SME")

with st.form("sme_form", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        prefix = st.selectbox("Prefix", PREFIXES, index=0, help="e.g., Tr. (Teacher)")
        sal = st.selectbox("Salutation", SALUTATIONS, index=0)
        name = st.text_input("Name*")
        email = st.text_input("Email*")
    with c2:
        subject = st.selectbox("Subject*", SUBJECTS, index=SUBJECTS.index("Tamil") if "Tamil" in SUBJECTS else 0)
        status = st.selectbox("Status*", STATUSES, index=0)
        district = st.text_input("District*")
        taluk = st.text_input("Taluk*")
    with c3:
        place = st.text_input("Place*")
        pin = st.text_input("Pin code", help="Digits only")
        wa = st.text_input("WhatsApp (digits only)")

    submitted = st.form_submit_button("Save SME")

if submitted:
    if not name.strip() or not email.strip():
        st.error("Please fill **Name** and **Email**.")
    else:
        df = load_master()
        row = {
            "Prefix": prefix.strip(),
            "Salutation": sal.strip(),
            "Name": name.strip(),
            "Email": email.strip(),
            "Subject": subject.strip(),
            "Status": status.strip(),
            "District": district.strip().title(),
            "Taluk": taluk.strip().title(),
            "Place": place.strip().title(),
            "Pin": clean_digits(pin, 6),
            "WhatsApp": clean_digits(wa)
        }
        # upsert on Email
        if (df["Email"] == row["Email"]).any():
            df.loc[df["Email"] == row["Email"], :] = row
            st.success(f"Updated SME: {row['Name']}")
        else:
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            st.success(f"Added SME: {row['Name']}")
        save_master(df)

# ---------- Filter & Table ----------
st.markdown("### 🔎 Filter")
f1, f2, f3, f4 = st.columns([1, 1, 1, 1])
with f1:
    f_subject = st.multiselect("Subject", SUBJECTS)
with f2:
    f_district = st.text_input("District contains…")
with f3:
    f_status = st.multiselect("Status", STATUSES, default=["Active"])
with f4:
    f_pin = st.text_input("Pin code contains…")

df_view = load_master().copy()

if f_subject:
    df_view = df_view[df_view["Subject"].isin(f_subject)]
if f_status:
    df_view = df_view[df_view["Status"].isin(f_status)]
if f_district:
    df_view = df_view[df_view["District"].str.contains(f_district, case=False, na=False)]
if f_pin:
    df_view = df_view[df_view["Pin"].astype(str).str.contains(f_pin, na=False)]

st.markdown("### 📋 SME Master Table")
# Status as colored dot
def _status_dot(s):
    color = "green" if s == "Active" else "red"
    return f"<span style='display:inline-flex;align-items:center;gap:.4rem'>\
<span style='width:.6rem;height:.6rem;border-radius:50%;background:{color};display:inline-block'></span>{s}</span>"

if not df_view.empty:
    show = df_view.copy()
    show["Status"] = show["Status"].apply(_status_dot)
    st.write(
        show.to_html(escape=False, index=False),
        unsafe_allow_html=True
    )
else:
    st.info("No SMEs to show yet.")

# Downloads
c_dl1, c_dl2 = st.columns(2)
with c_dl1:
    st.download_button(
        "⬇️ Download Master CSV",
        data=load_master().to_csv(index=False, encoding="utf-8-sig"),
        file_name="sme_master.csv",
        mime="text/csv",
    )
with c_dl2:
    buf = io.BytesIO()
    load_master().to_excel(buf, index=False)
    st.download_button(
        "⬇️ Download Master Excel",
        data=buf.getvalue(),
        file_name="sme_master.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
