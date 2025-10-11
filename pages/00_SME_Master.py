# pages/00_SME_Master.py
import io
import re
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html

# ---------------- Page setup ----------------
st.set_page_config(page_title="SME Master", page_icon="🧑‍🏫", layout="wide")
st.title("🧑‍🏫 SME Master")
st.caption("Maintain the master list of Subject Matter Experts (subject-wise, location, WhatsApp).")

# ---- iPad / mobile: keep inputs visible above keyboard ----
st.markdown("""
<style>
  .block-container { padding-bottom: 40vh; }
  section[data-testid="stSidebar"] .block-container { padding-bottom: 20vh; }
  .stTextInput, .stNumberInput, .stSelectbox, .stTextArea { margin-bottom: 0.25rem !important; }
</style>
""", unsafe_allow_html=True)
html("""
<script>
 (function () {
   function bringIntoView(e) {
     try {
       const el = e.target, r = el.getBoundingClientRect();
       const safe = window.innerHeight * 0.30;
       if (r.bottom > window.innerHeight - safe) el.scrollIntoView({block:"center", behavior:"smooth"});
     } catch(_) {}
   }
   document.addEventListener('focusin', bringIntoView, {passive:true});
 })();
</script>
""", height=0)

# ---------------- Session state init ----------------
SME_COLUMNS = [
    "Prefix", "Salutation", "Name", "Email", "Subject", "Status",
    "District", "Taluk", "Place", "Pincode", "WhatsApp"
]
if "sme_master" not in st.session_state:
    st.session_state.sme_master = pd.DataFrame(columns=SME_COLUMNS)

# built-in subjects; user can add more (persist for session)
DEFAULT_SUBJECTS = ["Biology", "Chemistry", "English", "Maths", "Physics", "Tamil", "Others"]
if "subjects_master" not in st.session_state:
    st.session_state.subjects_master = sorted(DEFAULT_SUBJECTS)

# optional locations cache (District,Taluk,Place,Pincode)
if "locations_master" not in st.session_state:
    st.session_state.locations_master = pd.DataFrame(columns=["District", "Taluk", "Place", "Pincode"])

# ---------------- Helpers ----------------
EMAIL_RE = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.I)

def clean_phone_digits(s: str, max_len: int = 15) -> str:
    digits = re.sub(r"\D", "", s or "")
    return digits[:max_len]

def title_or_empty(s: str) -> str:
    s = (s or "").strip()
    return s.title() if s else s

def ensure_subject_in_master(new_subj: str):
    if new_subj and new_subj not in st.session_state.subjects_master:
        st.session_state.subjects_master.append(new_subj)
        st.session_state.subjects_master.sort()

# ---------------- Locations loader (optional) ----------------
with st.expander("📍 Optional: Load Locations CSV (District, Taluk, Place, Pincode)"):
    help_cols = st.columns([1,1,1])
    with help_cols[0]:
        sample = pd.DataFrame({
            "District":["Coimbatore","Coimbatore","Erode"],
            "Taluk":["Sulur","Sulur","Perundurai"],
            "Place":["Irugur","Palladam Road","Perundurai Town"],
            "Pincode":["641103","641402","638052"],
        })
        st.dataframe(sample, use_container_width=True)
    up = st.file_uploader("Upload locations CSV", type=["csv"])
    if up is not None:
        try:
            loc_df = pd.read_csv(up).fillna("")
            # normalise column names
            cols_map = {c.lower(): c for c in loc_df.columns}
            need = ["district","taluk","place","pincode"]
            if all(n in cols_map for n in need):
                loc_df = loc_df.rename(columns={
                    cols_map["district"]: "District",
                    cols_map["taluk"]: "Taluk",
                    cols_map["place"]: "Place",
                    cols_map["pincode"]: "Pincode",
                })
                for c in ["District","Taluk","Place"]:
                    loc_df[c] = loc_df[c].astype(str).map(title_or_empty)
                loc_df["Pincode"] = loc_df["Pincode"].astype(str).map(clean_phone_digits)
                st.session_state.locations_master = loc_df
                st.success(f"Loaded {len(loc_df)} location rows.")
            else:
                st.error("CSV must include columns: District, Taluk, Place, Pincode (any case).")
        except Exception as e:
            st.error(f"Could not read CSV: {e}")

# ---------------- Subject add (optional) ----------------
with st.expander("🧩 Add a new Subject"):
    s_new = st.text_input("New subject")
    if st.button("➕ Add Subject"):
        sn = title_or_empty(s_new)
        if sn:
            ensure_subject_in_master(sn)
            st.success(f"Added subject: {sn}")
        else:
            st.warning("Type a subject name first.")

# ---------------- Add / Update SME ----------------
st.subheader("➕ Add / Update SME")

salutations = ["Mr.", "Ms.", "Mrs.", "Dr.", "Prof."]
prefix_default = "Tr."

