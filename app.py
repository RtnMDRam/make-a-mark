# app.py — make-a-mark (SME Allocation • offline, one-file)
# Requirements (exact):
#   streamlit==1.38.0
#   pandas==2.2.2
#   openpyxl==3.1.2

from __future__ import annotations
import io
import re
import zipfile
from typing import List, Tuple, Dict
import pandas as pd
import streamlit as st

# ----------------------------- utils -----------------------------
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

def clean_sme_label(name: str) -> str:
    n = (name or "")
    for tag in ["Mr.", "Mr", "Dr.", "Dr", "Mrs.", "Mrs", "Ms.", "Ms"]:
        n = n.replace(tag, "")
    return sanitize(n.strip())

def sme_filename(base: str, sme_name: str, start_row: int, end_row: int) -> str:
    return f"{base}__SME-{clean_sme_label(sme_name)}__rows-{start_row}-{end_row}.xlsx"

def read_uploaded(uploaded) -> pd.DataFrame:
    name = (uploaded.name or "").lower()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded)        # needs openpyxl
    return pd.read_csv(uploaded)

def to_excel_bytes(df: pd.DataFrame, sheet_name="Sheet1") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        df.to_excel(xw, index=False, sheet_name=sheet_name)
    buf.seek(0)
    return buf.read()

def zip_bytes(files: List[Tuple[str, bytes]]) -> bytes:
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fname, content in files:
            zf.writestr(fname, content)
    mem.seek(0)
    return mem.read()

def parse_range_from_filename(name: str) -> Tuple[int, int]:
    """
    Extract rows-{start}-{end} from filename.
    Accepts either ...__rows-61-120.xlsx or ...__rows-61-120__qc.xlsx
    """
    m = re.search(r"__rows-(\d+)-(\d+)(?:__qc)?\.xlsx$", name)
    if m:
        return int(m.group(1)), int(m.group(2))
    return (-1, -1)

def detect_tamil_columns(df: pd.DataFrame) -> List[str]:
    """
    Keep 'id' (any case) + any columns whose header contains Tamil characters (U+0B80–U+0BFF).
    If nothing found, fallback to full df.
    """
    out = []
    id_col = None
    for c in df.columns:
        if str(c).lower().strip() == "id":
            id_col = c
            break
    if id_col is not None:
        out.append(id_col)
    for c in df.columns:
        if any("\u0B80" <= ch <= "\u0BFF" for ch in str(c)):
            if c not in out:
                out.append(c)
    return out if out else list(df.columns)

# ------------------------------ UI --------------------------------
st.set_page_config(page_title="make-a-mark — SME Allocation (offline)", layout="wide")
st.title("🟣 make-a-mark — SME Allocation (offline)")
st.caption(
    "Split master into per-SME Excel files, then re-assemble QC returns — all offline. "
    "Outgoing: `bl_..._qb__SME-<Name>__rows-<s>-<e>.xlsx`. "
    "SMEs return with `__qc.xlsx`. Final outputs: `bl_..._qb__qc.xlsx` and `mam_..._qb__qc.xlsx`."
)

# -------------------------- header / master --------------------------
with st.form("meta_form", clear_on_submit=False):
    c1, c2, c3, c4 = st.columns(4)
    subject = c1.text_input("Subject", value="bio")
    grade   = c2.text_input("Grade", value="g11")
    unit    = int(c3.number_input("Unit #", min_value=0, value=4, step=1))
    chap    = int(c4.number_input("Chapter # (0 allowed)", min_value=0, value=9, step=1))
    lesson  = st.text_input("Lesson / short label (used in file name)", value="the_tissues")

    uploaded = st.file_uploader("Upload master file (CSV/XLSX)", type=["csv", "xlsx", "xls"])
    submitted = st.form_submit_button("Load master file")

df = None
if submitted:
    if not uploaded:
        st.error("Please upload a file.")
    else:
        try:
            df = read_uploaded(uploaded)
            st.success(f"Loaded {len(df)} rows.")
            st.dataframe(df.head(10), use_container_width=True)
        except Exception as e:
            st.error(f"Couldn't read the file: {e}")

st.markdown("---")

# ------------------------------ SME ranges ---------------------------
st.subheader("👩‍🏫 SME Details")
num_smes = int(st.number_input("Number of SMEs", min_value=1, max_value=30, value=1, step=1))
smes: List[Tuple[str, int, int]] = []

for i in range(num_smes):
    st.markdown(f"**SME {i+1}**")
    a, b, c = st.columns([2,1,1])
    name = a.text_input(f"Name for SME {i+1}", key=f"sme_name_{i}")
    start_row = int(b.number_input(f"Start row for SME {i+1}", key=f"sme_start_{i}", min_value=1, value=1))
    end_row   = int(c.number_input(f"End row for SME {i+1}",   key=f"sme_end_{i}",   min_value=1, value=1))
    smes.append((name, start_row, end_row))

if st.button("📋 Show Allocation Summary"):
    st.subheader("✅ Allocation Summary")
    for i, (name, s, e) in enumerate(smes):
        st.write(f"**SME {i+1}: {name} → Rows {s} to {e}**")

