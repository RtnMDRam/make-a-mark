# pages/03_QC_Review.py
# SME QC panel: Glossary + English (RO) + Tamil Original (RO) + QC Verified (auto) + SME Edit
# - Preserves input headers & column order on export
# - iPad-friendly layout, Night Mode, stepper, prev/next, save & export

import io
import os
import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SME QC Panel", page_icon="📝", layout="wide")
st.title("📝 SME QC Panel")

# ---------------- Session state ----------------
ss = st.session_state
if "qc_src" not in ss:           ss.qc_src = pd.DataFrame()  # original as loaded (preserve headers/order)
if "qc_map" not in ss:           ss.qc_map = {}              # mapping: internal_key -> actual column name
if "qc_work" not in ss:          ss.qc_work = pd.DataFrame() # working copy with QC_* columns
if "qc_idx" not in ss:           ss.qc_idx = 0
if "qc_step" not in ss:          ss.qc_step = "Question"     # Question | Options | Answer | Explanation
if "glossary" not in ss:         ss.glossary = []            # [{en, ta}]
if "vocab_query" not in ss:      ss.vocab_query = ""
if "uploaded_name" not in ss:    ss.uploaded_name = None
if "night" not in ss:            ss.night = False

# ---------------- Helpers ----------------
def _digits_only(s, n=None):
    v = re.sub(r"\D", "", str(s or ""))
    return v[:n] if n else v

def _sorted_glossary(items):
    return sorted(items, key=lambda x: (x["en"] or "").lower())

def _auto_guess_map(df: pd.DataFrame):
    """Best-effort map based on common header patterns; returns dict of actual column names."""
    def guess(one_of):
        for cand in one_of:
            for c in df.columns:
                if cand.lower() in str(c).lower():
                    return c
        return None
    return {
        "ID":      guess(["id", "qid", "serial"]),
        "Q_EN":    guess(["question (english)", "question_en", "question english", "q_en"]),
        "OPT_EN":  guess(["options (english)", "option (english)", "options_en", "opt_en"]),
        "ANS_EN":  guess(["answer (english)", "ans_en", "answer en"]),
        "EXP_EN":  guess(["explanation (english)", "exp_en", "explanation en"]),
        "Q_TA":    guess(["question (tamil)", "question_tamil", "q_ta"]),
        "OPT_TA":  guess(["options (tamil)", "option (tamil)", "options_ta", "opt_ta"]),
        "ANS_TA":  guess(["answer (tamil)", "ans_ta", "answer ta"]),
        "EXP_TA":  guess(["explanation (tamil)", "exp_ta", "explanation ta"]),
    }

def _ensure_work(df_src: pd.DataFrame, m: dict) -> pd.DataFrame:
    """Create a working df with QC columns mirroring TA originals; does NOT change header names in source."""
    work = pd.DataFrame(index=df_src.index)
    # Bring through the mapped columns for convenience (read-only views)
    for k in ["ID", "Q_EN", "OPT_EN", "ANS_EN", "EXP_EN", "Q_TA", "OPT_TA", "ANS_TA", "EXP_TA"]:
        col = m.get(k)
        if col not in df_src.columns:
            work[k] = ""
        else:
            work[k] = df_src[col].astype(str).fillna("")
    # QC columns start as the TA originals (editable layer)
    work["QC_Q_TA"]   = work["Q_TA"]
    work["QC_OPT_TA"] = work["OPT_TA"]
    work["QC_ANS_TA"] = work["ANS_TA"]
    work["QC_EXP_TA"] = work["EXP_TA"]
    return work.reset_index(drop=True)

def _panel(title, color_class, body_html):
    st.markdown(f"<div class='box {color_class}'><h4>{title}</h4><div class='fine'>{body_html}</div></div>", unsafe_allow_html=True)

def _progress():
    if ss.qc_work.empty: 
        return
    st.progress((ss.qc_idx + 1) / len(ss.qc_work))
    st.caption(f"Row {ss.qc_idx + 1} / {len(ss.qc_work)}")