with st.form("sme_form", clear_on_submit=True):
    c1, c2 = st.columns(2)

    with c1:
        prefix = st.text_input("Prefix", value=prefix_default, help="Default teacher prefix.")
        sal = st.selectbox("Salutation", options=salutations, index=0)
        name = st.text_input("Name*")
        email = st.text_input("Email*")
        subject = st.selectbox("Subject*", options=st.session_state.subjects_master, index=st.session_state.subjects_master.index("Tamil") if "Tamil" in st.session_state.subjects_master else 0)
        status = st.selectbox("Status*", options=["Active", "Inactive"], index=0)

    with c2:
        # cascading locations when locations_master is present
        loc_df = st.session_state.locations_master
        if not loc_df.empty:
            districts = sorted(loc_df["District"].dropna().unique().tolist())
            district = st.selectbox("District*", options=districts)
            taluks = sorted(loc_df.loc[loc_df["District"]==district, "Taluk"].dropna().unique().tolist())
            taluk = st.selectbox("Taluk*", options=taluks)
            places = sorted(loc_df[(loc_df["District"]==district)&(loc_df["Taluk"]==taluk)]["Place"].dropna().unique().tolist())
            place = st.selectbox("Place*", options=places)
            # find a pincode (if multiple, let user override)
            pin_guess = ""
            subset = loc_df[(loc_df["District"]==district)&(loc_df["Taluk"]==taluk)&(loc_df["Place"]==place)]
            if not subset.empty:
                pin_guess = str(subset.iloc[0]["Pincode"])
            pincode = st.text_input("Pin code", value=pin_guess, help="6 digits if available.")
        else:
            district = st.text_input("District*")
            taluk = st.text_input("Taluk*")
            place = st.text_input("Place*")
            pincode = st.text_input("Pin code", help="6 digits if available.")

        whatsapp = st.text_input("WhatsApp (digits only)")

    submitted = st.form_submit_button("Save SME")

if submitted:
    # validations & cleaning
    nm = (name or "").strip()
    em = (email or "").strip()
    if not nm or not em:
        st.warning("Please fill **Name** and **Email**.")
    elif not EMAIL_RE.match(em):
        st.warning("Email format looks invalid.")
    else:
        subj = title_or_empty(subject) or subject
        ensure_subject_in_master(subj)
        row = {
            "Prefix": (prefix or "Tr.").strip(),
            "Salutation": sal,
            "Name": nm,
            "Email": em,
            "Subject": subj,
            "Status": status,
            "District": title_or_empty(district),
            "Taluk": title_or_empty(taluk),
            "Place": title_or_empty(place),
            "Pincode": clean_phone_digits(pincode, max_len=6),
            "WhatsApp": clean_phone_digits(whatsapp),
        }
        st.session_state.sme_master = pd.concat(
            [st.session_state.sme_master, pd.DataFrame([row])],
            ignore_index=True
        )
        st.success(f"Added SME: {row['Salutation']} {row['Name']}")

# ---------------- Filter & Table ----------------
st.subheader("🔎 Filter")

fc1, fc2, fc3, fc4, fc5 = st.columns([1.2, 1.2, 1.0, 1.0, 0.8])

with fc1:
    subj_filter = st.multiselect("Subject", options=st.session_state.subjects_master)
with fc2:
    dist_contains = st.text_input("District contains…")
with fc3:
    status_filter = st.multiselect("Status", options=["Active","Inactive"], default=["Active"])
with fc4:
    pin_contains = st.text_input("Pin code contains…")
with fc5:
    if st.button("🔍 Search by Pin"):
        # quick-scroll effect: nothing extra needed—filters will apply
        pass

df = st.session_state.sme_master.copy()

# apply filters
if subj_filter:
    df = df[df["Subject"].isin(subj_filter)]
if dist_contains:
    df = df[df["District"].str.contains(dist_contains, case=False, na=False)]
if status_filter:
    df = df[df["Status"].isin(status_filter)]
if pin_contains:
    df = df[df["Pincode"].str.contains(pin_contains, na=False)]

# nice status icon
def status_icon(s):
    return "🟢 Active" if s == "Active" else "🔴 Inactive"
if not df.empty and "Status" in df.columns:
    df = df.assign(Status=df["Status"].map(status_icon))

st.subheader("📋 SME Master Table")
st.dataframe(
    df.sort_values(["Subject", "District", "Taluk", "Place", "Name"], na_position="last"),
    use_container_width=True
)

# ---------------- Downloads ----------------
dcol1, dcol2 = st.columns(2)

with dcol1:
    csv_bytes = st.session_state.sme_master.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Download Master CSV", data=csv_bytes, file_name="sme_master.csv", mime="text/csv")

with dcol2:
    # Excel export
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as xw:
        st.session_state.sme_master.to_excel(xw, index=False, sheet_name="SME_Master")
    st.download_button("📗 Download Master Excel", data=out.getvalue(), file_name="sme_master.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