# --------------------------- generate ZIP ----------------------------
st.markdown("")
left = st.columns([1,5])[0]
if left.button("📦 Generate SME Files (ZIP)", disabled=("df" not in locals() and df is None)):
    if df is None:
        st.warning("Upload your master file first.")
    else:
        base = base_name(subject, grade, unit, chap, lesson, bilingual=True)
        out: List[Tuple[str, bytes]] = []

        # Validate for simple mistakes (optional overlap warning)
        used_segments = []
        for name, s, e in smes:
            if not str(name).strip():
                st.error("Every SME must have a name.")
                st.stop()
            if s > e:
                st.error(f"Invalid range for {name}: start({s}) > end({e}).")
                st.stop()
            used_segments.append((s, e, name))

        # Build files
        for s, e, name in used_segments:
            lo, hi = max(1, s), max(1, e)
            part = df.iloc[lo-1:hi].copy()
            fname = sme_filename(base, name, lo, hi)
            out.append((fname, to_excel_bytes(part)))

        z = zip_bytes(out)
        st.success(f"Generated {len(out)} SME files.")
        st.download_button(
            "⬇️ Download SME ZIP",
            data=z,
            file_name=f"{base}__sme_split.zip",
            mime="application/zip",
            use_container_width=True
        )

st.caption("SMEs must return the same filename plus `__qc` before `.xlsx` (e.g., `...__rows-61-120__qc.xlsx`).")

# ----------------------- QC return & assembly ------------------------
st.markdown("---")
st.subheader("🧩 QC Return & Assembly")

# Expected set from allocations
expected = {(s, e) for _, s, e in smes if s and e}
exp_txt = ", ".join([f"{a}-{b}" for (a, b) in sorted(expected)]) or "—"
st.caption(f"**Expected ranges:** {exp_txt}")

qc_files = st.file_uploader("Drop QC-returned files (.xlsx) here", type=["xlsx"], accept_multiple_files=True)

received_ranges = set()
qc_parts: Dict[Tuple[int, int], bytes] = {}
ignored: List[str] = []

if qc_files:
    for f in qc_files:
        nm = f.name
        s, e = parse_range_from_filename(nm)
        data = f.read()
        if s > 0 and e >= s:
            received_ranges.add((s, e))
            qc_parts[(s, e)] = data
        else:
            ignored.append(nm)

rec_txt = ", ".join([f"{a}-{b}" for (a, b) in sorted(received_ranges)]) or "—"
miss = sorted(list(expected - received_ranges))
miss_txt = ", ".join([f"{a}-{b}" for (a, b) in miss]) or "—"

c1, c2, c3 = st.columns(3)
c1.metric("Received", rec_txt)
c2.metric("Missing", miss_txt)
c3.metric("Ignored files", len(ignored))

if ignored:
    with st.expander("Ignored files (name format not recognized)"):
        for nm in ignored:
            st.write(nm)

def assemble_and_offer_downloads(qc_parts: Dict[Tuple[int,int], bytes], base: str):
    if not qc_parts:
        st.error("No QC files to assemble.")
        return

    # Read and stitch in order of start row
    frames = []
    for (s, e) in sorted(qc_parts.keys(), key=lambda x: x[0]):
        try:
            frames.append(pd.read_excel(io.BytesIO(qc_parts[(s, e)])))
        except Exception as ee:
            st.error(f"Couldn't read one QC file ({s}-{e}): {ee}")
            return
    merged = pd.concat(frames, ignore_index=True)

    # Final names
    bl_name = f"{base}_qb__qc.xlsx"
    mam_name = bl_name.replace("bl_", "mam_", 1)

    # Bilingual bytes
    bio_bl = io.BytesIO()
    with pd.ExcelWriter(bio_bl, engine="openpyxl") as xw:
        merged.to_excel(xw, index=False, sheet_name="Sheet1")
    bio_bl.seek(0)

    # Tamil-only bytes (auto-detect columns)
    keep_cols = detect_tamil_columns(merged)
    mam_df = merged[keep_cols] if set(keep_cols).issubset(merged.columns) else merged.copy()
    bio_mam = io.BytesIO()
    with pd.ExcelWriter(bio_mam, engine="openpyxl") as xw:
        mam_df.to_excel(xw, index=False, sheet_name="Sheet1")
    bio_mam.seek(0)

    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "⬇️ Download Bilingual (bl_...__qc.xlsx)",
            data=bio_bl.getvalue(),
            file_name=bl_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with d2:
        st.download_button(
            "⬇️ Download Tamil-only (mam_...__qc.xlsx)",
            data=bio_mam.getvalue(),
            file_name=mam_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    st.success("Final files ready.")

auto_ready = (expected and received_ranges == expected)
assemble_btn = st.button("🧵 Assemble Final Files", disabled=not qc_parts and not auto_ready)

if assemble_btn or auto_ready:
    base = base_name(subject, grade, unit, chap, lesson, bilingual=True)
    assemble_and_offer_downloads(qc_parts, base)
