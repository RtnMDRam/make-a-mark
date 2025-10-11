# pages/05_Drive_Link_Input.py
import re
import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Drive Link Input", page_icon="🔗", layout="wide")

st.title("🔗 Load QB from Google Drive (Link)")
st.caption("Paste a **shareable link** to a .xlsx or .csv file in Google Drive. "
           "Make sure the file's sharing is set to **Anyone with the link → Viewer**.")

# ---------- helpers ----------
def extract_drive_file_id(url: str) -> str | None:
    """
    Accepts common Google Drive link styles and returns the file ID.
    Examples:
      https://drive.google.com/file/d/FILE_ID/view?usp=sharing
      https://drive.google.com/open?id=FILE_ID
      https://drive.google.com/uc?id=FILE_ID&export=download
    """
    if not url:
        return None
    # /d/<id>/ pattern
    m = re.search(r"/d/([a-zA-Z0-9_-]{10,})", url)
    if m:
        return m.group(1)
    # id=<id> pattern
    m = re.search(r"[?&]id=([a-zA-Z0-9_-]{10,})", url)
    if m:
        return m.group(1)
    return None

def read_bytes_to_df(name_hint: str, raw: bytes) -> pd.DataFrame:
    """Try Excel first, then CSV."""
    buf = io.BytesIO(raw)
    # Excel?
    try:
        return pd.read_excel(buf, engine="openpyxl")
    except Exception:
        pass
    # CSV (recreate buffer)
    return pd.read_csv(io.BytesIO(raw))

def save_into_session(df: pd.DataFrame, source: str, filename: str):
    st.session_state["qb_df"] = df
    st.session_state["qb_source"] = source
    st.session_state["qb_filename"] = filename

# ---------- UI ----------
with st.form("drive_loader"):
    link = st.text_input("Paste Google Drive link", placeholder="https://drive.google.com/file/d/…/view?usp=sharing")
    submitted = st.form_submit_button("Fetch file")

if submitted:
    file_id = extract_drive_file_id(link)
    if not file_id:
        st.error("Couldn’t detect a Google Drive file ID. Please paste a standard Drive share link.")
    else:
        # build direct download URL
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        try:
            # use pandas' read_* via requests-like fetch with pd.read_*? We’ll pull bytes with st.experimental_connection? 
            # Simpler: use urllib to fetch raw bytes (works on Streamlit Cloud).
            import urllib.request
            with urllib.request.urlopen(url) as resp:
                raw = resp.read()

            df = read_bytes_to_df("drive_file", raw)
            if df is None or df.empty:
                st.warning("The file was downloaded but appears empty or unreadable.")
            else:
                save_into_session(df, source="drive", filename=f"drive:{file_id}")
                st.success(f"✅ Loaded {len(df)} rows from Drive file `{file_id}`.")
                st.dataframe(df.head(30), use_container_width=True)
                st.info("You can now switch to **Admin View** or **SME Editor** to continue.")
        except Exception as e:
            st.error(f"Download/read failed: {e}")

st.divider()
st.subheader("Alternative: Upload the file directly")
up = st.file_uploader("Upload .xlsx or .csv", type=["xlsx", "csv"])
if up is not None:
    try:
        raw = up.read()
        df = read_bytes_to_df(up.name, raw)
        save_into_session(df, source="upload", filename=up.name)
        st.success(f"✅ Loaded {len(df)} rows from uploaded file `{up.name}`.")
        st.dataframe(df.head(30), use_container_width=True)
        st.info("You can now switch to **Admin View** or **SME Editor** to continue.")
    except Exception as e:
        st.error(f"Could not read uploaded file: {e}")
