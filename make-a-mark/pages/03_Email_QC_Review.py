# pages/03_Email_QC_Review.py 
import os
import io
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html

st.set_page_config(page_title="Email QC Review", page_icon="✉️", layout="wide")
st.title("✉️ Email QC Review")
st.caption("Generate ready-to-send QC emails using SME Master + allocation file.")

DATA_DIR = "data"
MASTER_PATH = os.path.join(DATA_DIR, "sme_master.csv")

# ---- helpers ----
def load_master() -> pd.DataFrame:
    if os.path.exists(MASTER_PATH):
        return pd.read_csv(MASTER_PATH)
    return pd.DataFrame(columns=[
        "Prefix","Salutation","Name","Email","Subject","Status",
        "District","Taluk","Place","Pin","WhatsApp"
    ])

def copy_button(target_id: str, label="Copy to clipboard"):
    html(f"""
    <button id="copybtn" style="padding:.5rem 1rem;border:1px solid #ddd;border-radius:6px;cursor:pointer">
      📋 {label}
    </button>
    <script>
      const btn = document.getElementById('copybtn');
      btn.onclick = () => {{
        const txt = document.getElementById('{target_id}');
        navigator.clipboard.writeText(txt.value || txt.innerText || "");
        btn.innerText = "✅ Copied!";
        setTimeout(()=>btn.innerText="📋 {label}", 1600);
      }};
    </script>
    """, height=0)

# ---- Input files & filters ----
c1, c2 = st.columns([2, 1])
with c1:
    uploaded_file = st.file_uploader("Upload SME Allocation File (.xlsx or .csv)", type=["xlsx", "csv"])
with c2:
    master = load_master()
    if master.empty:
        st.warning("SME Master is empty. Add SMEs on the **SME Master** page.")
    else:
        st.success(f"Loaded SME Master: {len(master)} rows")

alloc_df = None
if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            alloc_df = pd.read_csv(uploaded_file)
        else:
            alloc_df = pd.read_excel(uploaded_file, engine="openpyxl")
        st.success(f"Loaded {len(alloc_df)} allocation rows from {uploaded_file.name}")
    except Exception as e:
        st.error(f"Could not read allocation file: {e}")

if alloc_df is not None:
    st.dataframe(alloc_df.head(), use_container_width=True)

st.divider()

# ---- SME selection from Master ----
master_active = master[master["Status"] == "Active"].copy()
subjects = sorted(master_active["Subject"].dropna().unique().tolist())
colA, colB = st.columns([1, 2])
with colA:
    subj_choice = st.selectbox("Subject", ["(All)"] + subjects, index=0)
with colB:
    # filter SMEs by subject if chosen
    pool = master_active if subj_choice == "(All)" else master_active[master_active["Subject"] == subj_choice]
    pool = pool.sort_values(["Name"])
    sme_names = (pool["Prefix"].fillna("") + " " + pool["Salutation"].fillna("") + " " + pool["Name"].fillna("")).str.replace(r"\s+", " ", regex=True)
    # keep both label and email for later
    labels = (sme_names + "  ⟶  " + pool["Email"]).tolist()
    choice = st.selectbox("SME", labels if len(labels) else ["(none)"])

if alloc_df is None or master_active.empty or choice == "(none)":
    st.stop()

# pick selected SME row
sel_email = choice.split("⟶")[-1].strip()
sel_row = pool[pool["Email"] == sel_email].iloc[0]

# count this SME's questions from allocation (if a matching column exists)
count = 0
if "SME Name" in alloc_df.columns:
    # try matching by Name in allocation
    count = int((alloc_df["SME Name"].fillna("") == sel_row["Name"]).sum())

deadline = (datetime.now() + timedelta(days=3)).strftime("%d-%b-%Y")
greeting_name = " ".join([str(sel_row.get("Prefix","")).strip(),
                          str(sel_row.get("Salutation","")).strip(),
                          str(sel_row.get("Name","")).strip()]).strip()
subject_line = f"[QC Assignment] SME {sel_row['Name']} – {count} Questions Pending Review"

body = f"""Dear {greeting_name},

Greetings from Make-A-Mark Academy!

You have been assigned {count} questions for bilingual QC verification.
Please review and update the Tamil translation where necessary.

Kindly return the verified file by {deadline}.

SME details on record:
• Subject: {sel_row.get('Subject','')}
• District/Taluk/Place: {sel_row.get('District','')}/{sel_row.get('Taluk','')}/{sel_row.get('Place','')}
• Pin: {str(sel_row.get('Pin',''))}
• WhatsApp: {str(sel_row.get('WhatsApp',''))}

Best regards,
MAM Content Coordination Team
"""

st.subheader("✉️ Email Preview")
ta = st.text_area("Body", body, height=260, key="email_body_area")
copy_button("email_body_area", "Copy email")

st.text_input("Subject", subject_line, key="email_subject", help="You can tweak before copying/downloading")

# ---- downloads (single and bulk) ----
cdl1, cdl2 = st.columns(2)
with cdl1:
    st.download_button(
        "⬇️ Download Email (TXT)",
        data=ta.encode("utf-8"),
        file_name=f"email_{sel_row['Name']}.txt",
        mime="text/plain",
    )

with cdl2:
    # one-row DataFrame for this SME
    one = pd.DataFrame([{
        "To": sel_row["Email"],
        "Subject": st.session_state.get("email_subject", subject_line),
        "Body": ta
    }])
    # CSV
    st.download_button(
        "⬇️ Download CSV (1 row)",
        data=one.to_csv(index=False, encoding="utf-8-sig"),
        file_name=f"emails_{sel_row['Name']}.csv",
        mime="text/csv",
    )

# Optional: bulk export for all SMEs of the filtered pool (use same count heuristic)
with st.expander("Bulk export for all SMEs in current filter"):
    bulk_rows = []
    for _, r in pool.iterrows():
        nm = r["Name"]
        c = 0
        if "SME Name" in alloc_df.columns:
            c = int((alloc_df["SME Name"].fillna("") == nm).sum())
        subj = f"[QC Assignment] SME {nm} – {c} Questions Pending Review"
        greet = " ".join([str(r.get("Prefix","")).strip(),
                          str(r.get("Salutation","")).strip(),
                          str(nm).strip()]).strip()
        b = f"""Dear {greet},

Greetings from Make-A-Mark Academy!

You have been assigned {c} questions for bilingual QC verification.
Please review and update the Tamil translation where necessary.

Kindly return the verified file by {deadline}.

Best regards,
MAM Content Coordination Team
"""
        bulk_rows.append({"To": r["Email"], "Subject": subj, "Body": b})

    bulk_df = pd.DataFrame(bulk_rows)
    c_b1, c_b2 = st.columns(2)
    with c_b1:
        st.download_button(
            "⬇️ Download Bulk CSV",
            data=bulk_df.to_csv(index=False, encoding="utf-8-sig"),
            file_name="emails_bulk.csv",
            mime="text/csv",
        )
    with c_b2:
        buf = io.BytesIO()
        bulk_df.to_excel(buf, index=False)
        st.download_button(
            "⬇️ Download Bulk Excel",
            data=buf.getvalue(),
            file_name="emails_bulk.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