def _export_qc():
    """Return bytes of xlsx and csv: source headers preserved; TA cols replaced with QC values."""
    if ss.qc_src.empty or not ss.qc_map:
        return None, None

    export_df = ss.qc_src.copy()

    # Replace TA columns with QC values (preserving the original column names)
    repl = [
        ("Q_TA",   "QC_Q_TA"),
        ("OPT_TA", "QC_OPT_TA"),
        ("ANS_TA", "QC_ANS_TA"),
        ("EXP_TA", "QC_EXP_TA"),
    ]
    for base_key, qc_key in repl:
        src_col = ss.qc_map.get(base_key)  # actual name in source
        if src_col and qc_key in ss.qc_work.columns:
            export_df[src_col] = ss.qc_work[qc_key]

    # XLSX
    xbuf = io.BytesIO()
    with pd.ExcelWriter(xbuf, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False)
    # CSV
    cbytes = export_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    return xbuf.getvalue(), cbytes

# ---------------- Styles (Light + Night) ----------------
# Ergonomic palette
CSS_LIGHT = """
<style>
:root{
  --bg: #ffffff;
  --text:#202020;
  --border:#dcdcdc;

  --gloss-bg:#EFEFEF;     --gloss-b:#000000;   --gloss-t:#222222;

  --en-bg:#E6F0FF;        --en-b:#1F77B4;      --en-t:#1B1B1B;

  --tao-bg:#E8F5E9;       --tao-b:#2CA02C;     --tao-t:#212121;

  --qc-bg:#FFF3F0;        --qc-b:#E57373;      --qc-t:#2A1A1A;

  --edit-bg:#FFF8E1;      --edit-b:#FFBF00;    --edit-t:#202020;

  --textarea-bg:#FAF9F6;  --chip-on:#1F77B4;   --chip-off:#dddddd;
}
</style>
"""

CSS_NIGHT = """
<style>
:root{
  --bg:#111417;
  --text:#f1f1f1;
  --border:#3a3f45;

  --gloss-bg:#2a2e33;     --gloss-b:#000000;   --gloss-t:#e6e6e6;

  --en-bg:#213247;        --en-b:#4da3ff;      --en-t:#f1f6ff;

  --tao-bg:#1d3222;       --tao-b:#6fd18a;     --tao-t:#e9f7ed;

  --qc-bg:#412b2b;        --qc-b:#ff8f8f;      --qc-t:#ffecec;

  --edit-bg:#3a331d;      --edit-b:#ffd166;    --edit-t:#fff7d6;

  --textarea-bg:#2b2b2b;  --chip-on:#7fb7ff;   --chip-off:#555;
}
</style>
"""

BASE_CSS = """
<style>
html, body, .block-container { background: var(--bg); color: var(--text); }
.box { border:2px solid var(--border); border-radius:12px; padding:1rem 1.1rem; margin:.8rem 0; }
.box h4 { margin:0 0 .5rem 0; font-size:1.0rem; }
.box .fine { font-size: .95rem; line-height: 1.5rem; }

.box.gloss { background: var(--gloss-bg); border-color: var(--gloss-b); color: var(--gloss-t); }
.box.en    { background: var(--en-bg);    border-color: var(--en-b);    color: var(--en-t); }
.box.tao   { background: var(--tao-bg);   border-color: var(--tao-b);   color: var(--tao-t); }
.box.qc    { background: var(--qc-bg);    border-color: var(--qc-b);    color: var(--qc-t); }
.box.edit  { background: var(--edit-bg);  border-color: var(--edit-b);  color: var(--edit-t); }

textarea, .stTextArea textarea { background: var(--textarea-bg) !important; }
.stepchip {display:inline-block;border:1px solid var(--chip-off);border-radius:999px;padding:.2rem .7rem;margin-right:.35rem;font-size:.85rem}
.stepchip.on {background:var(--chip-on); color:#fff; border-color:var(--chip-on)}
.idtag{display:inline-block;border:1px solid var(--border);border-radius:8px;padding:.2rem .6rem;font-size:.9rem;margin-left:.5rem}
.mono {font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;}
</style>
"""

st.markdown(CSS_NIGHT if ss.night else CSS_LIGHT, unsafe_allow_html=True)
st.markdown(BASE_CSS, unsafe_allow_html=True)

# Night mode toggle
hdr_left, hdr_mid, hdr_right = st.columns([2,4,2])
with hdr_left:
    st.caption("iPad-friendly layout · preserves headers")
with hdr_right:
    ss.night = st.toggle("🌙 Night Mode", value=ss.night)

