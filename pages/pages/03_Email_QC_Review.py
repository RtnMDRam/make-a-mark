# ================================
# 03_Email_QC_Review.py
# ================================

import io
import zipfile
from datetime import datetime

import pandas as pd
import streamlit as st


# ---------- Page ----------
st.set_page_config(page_title="Email QC Review", page_icon="✉️", layout="wide")
st.title("✉️ Email QC Review")
st.caption("View and download QC email drafts for SME feedback.")


# ---------- Helpers ----------
def find_col(candidates, cols):
    """Return the first column from `candidates` that exists in `cols` (case-insensitive)."""
    lc = {c.lower(): c for c in cols}
    for name in candidates:
        if name.lower() in lc:
            return lc[name.lower()]
    return None


def assigned_count_for_rows(rows: pd.DataFrame) -> int:
    """Pick the best available way to compute the assigned question count."""
    # 1) Direct column
    ac = find_col(["AssignedCount", "Assigned Count"], rows.columns)
    if ac and pd.notnull(rows.iloc[0].get(ac, None)):
        try:
            return int(rows.iloc[0][ac])
        except Exception:
            pass

    # 2) EndRow - StartRow + 1
    start_col = find_col(["StartRow", "Start Row"], rows.columns)
    end_col = find_col(["EndRow", "End Row"], rows.columns)
    if start_col and end_col:
        try:
            s = int(rows.iloc[0][start_col])
            e = int(rows.iloc[0][end_col])
            return max(0, e - s + 1)
        except Exception:
            pass

    # 3) Fallback: number of rows for this SME
    return len(rows)


def build_email_text(sme_name: str, count: int, subject_text: str, file_name: str, rows: pd.DataFrame) -> str:
    today = datetime.now().strftime("%d-%b-%Y")
    subj_col = find_col(["Subject"], rows.columns)
    reported_subject = rows.iloc[0][subj_col] if subj_col and len(rows) else "N/A"

    return f"""Dear {sme_name},

Greetings from **Make-A-Mark Academy**!

You have been assigned **{count} questions** for bilingual QC verification.
Please review and update the Tamil translation where necessary.

Kindly return the verified file by **{today}**.

Best regards,  
**MAM Content Coordination Team**

---

🗂️ File: `{file_name}`
📘 Subject/Unit: {reported_subject}

---

_This is an auto-generated message for SME QC tracking._
""", f"[QC Assignment] {sme_name} — {count} Questions Pending Review" if not subject_text else subject_text


# ---------- Upload ----------
uploaded_file = st.file_uploader("Upload SME Allocation File (.xlsx or .csv)", type=["xlsx", "csv"])

if not uploaded_file:
    st.info("Please upload an allocation file first.")
    st.stop()

# Read file
try:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    st.success(f"Loaded {len(df)} records from {uploaded_file.name}")
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

st.dataframe(df.head(), use_container_width=True)

# Locate important columns
sme_col = find_col(["SME Name", "SME"], df.columns)
if not sme_col:
    st.error("Could not find an SME column. Expected one of: 'SME Name', 'SME'.")
    st.stop()

# ---------- SME picker ----------
st.subheader("✉️ Generate QC Email")

sme_names = sorted([str(x) for x in df[sme_col].dropna().unique().tolist()])
sme_choice = st.selectbox("Select SME", sme_names, index=0 if sme_names else None)

# Optional editable email subject (blank = auto)
custom_subject = st.text_input(
    "Email Subject (leave blank for automatic)",
    value=""
)

if sme_choice:
    sme_rows = df[df[sme_col] == sme_choice].reset_index(drop=True)
    count = assigned_count_for_rows(sme_rows)
    email_body, final_subject = build_email_text(
        sme_name=sme_choice,
        count=count,
        subject_text=custom_subject.strip(),
        file_name=uploaded_file.name,
        rows=sme_rows,
    )

    # Preview + download for this SME
    st.markdown("### ✉️ Email Preview")
    st.text_area("Generated Email", email_body, height=280)

    col_a, col_b = st.columns(2)
    with col_a:
        st.write(f"**Subject:** {final_subject}")
    with col_b:
        st.download_button(
            "📥 Download This Email (.txt)",
            data=email_body.encode("utf-8"),
            file_name=f"QC_Email_{sme_choice.replace(' ', '_')}.txt",
            mime="text/plain",
        )

# ---------- Batch export (all SMEs) ----------
st.markdown("---")
st.markdown("### 📦 Download all SME emails (.zip)")

if st.button("Create ZIP"):
    if not len(sme_names):
        st.warning("No SMEs found in the file.")
    else:
        memfile = io.BytesIO()
        with zipfile.ZipFile(memfile, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for name in sme_names:
                rows = df[df[sme_col] == name]
                count = assigned_count_for_rows(rows)
                body, subject_for_one = build_email_text(
                    sme_name=name,
                    count=count,
                    subject_text="",  # use auto for batch
                    file_name=uploaded_file.name,
                    rows=rows,
                )
                zf.writestr(f"QC_Email_{name.replace(' ', '_')}.txt", body)

        memfile.seek(0)
        st.download_button(
            "⬇️ Download ZIP",
            data=memfile,
            file_name="QC_Emails_All_SMEs.zip",
            mime="application/zip",
        )
