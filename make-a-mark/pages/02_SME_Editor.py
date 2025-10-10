# pages/02_SME_Editor.py
# iPad-first SME Editor – rowwise, horizontal layout + glossary side panel

import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="SME Editor", page_icon="✍️", layout="wide")
st.title("✍️ SME Editor (Row-wise, iPad friendly)")

# ------------- Helpers & Session -------------
if "sme_df" not in st.session_state:
    st.session_state.sme_df = pd.DataFrame()
if "sme_row_idx" not in st.session_state:
    st.session_state.sme_row_idx = 0
if "glossary" not in st.session_state:
    # basic seed – empty glossary
    st.session_state.glossary = []  # list of dicts: {"en": "...", "ta": "...", "source": "core|sme"}
if "sme_suggestions" not in st.session_state:
    st.session_state.sme_suggestions = []  # pending new words from SMEs

def sorted_glossary(items):
    return sorted(items, key=lambda x: x["en"].lower())

def colorize_en_ta(en, ta):
    return (
        f'<div style="margin-bottom:0.25rem;">'
        f'<span style="color:#1f77b4;font-weight:600">{en}</span><br>'
        f'<span style="color:#2ca02c">{ta}</span>'
        f'</div>'
    )

# small CSS: sticky glossary panel + subtle borders
st.markdown("""
<style>
.right-panel { position: sticky; top: 0; max-height: 85vh; overflow-y: auto; padding-left: 0.5rem; }
.card { border: 1px solid #e5e5e5; border-radius: 8px; padding: 0.8rem 1rem; margin-bottom: 0.75rem; }
.suggestion { background: #fff7cc; border: 1px dashed #e0c200; }
.kv { font-size: 0.925rem; line-height: 1.35rem; }
</style>
""", unsafe_allow_html=True)

# ------------- Source data upload -------------
with st.expander("📥 Load source (CSV/XLSX) – must include English & Tamil columns", expanded=(st.session_state.sme_df.empty)):
    up = st.file_uploader("Upload file", type=["csv","xlsx"])
    en_col = ta_col = None
    if up is not None:
        try:
            if up.name.lower().endswith(".csv"):
                df = pd.read_csv(up)
            else:
                try:
                    df = pd.read_excel(up, engine="openpyxl")
                except Exception:
                    df = pd.read_excel(up)
            # guess columns
            cols_lower = {c.lower(): c for c in df.columns}
            en_col = cols_lower.get("english") or next((c for c in df.columns if "eng" in c.lower()), None)
            ta_col = cols_lower.get("tamil") or next((c for c in df.columns if "tam" in c.lower()), None)
            st.success(f"Loaded **{up.name}** with **{len(df)}** rows.")
            if en_col and ta_col:
                st.info(f"Detected columns → English: **{en_col}**, Tamil: **{ta_col}**")
            else:
                st.warning("Couldn’t auto-detect English/Tamil columns. Please map below.")
            # column mapping UI
            col1, col2 = st.columns(2)
            en_map = col1.selectbox("English column", options=list(df.columns), index=list(df.columns).index(en_col) if en_col in df.columns else 0)
            ta_map = col2.selectbox("Tamil column", options=list(df.columns), index=list(df.columns).index(ta_col) if ta_col in df.columns else 0)
            df = df.rename(columns={en_map: "English", ta_map: "Tamil"})
            st.session_state.sme_df = df[["English","Tamil"]].copy().reset_index(drop=True)
            st.session_state.sme_row_idx = 0
        except Exception as e:
            st.error(f"Error reading file: {e}\nIf Excel: add `openpyxl>=3.1` to requirements.txt")

df = st.session_state.sme_df

if df.empty:
    st.stop()

# ------------- Layout: main editor (3/4) + glossary (1/4) -------------
main, right = st.columns([3,1], gap="large")

with main:
    # Navigation row (Prev / index / Next)
    total = len(df)
    c1, c2, c3, c4 = st.columns([1,2,4,1])
    with c1:
        if st.button("◀️ Prev", use_container_width=True, disabled=st.session_state.sme_row_idx <= 0):
            st.session_state.sme_row_idx = max(0, st.session_state.sme_row_idx - 1)
            st.experimental_rerun()
    with c2:
        st.write(f"**Row:** {st.session_state.sme_row_idx + 1} / {total}")
    with c3:
        st.progress((st.session_state.sme_row_idx + 1) / total if total else 0.0)
    with c4:
        if st.button("Next ▶️", use_container_width=True, disabled=st.session_state.sme_row_idx >= total - 1):
            st.session_state.sme_row_idx = min(total - 1, st.session_state.sme_row_idx + 1)
            st.experimental_rerun()

    row = df.iloc[st.session_state.sme_row_idx]

    # Collapsible original (read-only) – hidden by default on iPad
    with st.expander("🔎 Show original (read-only) – English & Tamil", expanded=False):
        st.markdown(f"**English (orig):** {row['English']}")
        st.markdown(f"**Tamil (orig):** {row['Tamil']}")

    # Editor card
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("✏️ Edit Tamil")
    new_ta = st.text_area(
        "Tamil (SME editable)",
        value=str(row["Tamil"] or ""),
        height=180,
        key=f"edit_ta_{st.session_state.sme_row_idx}"
    )
    qc_toggle = st.checkbox("Show QC preview below (hide on small screens)")
    if qc_toggle:
        st.markdown("**QC Preview**")
        st.markdown(f"""
        <div class='kv'>
            <div>{colorize_en_ta(row['English'], new_ta)}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Save current edit into the session dataframe
    if st.button("💾 Save this row"):
        st.session_state.sme_df.at[st.session_state.sme_row_idx, "Tamil"] = new_ta
        st.success("Saved!")

    # Export current work
    csv_bytes = st.session_state.sme_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Download edited CSV", data=csv_bytes, file_name="edited_bilingual.csv", mime="text/csv")

with right:
    st.markdown("<div class='right-panel'>", unsafe_allow_html=True)
    st.subheader("📚 Glossary (EN → TA)")

    # Add new word (SME suggestion)
    with st.form("add_word"):
        en_new = st.text_input("English word")
        ta_new = st.text_input("Tamil word")
        submit = st.form_submit_button("➕ Add suggestion (yellow)")
        if submit and en_new.strip() and ta_new.strip():
            st.session_state.sme_suggestions.append({"en": en_new.strip(), "ta": ta_new.strip(), "source": "sme"})
            st.success("Suggestion added (pending central validation).")

    # Core glossary + suggestions (yellow)
    if st.session_state.glossary or st.session_state.sme_suggestions:
        # Merge to display (core first, then suggestions)
        core = [{"en": g["en"], "ta": g["ta"], "source": "core"} for g in st.session_state.glossary]
        sug  = [{"en": g["en"], "ta": g["ta"], "source": "sme"} for g in st.session_state.sme_suggestions]
        merged = sorted_glossary(core) + sorted_glossary(sug)

        for item in merged:
            html = colorize_en_ta(item["en"], item["ta"])
            cls = "card suggestion" if item["source"] == "sme" else "card"
            st.markdown(f"<div class='{cls}'>{html}</div>", unsafe_allow_html=True)
    else:
        st.info("No glossary terms yet. Add suggestions above.")

    st.markdown("</div>", unsafe_allow_html=True)
