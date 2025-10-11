# =========================
# Make-A-Mark Streamlit App
# =========================

from __future__ import annotations
import streamlit as st

st.set_page_config(
    page_title="Make-A-Mark Academy",
    page_icon="🎓",
    layout="wide"
)

# Introductory block — displayed before the main dashboard
st.markdown("""
# 🎓 **Make-A-Mark Academy**
### Mission Aspire | Bilingual NEET & JEE Program
st.caption("**மேக்-அ-மார்க் அகாடமி – தாய் மொழி கல்வித் தளம் (ஆங்கிலம்–தமிழ்)**")

Welcome to the **Admin & Content Processing Dashboard**.  
This platform enables centralized monitoring and bilingual content management for
NEET and JEE preparation across participating institutions.

**Key Modules:**

- 🧑‍🏫 **SME Allocation Dashboard** – Assign, track, and manage content contributors.  
  <span style="color:gray"><i>ஆசிரியர்கள் ஒதுக்கீட்டு பலகை</i></span>  

- 📘 **Question Bank Processor** – Generate bilingual (English–Tamil) datasets.  
  <span style="color:gray"><i>தமிழ் மொழி / கேள்விகளின் தொகுப்பு செயலி</i></span>  

- 🧾 **Reports Panel** – Export SME work summaries and progress metrics.  
  <span style="color:gray"><i>அறிக்கைகள் & முன்னேற்றக் கண்காணிப்பு பலகை</i></span>  

---
""")
# ================================
# SME Allocation Dashboard (inline)
# ================================
import io
import pandas as pd
import streamlit as st

st.divider()
st.header("🧑‍🏫 SME Allocation Dashboard")

# ---------- 1) Load bilingual file ----------
up = st.file_uploader("Upload bilingual QB file (.xlsx or .csv)", type=["xlsx", "csv"])
df = None
read_err = None
if up is not None:
    try:
        if up.name.lower().endswith(".csv"):
            df = pd.read_csv(up)
        else:
            try:
                df = pd.read_excel(up, engine="openpyxl")
            except Exception:
                # fallback if openpyxl missing on cloud
                df = pd.read_excel(up)
        st.success(f"Loaded **{up.name}** with **{len(df)}** rows and **{len(df.columns)}** columns.")
        with st.expander("Preview first 30 rows", expanded=False):
            st.dataframe(df.head(30), use_container_width=True)
    except Exception as e:
        read_err = str(e)
        st.error(f"Could not read file: {e}\nIf this is an Excel file, add **openpyxl>=3.1** to requirements.txt.")

