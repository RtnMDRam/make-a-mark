# pages/05_Drive_Link_Input.py
import re
import io
import pandas as pd
import streamlit as st

# NOTE: requires "requests" in requirements.txt
import requests

st.set_page_config(page_title="Load from Google Drive", page_icon="🔗", layout="wide")
st.title("🔗 Load Bilingual QB from Google Drive")

st.markdown("""
Paste a **Google Drive link** to an Excel/CSV file and click **Load file**.

**Works with links like:**
- `https://drive.google.com/file/d/<FILE_ID>/view?usp=sharing`
- `https://drive.google.com/open?id=<FILE_ID>`
- `https://drive.google.com/uc?id=<FILE_ID>&export=download`

> Make sure the file’s sharing is set to **Anyone with the link → Viewer**.
""")

# ---------- helpers ----------
ID_PATTERNS = [
    r"drive\.google\.com/file/d/([a-zA-Z0-9_-]+)",      # /file/d/<ID>/
    r"[?&]id=([a-zA-Z0-9_-]+)",                         # id=<ID>
    r"[?&]export=download&id=([a-zA-Z0-9_-]+)",         # export=download&id=<ID>
]

def extract_file_id(url: str) -> str | None:
    for pat in ID_PATTERNS:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None

def drive_download(file_id: str) -> tuple[bytes, str]:
    """
    Robust Google Drive downloader that follows Drive's confirm token flow.
    Returns (content_bytes, suggested_filename).
    """
    sess = requests.Session()
    base = "https://drive.google.com/uc?export=download"
    params = {"id": file_id}
    r = sess.get(base, params=params, stream=True)
    r.raise_for_status()

    # Large files show a confirm token in HTML
    token = None
    if "text/html" in r.headers.get("Content-Type", "") and "confirm=" in r.text:
        m = re.search(r"confirm=([0-9A-Za-z_]+)", r.text)
        if m:
            token = m.group(1)

    if token:
        params["confirm"] = token
        r = sess.get(base, params=params, stream=True)
        r.raise_for_status()

    # try to get filename
    cd = r.headers.get("Content-Disposition", "")
    name_match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^\";]+)"?', cd)
    filename = name_match.group(1) if name_match else f"{file_id}.bin"

    content = r.content
    return content, filename

# ---------- UI ----------
col = st.container(border=True)
url = col.text_input("Paste Google Drive link", placeholder="https://drive.google.com/file/d/FILE_ID/view?usp=sharing")
go = col.button("Load file", type="primary")

if go:
    if not url.strip():
        st.error("Please paste a Google Drive link.")
        st.stop()

    file_id = extract_file_id(url)
    if not file_id:
        st.error("Could not find a file ID in the link. Please paste a standard Google Drive share link.")
        st.stop()

    with st.spinner("Fetching file from Google Drive..."):
        try:
            data_bytes, name = drive_download(file_id)
        except Exception as e:
            st.error(f"Download failed: {e}")
            st.stop()

    st.success(f"Downloaded **{name}**  •  {len(data_bytes):,} bytes")

    # Try reading as Excel, then CSV
    df = None
    error_msg = None
    bio = io.BytesIO(data_bytes)

    # Try Excel first
    try:
        bio.seek(0)
        df = pd.read_excel(bio, engine="openpyxl")
        kind = "Excel"
    except Exception as ex_xlsx:
        try:
            bio.seek(0)
            # let pandas auto-detect CSV (utf-8) — adjust if needed later
            df = pd.read_csv(bio)
            kind = "CSV"
        except Exception as ex_csv:
            error_msg = f"Not a readable Excel/CSV file.\n\nExcel error: {ex_xlsx}\nCSV error: {ex_csv}"

    if df is None:
        st.error(error_msg or "Could not read file.")
        st.stop()

    st.info(f"Loaded as **{kind}**. Preview below:")
    st.dataframe(df.head(30), use_container_width=True)

    # Bridge for Admin View: stash the dataframe & a BytesIO in session_state
    st.session_state["qb_df"] = df               # DataFrame for direct use
    st.session_state["qb_file_bytes"] = data_bytes  # original bytes (if needed)

    st.success("✅ File is ready to use. Open **Admin View** (left sidebar) to proceed.")
    if st.button("Go to Admin View →"):
        try:
            st.switch_page("pages/01_Admin_View.py")
        except Exception:
            st.info("If switch didn't work, click **Admin View** in the left sidebar.")