# ---------------- Load bilingual file + mapping ----------------
with st.expander("📥 Load bilingual file (.csv/.xlsx) & map columns", expanded=ss.qc_src.empty):
    up = st.file_uploader("Upload bilingual file", type=["csv","xlsx"])
    if up:
        # Read with header row as first row
        if up.name.lower().endswith(".csv"):
            src = pd.read_csv(up)
        else:
            try:
                src = pd.read_excel(up, engine="openpyxl")
            except Exception:
                src = pd.read_excel(up)
        if src.empty:
            st.error("File appears empty.")
        else:
            ss.uploaded_name = os.path.splitext(os.path.basename(up.name))[0]
            ss.qc_src = src
            auto = _auto_guess_map(src)

            st.write("**Map the required columns (preserved on export):**")
            cols = list(src.columns)
            sel = {}
            c1, c2 = st.columns(2)
            with c1:
                sel["ID"]     = st.selectbox("ID", cols, index=cols.index(auto["ID"]) if auto["ID"] in cols else 0)
                sel["Q_EN"]   = st.selectbox("Question (English)", cols, index=cols.index(auto["Q_EN"]) if auto["Q_EN"] in cols else 0)
                sel["OPT_EN"] = st.selectbox("Options (English)", cols, index=cols.index(auto["OPT_EN"]) if auto["OPT_EN"] in cols else 0)
                sel["ANS_EN"] = st.selectbox("Answer (English)", cols, index=cols.index(auto["ANS_EN"]) if auto["ANS_EN"] in cols else 0)
                sel["EXP_EN"] = st.selectbox("Explanation (English)", cols, index=cols.index(auto["EXP_EN"]) if auto["EXP_EN"] in cols else 0)
            with c2:
                sel["Q_TA"]   = st.selectbox("Question (Tamil)", cols, index=cols.index(auto["Q_TA"]) if auto["Q_TA"] in cols else 0)
                sel["OPT_TA"] = st.selectbox("Options (Tamil)", cols, index=cols.index(auto["OPT_TA"]) if auto["OPT_TA"] in cols else 0)
                sel["ANS_TA"] = st.selectbox("Answer (Tamil)", cols, index=cols.index(auto["ANS_TA"]) if auto["ANS_TA"] in cols else 0)
                sel["EXP_TA"] = st.selectbox("Explanation (Tamil)", cols, index=cols.index(auto["EXP_TA"]) if auto["EXP_TA"] in cols else 0)

            if st.button("✅ Confirm mapping & start QC"):
                ss.qc_map = sel
                ss.qc_work = _ensure_work(ss.qc_src, ss.qc_map)
                ss.qc_idx = 0
                st.success(f"Loaded {len(ss.qc_work)} rows. Headers will be preserved in exports.")
                st.rerun()

# Stop until we have data
if ss.qc_work.empty:
    st.stop()

# ---------------- Navigation row ----------------
row = ss.qc_work.iloc[ss.qc_idx]
nav1, nav2, nav3, nav4 = st.columns([1.2, 3, 3, 1.2])
with nav1:
    if st.button("◀️ Prev", use_container_width=True, disabled=ss.qc_idx <= 0):
        ss.qc_idx = max(0, ss.qc_idx - 1)
        st.rerun()
with nav2:
    rid = row["ID"]
    st.subheader(f"ID: {rid}")
with nav3:
    _progress()
with nav4:
    if st.button("Next ▶️", use_container_width=True, disabled=ss.qc_idx >= len(ss.qc_work)-1):
        ss.qc_idx = min(len(ss.qc_work)-1, ss.qc_idx + 1)
        st.rerun()

# Stepper
step_labels = ["Question", "Options", "Answer", "Explanation"]
ss.qc_step = st.radio("Step", step_labels, index=step_labels.index(ss.qc_step) if ss.qc_step in step_labels else 0, horizontal=True)

# Choose step columns
COL_EN  = {"Question":"Q_EN","Options":"OPT_EN","Answer":"ANS_EN","Explanation":"EXP_EN"}[ss.qc_step]
COL_TA  = {"Question":"Q_TA","Options":"OPT_TA","Answer":"ANS_TA","Explanation":"EXP_TA"}[ss.qc_step]
COL_QC  = {"Question":"QC_Q_TA","Options":"QC_OPT_TA","Answer":"QC_ANS_TA","Explanation":"QC_EXP_TA"}[ss.qc_step]