# ---------- 2) Column mapping (subject/unit/chapter) ----------
if df is not None and not df.empty:
    st.subheader("Select identifiers")
    # naive guesses
    guess = lambda keys: next((c for c in df.columns if c.lower() in keys), None)
    col_subject = st.selectbox("Subject column", options=["(none)"] + list(df.columns),
                               index=(["(none)"] + list(df.columns)).index(guess({"subject","sub"})) if guess({"subject","sub"}) in df.columns else 0)
    col_unit    = st.selectbox("Unit column", options=["(none)"] + list(df.columns),
                               index=(["(none)"] + list(df.columns)).index(guess({"unit","unit_no","unitno"})) if guess({"unit","unit_no","unitno"}) in df.columns else 0)
    col_chap    = st.selectbox("Chapter column", options=["(none)"] + list(df.columns),
                               index=(["(none)"] + list(df.columns)).index(guess({"chapter","chap","chapter_name"})) if guess({"chapter","chap","chapter_name"}) in df.columns else 0)

    # filters (optional)
    left, mid, right = st.columns(3)
    with left:
        subj_val = st.selectbox("Subject", sorted(df[col_subject].dropna().unique()) if col_subject != "(none)" else ["(all)"])
    with mid:
        unit_val = st.selectbox("Unit", sorted(df[col_unit].dropna().unique()) if col_unit != "(none)" else ["(all)"])
    with right:
        chap_val = st.selectbox("Chapter", sorted(df[col_chap].dropna().unique()) if col_chap != "(none)" else ["(all)"])

    # apply filters
    mask = pd.Series([True] * len(df))
    if col_subject != "(none)" and subj_val != "(all)":
        mask &= df[col_subject] == subj_val
    if col_unit != "(none)" and unit_val != "(all)":
        mask &= df[col_unit] == unit_val
    if col_chap != "(none)" and chap_val != "(all)":
        mask &= df[col_chap] == chap_val
    work_df = df.loc[mask].reset_index(drop=True)
    st.info(f"Working set: **{len(work_df)}** rows selected.")

    # ---------- 3) SME list ----------
    st.subheader("SMEs")
    n = st.number_input("Number of SMEs", min_value=1, max_value=20, value=3, step=1)
    sme_cols = st.columns(3)
    smes = []
    for i in range(n):
        with sme_cols[i % 3]:
            name = st.text_input(f"SME {i+1} Name", key=f"sme_name_inline_{i}", value=f"SME {i+1}")
            email = st.text_input(f"SME {i+1} Email", key=f"sme_email_inline_{i}", value=f"sme{i+1}@example.com")
        smes.append((name.strip(), email.strip()))

    # ---------- 4) Allocation ----------
    st.subheader("Allocate rows")
    auto = st.checkbox("Auto-allocate equally", value=True)
    alloc_rows = []
    if auto:
        total = len(work_df)
        q, r = divmod(total, n)
        start = 1
        for i in range(n):
            share = q + (1 if i < r else 0)
            end = start + share - 1 if share > 0 else 0
            alloc_rows.append({"SME": smes[i][0], "Email": smes[i][1],
                               "StartRow": start if share > 0 else 0,
                               "EndRow": end if share > 0 else 0})
            start = end + 1
    else:
        # manual template
        for i in range(n):
            alloc_rows.append({"SME": smes[i][0], "Email": smes[i][1],
                               "StartRow": 0, "EndRow": 0})

    alloc_df = pd.DataFrame(alloc_rows)
    st.caption("Edit Start/End rows if needed (1-indexed, inclusive).")
    edited = st.data_editor(
        alloc_df,
        key="alloc_editor_inline",
        use_container_width=True,
        column_config={
            "StartRow": st.column_config.NumberColumn(min_value=0, step=1),
            "EndRow": st.column_config.NumberColumn(min_value=0, step=1),
        }
    )
    # derived & validation
    edited["AssignedCount"] = (edited["EndRow"] - edited["StartRow"] + 1).clip(lower=0)
    total_assigned = int(edited["AssignedCount"].sum())
    unalloc = max(0, len(work_df) - total_assigned)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total rows (filtered)", len(work_df))
    c2.metric("Allocated", total_assigned)
    c3.metric("Unallocated", unalloc)

    # Simple overlap check
    trouble = []
    intervals = []
    for _, r in edited.iterrows():
        s, e = int(r.StartRow), int(r.EndRow)
        if s == 0 and e == 0:
            continue
        for (us, ue) in intervals:
            if not (e < us or s > ue):
                trouble.append(f"Overlap: [{s}, {e}] with [{us}, {ue}]")
        intervals.append((s, e))
    if trouble:
        for t in trouble:
            st.warning(t)
    elif len(work_df) > 0 and total_assigned != len(work_df):
        st.info("Coverage warning: allocation does not match filtered row count.")
    else:
        st.success("✅ Allocation looks consistent.")

    # ---------- 5) Export ----------
    st.subheader("Export")
    # Attach context columns to export (subject/unit/chapter values if chosen)
    meta = {
        "Subject": subj_val if col_subject != "(none)" and subj_val != "(all)" else "",
        "Unit": unit_val if col_unit != "(none)" and unit_val != "(all)" else "",
        "Chapter": chap_val if col_chap != "(none)" and chap_val != "(all)" else "",
        "SourceFile": up.name if up is not None else "",
        "TotalFilteredRows": len(work_df)
    }
    out = edited.assign(**meta)
    csv_bytes = out.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Download Allocation CSV", data=csv_bytes,
                       file_name="sme_allocation.csv", mime="text/csv")

# ------------------------------ utils ------------------------------
SAFE = "-_.()abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def sanitize(s: str) -> str:
    s = str(s or "").strip().replace(" ", "_")
    return "".join(ch for ch in s if ch in SAFE)

def base_name(subject: str, grade: str, unit: int, chap: int, lesson: str, bilingual=True) -> str:
    """
    bl_ for bilingual, mam_ for Tamil-only. chap can be 0.
    Example: bl_bio_g11_unit_4_chap_9_the_tissues_qb
    """
    prefix = "bl" if bilingual else "mam"
    parts = [
        prefix,
        sanitize(subject.lower()),
        sanitize(grade.lower()),
        "unit", str(unit),
        "chap", str(chap),
        sanitize(lesson.lower()),
        "qb",
    ]
    return "_".join(parts)

def strip_salutation(name: str) -> str:
    n = (name or "").replace(".", " ").strip()
    for tok in ["Mr", "Mrs", "Ms", "Dr", "Prof", "Sir", "Madam", "Sri", "Smt"]:
        if n.lower().startswith(tok.lower()+" "):
            n = n[len(tok):].strip()
    return n

