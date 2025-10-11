# pages/02_Email_QC_Generator.py
import io
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html

st.set_page_config(page_title="Email QC Generator", page_icon="✉️", layout="wide")
st.title("✉️ Email QC Generator")
st.caption("Build per-SME emails and WhatsApp texts from the current allocation table.")

# --- iPad keyboard friendly tweaks (same pattern we used) ---
html("""
<style>
  .block-container { padding-bottom: 35vh; }
  section[data-testid="stSidebar"] .block-container { padding-bottom: 20vh; }
</style>
""")

# ---- guards ----
if "alloc_df" not in st.session_state or st.session_state.alloc_df is None or st.session_state.alloc_df.empty:
    st.warning("No allocation found. Go to **Admin View** and create/save an allocation first.")
    st.stop()

alloc_df = st.session_state.alloc_df.copy()

# Try to recover original dataset name / row count for context
dataset_name = st.session_state.get("dataset_name", "Question Bank")
total_rows = st.session_state.get("total_rows", int(alloc_df["AssignedCount"].sum()))

# Optional: join with SME Master to enrich phone/location if available
master = st.session_state.get("sme_master", pd.DataFrame())
if not master.empty:
    # ensure unique emails (latest record wins)
    master = master.sort_values("Email").drop_duplicates("Email", keep="last")

    # match by Email (safe if column exists)
    if "Email" in master.columns:
        cols_keep = [c for c in master.columns if c in
                     ["Email", "Name", "Subject", "Place", "Taluk", "District", "WhatsApp", "Pin"]]
        alloc_df = alloc_df.merge(master[cols_keep], on="Email", how="left", suffixes=("", "_m"))

# Sidebar: global email settings
with st.sidebar:
    st.header("✉️ Settings")
    default_subject = f"[QC Allocation] {dataset_name} — Rows assigned"
    subject_line = st.text_input("Email subject", value=default_subject)
    greet = st.text_input("Greeting", value="Dear {name},")
    closing = st.text_area("Closing", value="Thanks for your support.\n— Mission Aspire")
    include_location = st.checkbox("Include location line (if available)", value=True)
    include_whatsapp = st.checkbox("Include WhatsApp number (if available)", value=True)

st.subheader("📋 Current Allocation")
st.dataframe(alloc_df, use_container_width=True)

st.markdown("---")
st.subheader("📨 Generate messages per SME")

# Helper: build per-SME email body and WhatsApp text
def build_text(row: pd.Series) -> dict:
    name = (row.get("SME") or row.get("Name") or "").strip() or "Sir/Madam"
    email = row.get("Email", "").strip()
    s = int(row.get("StartRow", 0) or 0)
    e = int(row.get("EndRow", 0) or 0)
    count = int(row.get("AssignedCount", max(0, e - s + 1)) or 0)

    # Optional lines
    extra_lines = []
    if include_location:
        parts = [row.get("Place", ""), row.get("Taluk", ""), row.get("District", "")]
        loc = ", ".join([p for p in parts if isinstance(p, str) and p.strip()])
        if loc:
            extra_lines.append(f"Location: {loc}")
        pin = row.get("Pin", "")
        if isinstance(pin, (int, float)) or (isinstance(pin, str) and pin.strip().isdigit()):
            extra_lines.append(f"PIN: {str(pin).split('.')[0]}")

    wa = str(row.get("WhatsApp", "") or "").strip()
    if include_whatsapp and wa:
        extra_lines.append(f"WhatsApp: {wa}")

    extra = ("\n".join(extra_lines)).strip()
    if extra:
        extra = "\n" + extra

    body = (
        f"{greet.format(name=name)}\n\n"
        f"You have been assigned **{count}** rows from **{dataset_name}** "
        f"(rows **{s}–{e}**, inclusive).\n"
        f"Please review and update the status as you progress.{extra}\n\n"
        f"{closing}"
    )

    # WhatsApp (leaner)
    wa_text = (
        f"{name}, {count} rows assigned from {dataset_name} "
        f"(rows {s}–{e}). Thanks! — Mission Aspire"
    )
    return {"subject": subject_line, "body": body, "whatsapp": wa_text, "email": email}

# Build SME selector
sme_options = [f"{r.SME or r.get('Name','')} — {r.Email}" for _, r in alloc_df.iterrows()]
selected = st.selectbox("Choose SME", options=sme_options, index=0)

# Resolve selected row
sel_idx = sme_options.index(selected)
row = alloc_df.iloc[sel_idx]
texts = build_text(row)

# Show composed email + WhatsApp
c1, c2 = st.columns(2)
with c1:
    st.caption("Email Subject")
    st.code(texts["subject"])
    st.caption("Email Body")
    st.text_area("Body (editable/copyable)", value=texts["body"], height=280, key="email_body")

with c2:
    st.caption("WhatsApp Text")
    st.text_area("WhatsApp (copy)", value=texts["whatsapp"], height=140, key="wa_body")

    # Per-SME CSV of assigned rows (if the original file is present)
    if "qb_df" in st.session_state and st.session_state["qb_df"] is not None:
        qb = st.session_state["qb_df"]
        s = int(row.get("StartRow", 0) or 0)
        e = int(row.get("EndRow", 0) or 0)
        if s >= 1 and e >= s and e <= len(qb):
            part = qb.iloc[s-1:e].reset_index(drop=True)
            buf = io.BytesIO(part.to_csv(index=False).encode("utf-8-sig"))
            st.download_button(
                label="⬇️ Download this SME's rows (CSV)",
                data=buf,
                file_name=f"{(row.get('SME') or 'SME').replace(' ','_')}_{s}-{e}.csv",
                mime="text/csv",
            )
        else:
            st.info("Assigned Start/End rows are out of range for the loaded file.")

st.markdown("---")
st.success("Ready! Copy the email/WhatsApp text above, or download the SME’s CSV.")