# ---------------- Glossary (Black border) ----------------
gloss_html = ""
if ss.vocab_query.strip():
    hits = [g for g in _sorted_glossary(ss.glossary) if g["en"].lower().startswith(ss.vocab_query.lower())]
    if hits:
        gloss_html += "<b>Matches</b><br>" + "<br>".join([f"• <b>{h['en']}</b> → {h['ta']}" for h in hits])
    else:
        gloss_html += "No matches."
else:
    if ss.glossary:
        gloss_html += "<b>Recently added</b><br>" + "<br>".join([f"• <b>{g['en']}</b> → {g['ta']}" for g in _sorted_glossary(ss.glossary)[:8]])
    else:
        gloss_html += "No glossary yet. Add below."

_panel("Vocabulary / சொற்களஞ்சியம்", "gloss", gloss_html)

with st.expander("Add to glossary"):
    ven = st.text_input("English")
    vta = st.text_input("Tamil")
    if st.button("➕ Add term"):
        if ven.strip() and vta.strip():
            ss.glossary.append({"en": ven.strip(), "ta": vta.strip()})
            ss.vocab_query = ven.strip()
            st.success("Added.")
        else:
            st.warning("Enter both English and Tamil.")

# ---------------- Panels (Blue / Green / Red / Yellow) ----------------
# BLUE: English non-editable
_panel("English Version / ஆங்கில பதிப்பு", "en",
       f"<div class='mono'>{(row[COL_EN] or '').strip().replace(chr(10), '<br>')}</div>")

# GREEN: Tamil original non-editable (from source)
_panel("Tamil Version / தமிழ் பதிப்பு", "tao",
       f"<div class='mono'>{(row[COL_TA] or '').strip().replace(chr(10), '<br>')}</div>")

# RED: SME QC Verified (auto-updated from saved edits)
_panel("SME QC Verified / ஆசிரியரால் தணிக்கை செய்யப்பட்டது", "qc",
       f"<div class='mono'>{(row[COL_QC] or '').strip().replace(chr(10), '<br>')}</div>")

# YELLOW: SME Editable panel
st.markdown("<div class='box edit'><h4>For SME QC Check / ஆசிரியர் தணிக்கை செய்திட</h4>", unsafe_allow_html=True)

# Main editor for the active step
edited_text = st.text_area("Edit (Tamil)", value=str(row[COL_QC] or ""), height=170, key=f"edit_{ss.qc_idx}_{COL_QC}")

# Vocabulary feeder inside the edit panel
vf = st.text_input("🔎 Vocabulary feeder (paste/type English word)")
if vf.strip():
    ss.vocab_query = vf.strip()

ed1, ed2, ed3 = st.columns([1.2, 1.3, 2.5])
with ed1:
    if st.button("💾 Save this step", use_container_width=True):
        ss.qc_work.at[ss.qc_idx, COL_QC] = edited_text
        st.success("Saved. Red panel updated.")
with ed2:
    if st.button("💾 Save & Next ▶️", use_container_width=True):
        ss.qc_work.at[ss.qc_idx, COL_QC] = edited_text
        if ss.qc_idx < len(ss.qc_work)-1:
            ss.qc_idx += 1
        st.success("Saved. Moving to next row…")
        st.rerun()
with ed3:
    st.caption("Tip: Use ‘Save & Next’ to speed through rows. QC-Verified (red) shows your latest saved text.")

st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Export ----------------
st.divider()
st.subheader("⬇️ Export")

# On-demand export (always available)
xlsx_bytes, csv_bytes = _export_qc()
if xlsx_bytes and csv_bytes:
    base = ss.uploaded_name or "qc_file"
    st.download_button("Download QC Excel (.xlsx)", data=xlsx_bytes,
                       file_name=f"{base}_qc_verified.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.download_button("Download QC CSV (.csv)", data=csv_bytes,
                       file_name=f"{base}_qc_verified.csv", mime="text/csv")

# Finalize button (for SMEs to confirm completion)
if st.button("✅ Work complete — Save QC file"):
    xlsx_bytes, csv_bytes = _export_qc()
    if not xlsx_bytes:
        st.error("Nothing to export yet.")
    else:
        st.success("QC file prepared. Use the buttons above to download.")