def sme_filename(base: str, sme_name: str, start_row: int, end_row: int) -> str:
    clean = sanitize(strip_salutation(sme_name))
    return f"{base}__SME-{clean}__rows-{start_row}-{end_row}.xlsx"

def read_uploaded(uploaded) -> pd.DataFrame:
    name = (uploaded.name or "").lower()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded)          # needs openpyxl
    return pd.read_csv(uploaded)

def write_excel_bytes(df: pd.DataFrame, sheet_name="Sheet1") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        df.to_excel(xw, index=False, sheet_name=sheet_name)
    buf.seek(0)
    return buf.read()

def build_zip(files: List[Tuple[str, bytes]]) -> bytes:
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fname, content in files:
            zf.writestr(fname, content)
    mem.seek(0)
    return mem.read()

# ------------------------------ UI ------------------------------
st.set_page_config(page_title="Make-a-Mark — SME Allocation", layout="wide")
st.title("✍️ Make-a-Mark — SME Allocation (offline)")
st.caption("Upload the master file, assign SMEs by row ranges, download a ZIP of per-SME Excel files. "
           "Returned QC files should keep the same name and append `__qc` before `.xlsx`.")

with st.form("meta", clear_on_submit=False):
    c1, c2, c3, c4 = st.columns(4)
    subject = c1.text_input("Subject", value="bio")
    grade   = c2.text_input("Grade", value="g11")
    unit    = c3.number_input("Unit #", min_value=0, value=4, step=1)
    chap    = c4.number_input("Chapter # (0 allowed)", min_value=0, value=9, step=1)
    lesson  = st.text_input("Lesson / short label (used in file name)", value="the_tissues")

    uploaded = st.file_uploader("Upload the master file (CSV or Excel)", type=["csv","xlsx","xls"])
    submitted = st.form_submit_button("Load file")

df = None
if submitted:
    if uploaded is None:
        st.error("Please upload a file to begin.")
    else:
        try:
            df = read_uploaded(uploaded)
            st.success(f"Loaded {len(df)} rows.")
            st.dataframe(df.head(12), use_container_width=True)
        except Exception as e:
            st.error(f"Couldn't read the file: {e}")

st.markdown("---")

# SME ranges
st.subheader("👩‍🏫 SME Details")
num_smes = st.number_input("Number of SMEs", min_value=1, max_value=20, step=1, value=1)
smes: List[Tuple[str, int, int]] = []

for i in range(int(num_smes)):
    st.markdown(f"**SME {i+1}**")
    c1, c2, c3 = st.columns([2,1,1])
    name = c1.text_input(f"Name for SME {i+1}", key=f"sme_name_{i}")
    start_row = c2.number_input(f"Start row for SME {i+1}", key=f"sme_start_{i}", min_value=1, step=1, value=1)
    end_row   = c3.number_input(f"End row for SME {i+1}", key=f"sme_end_{i}",   min_value=1, step=1, value=1)
    smes.append((name, int(start_row), int(end_row)))

if st.button("📋 Show Allocation Summary"):
    st.subheader("✅ SME Allocation Summary")
    for i, (name, s, e) in enumerate(smes):
        st.write(f"**SME {i+1}: {name or '—'} → Rows {s} to {e}**")

# Generate ZIP
st.markdown("")
left = st.columns([1,5])[0]
if left.button("📦 Generate SME Files (ZIP)", disabled=(df is None)):
    if df is None:
        st.warning("Please upload a master file first.")
    else:
        base = base_name(subject, grade, int(unit), int(chap), lesson, bilingual=True)

        out_files: List[Tuple[str, bytes]] = []
        for (name, s, e) in smes:
            if not (name or "").strip():
                st.error("Every SME must have a name.")
                st.stop()
            if s > e:
                st.error(f"Invalid range for {name}: start({s}) > end({e}).")
                st.stop()
            # 1-based inclusive → 0-based slice
            lo = max(1, s)
            hi = max(1, e)
            slice_df = df.iloc[lo-1:hi].copy()
            fname = sme_filename(base, name, lo, hi)
            out_files.append((fname, write_excel_bytes(slice_df)))

        zip_bytes = build_zip(out_files)
        st.success(f"Generated {len(out_files)} SME files.")
        st.download_button(
            "⬇️ Download SME ZIP",
            data=zip_bytes,
            file_name=f"{base}__sme_split.zip",
            mime="application/zip",
        )

st.caption("Returned files after SME QC should keep the same name and append `__qc` before `.xlsx` "
           "(e.g., `...__rows-61-120__qc.xlsx`).")
