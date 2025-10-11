# pages/03_Email_QC_Panel.py
# Single-page SME QC layout (iPad-first)
# - Slim top bar with nav + export
# - Compact English & Tamil Original reference blocks
# - Large SME Edit Console with separate fields (Q, A/B, C/D, Answer, Explanation)
# - Live yellow preview mirrors edits
# - Tiny file link/upload drawer (for emergency use)
# - Optional right-side glossary drawer

import io
import os
import re
import json
import pandas as pd
import streamlit as st

# ---------------------- Helpers (standalone + lib/ fallback) ----------------------
def _has_lib():
    try:
        import lib  # noqa: F401
        return True
    except Exception:
        return False

if _has_lib():
    from lib import apply_theme as _apply_theme_lib  # type: ignore
    from lib import read_bilingual as _read_bilingual_lib  # type: ignore
    from lib import export_qc as _export_qc_lib  # type: ignore
    from lib import auto_guess_map as _auto_guess_map_lib  # type: ignore
    from lib import sort_glossary as _sort_glossary_lib  # type: ignore
    from lib.glossary import render_matches as _render_matches_lib  # type: ignore
else:
    _apply_theme_lib = None
    _read_bilingual_lib = None
    _export_qc_lib = None
    _auto_guess_map_lib = None
    _sort_glossary_lib = None
    _render_matches_lib = None

# Light CSS to tighten everything
CSS = """
<style>
/* full width, no sidebar */
section[data-testid="stSidebar"] { display: none !important; }
main.block-container { padding-top: 0.4rem; padding-bottom: 0.6rem; max-width: 1400px; }

/* compact headings & boxes */
h1,h2,h3,h4 { margin: 0.2rem 0 0.4rem 0; }
.box { border: 2px solid var(--border); border-radius: 10px; padding: .6rem .8rem; margin: .5rem 0; }
.box.en { background: #e9f2ff; border-color: #9dc2ff; }
.box.ta { background: #eaf7ea; border-color: #92d18b; }
.box.edit { background: #fff7e6; border-color: #ffd28b; }
.box.preview { background: #fff6cc; border-color: #ffdf70; }
.idpill { display:inline-block; padding:.2rem .5rem; border-radius:999px; background:#111; color:#fff; font-weight:600; font-size:.8rem; }
.topbar { display:flex; gap:.5rem; align-items:center; }
.topbar .grow { flex: 1; }
.smallcaps { font-variant: all-small-caps; letter-spacing:.04em; opacity:.7; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; white-space: pre-wrap; }
.xbtn { border:1px solid var(--border); border-radius:8px; padding:.35rem .6rem; }
.xbtn:disabled { opacity:.5; }
.split2 { display:grid; grid-template-columns: 1fr 1fr; gap:.5rem; }
.split4 { display:grid; grid-template-columns: 1fr 1fr; gap:.5rem .8rem; }
label[data-testid="stWidgetLabel"] > div > p { margin-bottom: .15rem; }
.tip { font-size:.85rem; opacity:.65; }
hr { margin:.5rem 0; }
</style>
"""
st.set_page_config(page_title="SME QC Panel", page_icon="📝", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

# ---------------------- Session ----------------------
ss = st.session_state
if "night" not in ss: ss.night = False
if "df" not in ss: ss.df = pd.DataFrame()
if "idx" not in ss: ss.idx = 0
if "glossary" not in ss: ss.glossary = []
if "vocab_query" not in ss: ss.vocab_query = ""
if "file_note" not in ss: ss.file_note = ""  # to show which file is loaded
if "ed" not in ss: ss.ed = {}  # per-row edit cache

# ---------------------- Basic theme (fallback) ----------------------
def apply_theme(night: bool):
    if _apply_theme_lib:
        _apply_theme_lib(night, hide_sidebar=True)
    # (fallback: do nothing—Streamlit theme handles night mode if enabled globally)

# ---------------------- File loading ----------------------
EXPECTED = ["ID","Q_EN","OPT_EN","ANS_EN","EXP_EN","Q_TA","OPT_TA","ANS_TA","EXP_TA"]

def _auto_guess_map(df: pd.DataFrame) -> dict:
    if _auto_guess_map_lib:
        return _auto_guess_map_lib(df)
    # very small fallback: look for best matching names
    cols = {c.lower(): c for c in df.columns}
    def pick(*cands):
        for c in cands:
            if c.lower() in cols: return cols[c.lower()]
        # substring contains
        for k,v in cols.items():
            for p in cands:
                if p.lower() in k: return v
        return df.columns[0]  # last resort
    return {
        "ID": pick("id"),
        "Q_EN": pick("question (english)","q_en","eng q","eng_question"),
        "OPT_EN": pick("options (english)","opt_en","eng options"),
        "ANS_EN": pick("answer (english)","ans_en","eng answer"),
        "EXP_EN": pick("explanation (english)","exp_en","eng explanation"),
        "Q_TA": pick("question (tamil)","q_ta","ta q"),
        "OPT_TA": pick("options (tamil)","opt_ta","ta options"),
        "ANS_TA": pick("answer (tamil)","ans_ta","ta answer"),
        "EXP_TA": pick("explanation (tamil)","exp_ta","ta explanation"),
    }

def read_bilingual(file) -> pd.DataFrame:
    if _read_bilingual_lib:
        return _read_bilingual_lib(file)
    name = getattr(file, "name", "")
    if isinstance(file, (str, bytes)):  # URL or path
        if str(file).lower().endswith(".csv"):
            return pd.read_csv(file)
        return pd.read_excel(file)
    # UploadedFile
    data = file.read()
    bio = io.BytesIO(data)
    if name.lower().endswith(".csv"):
        return pd.read_csv(bio)
    return pd.read_excel(bio)

def _split_opts(text: str):
    s = str(text or "").strip()
    if not s:
        return ["","","",""]
    # common separators: | or \n or numbered bullets
    # Try to strip "A) ..." forms gently
    parts = re.split(r"\s*\|\s*|\n+", s)
    # clean labels A) 1) etc.
    cleaned = []
    for p in parts:
        cleaned.append(re.sub(r"^\s*([A-Da-d1-4][\)\.]\s*)", "", p).strip())
    # pad/trim to 4
    cleaned = (cleaned + ["","","",""])[:4]
    return cleaned

def _compose_opts(a,b,c,d):
    items = [x for x in [a,b,c,d]]
    labels = ["A) ","B) ","C) ","D) "]
    out = " | ".join(f"{labels[i]}{(items[i] or '').strip()}" for i in range(4))
    return out

# ---------------------- Load area (tiny drawer) ----------------------
with st.expander("📎 File link or upload (admin-prepared, mapped) — open only if needed", expanded=False):
    colL, colR = st.columns([2,1])
    with colL:
        url = st.text_input("Paste CSV/XLSX URL (public link)", value="")
    with colR:
        up = st.file_uploader("…or upload file", type=["csv","xlsx"], label_visibility="collapsed")
    if st.button("Load file"):
        try:
            src = read_bilingual(url or up)
            if src.empty:
                st.error("File appears empty.")
            else:
                # Normalize/rename expected columns
                amap = _auto_guess_map(src)
                df = pd.DataFrame()
                for k in EXPECTED:
                    src_col = amap.get(k, None)
                    if src_col is None or src_col not in src.columns:
                        st.warning(f"Missing column guess for {k}; using blanks.")
                        df[k] = ""
                    else:
                        df[k] = src[src_col]
                # ensure ID is str-like
                df["ID"] = df["ID"].astype(str)
                ss.df = df.reset_index(drop=True)
                ss.idx = 0
                ss.file_note = (getattr(up,"name", "") or url or "").split("/")[-1]
                ss.ed.clear()
                st.success(f"Loaded {len(ss.df)} rows.")
        except Exception as e:
            st.error(f"Load failed: {e}")

# If nothing loaded yet, show a tiny hint and stop
if ss.df.empty:
    st.caption("English ⇄ Tamil · single-page QC")
    st.info("No file loaded yet. Use the small 📎 drawer above **once**, then the screen will fill with content.")
    st.stop()

# ---------------------- Theme & top bar ----------------------
apply_theme(ss.night)

row = ss.df.iloc[ss.idx]
rid = str(row["ID"])

topL, topC, topR = st.columns([1.6, 3.2, 2.2])
with topL:
    st.markdown("### 📝 SME QC Panel")
    st.caption("English ⇄ Tamil · single-page QC")
with topC:
    st.progress((ss.idx+1) / len(ss.df))
    st.caption(f"ID: **{rid}** · Row {ss.idx+1} / {len(ss.df)}" + (f" · _{ss.file_note}_" if ss.file_note else ""))
with topR:
    nav1, nav2, nav3, nav4 = st.columns(4)
    with nav1:
        if st.button("◀️ Prev", use_container_width=True, disabled=ss.idx<=0):
            ss.idx = max(0, ss.idx-1); st.rerun()
    with nav2:
        if st.button("Next ▶️", use_container_width=True, disabled=ss.idx>=len(ss.df)-1):
            ss.idx = min(len(ss.df)-1, ss.idx+1); st.rerun()
    with nav3:
        pass
    with nav4:
        pass

# ---------------------- Reference blocks (compact) ----------------------
def _clean(s: str) -> str:
    return (s or "").replace("\r\n","\n").strip()

en_q   = _clean(row["Q_EN"])
en_op4 = _split_opts(row["OPT_EN"])
en_ans = _clean(row["ANS_EN"])
en_exp = _clean(row["EXP_EN"])

ta_q   = _clean(row["Q_TA"])
ta_op4 = _split_opts(row["OPT_TA"])
ta_ans = _clean(row["ANS_TA"])
ta_exp = _clean(row["EXP_TA"])

# English reference (compact)
st.markdown("<div class='box en'><h4>English Version / ஆங்கிலம்</h4>"
            f"<div class='mono'><b>Q:</b> {en_q}\n\n"
            f"<b>Options (A–D):</b> A) {en_op4[0]} | B) {en_op4[1]} | C) {en_op4[2]} | D) {en_op4[3]}\n\n"
            f"<b>Answer:</b> {en_ans}\n\n"
            f"<b>Explanation:</b> {en_exp}</div></div>", unsafe_allow_html=True)

# Tamil original reference (compact)
st.markdown("<div class='box ta'><h4>Tamil Original / தமிழ் மூலப் பதிப்பு</h4>"
            f"<div class='mono'><b>கேள்வி:</b> {ta_q}\n\n"
            f"<b>விருப்பங்கள் (A–D):</b> A) {ta_op4[0]} | B) {ta_op4[1]} | C) {ta_op4[2]} | D) {ta_op4[3]}\n\n"
            f"<b>பதில்:</b> {ta_ans}\n\n"
            f"<b>விளக்கம்:</b> {ta_exp}</div></div>", unsafe_allow_html=True)

# ---------------------- SME Edit Console (large) ----------------------
# Prepare per-row edit cache
cache_key = f"row_{ss.idx}"
if cache_key not in ss.ed:
    ss.ed[cache_key] = {
        "q": ta_q,
        "a": ta_op4[0],
        "b": ta_op4[1],
        "c": ta_op4[2],
        "d": ta_op4[3],
        "ans": ta_ans,
        "exp": ta_exp,
    }

E = ss.ed[cache_key]

st.markdown("<div class='box edit'><h4>SME Edit Console / ஆசிரியர் திருத்தம்</h4>", unsafe_allow_html=True)

# Q (full width)
E["q"] = st.text_area("கேள்வி / Question (TA)", value=E["q"], height=90, label_visibility="visible")

# Options split 2x2
opt_top = st.columns(2)
with opt_top[0]:
    E["a"] = st.text_input("விருப்பம் A", value=E["a"])
with opt_top[1]:
    E["b"] = st.text_input("விருப்பம் B", value=E["b"])

opt_bot = st.columns(2)
with opt_bot[0]:
    E["c"] = st.text_input("விருப்பம் C", value=E["c"])
with opt_bot[1]:
    E["d"] = st.text_input("விருப்பம் D", value=E["d"])

E["ans"] = st.text_input("பதில் / Answer (TA)", value=E["ans"])
E["exp"] = st.text_area("விளக்கம் / Explanation (TA)", value=E["exp"], height=140)

# Live preview (yellow)
preview = f"""**கேள்வி:** {E['q']}

**விருப்பங்கள் (A–D):** A) {E['a']} | B) {E['b']} | C) {E['c']} | D) {E['d']}

**பதில்:** {E['ans']}

**விளக்கம்:** {E['exp']}
"""
st.markdown("<div class='box preview'><h4>Live Preview / நேரடி முன் நோட்டம்</h4></div>", unsafe_allow_html=True)
st.markdown(preview)

# Save + Next row
colS = st.columns([1.2, 1.2, 6])
with colS[0]:
    if st.button("💾 Save this row", use_container_width=True):
        # write back into the working DF (create columns if missing)
        for k in ["QC_Q_TA","QC_OPT_A_TA","QC_OPT_B_TA","QC_OPT_C_TA","QC_OPT_D_TA","QC_ANS_TA","QC_EXP_TA"]:
            if k not in ss.df.columns:
                ss.df[k] = ""
        ss.df.at[ss.idx, "QC_Q_TA"]      = E["q"]
        ss.df.at[ss.idx, "QC_OPT_A_TA"]  = E["a"]
        ss.df.at[ss.idx, "QC_OPT_B_TA"]  = E["b"]
        ss.df.at[ss.idx, "QC_OPT_C_TA"]  = E["c"]
        ss.df.at[ss.idx, "QC_OPT_D_TA"]  = E["d"]
        ss.df.at[ss.idx, "QC_ANS_TA"]    = E["ans"]
        ss.df.at[ss.idx, "QC_EXP_TA"]    = E["exp"]
        st.success("Saved.")
with colS[1]:
    if st.button("💾 Save & Next ▶️", use_container_width=True, disabled=ss.idx>=len(ss.df)-1):
        for k in ["QC_Q_TA","QC_OPT_A_TA","QC_OPT_B_TA","QC_OPT_C_TA","QC_OPT_D_TA","QC_ANS_TA","QC_EXP_TA"]:
            if k not in ss.df.columns:
                ss.df[k] = ""
        ss.df.at[ss.idx, "QC_Q_TA"]      = E["q"]
        ss.df.at[ss.idx, "QC_OPT_A_TA"]  = E["a"]
        ss.df.at[ss.idx, "QC_OPT_B_TA"]  = E["b"]
        ss.df.at[ss.idx, "QC_OPT_C_TA"]  = E["c"]
        ss.df.at[ss.idx, "QC_OPT_D_TA"]  = E["d"]
        ss.df.at[ss.idx, "QC_ANS_TA"]    = E["ans"]
        ss.df.at[ss.idx, "QC_EXP_TA"]    = E["exp"]
        ss.idx = min(len(ss.df)-1, ss.idx+1)
        st.experimental_rerun()

# ---------------------- Exports (always available at top bar via download buttons) ----------------------
# Build a compact export table with the edited Tamil alongside originals & English
export_df = ss.df[[
    "ID","Q_EN","OPT_EN","ANS_EN","EXP_EN","Q_TA","OPT_TA","ANS_TA","EXP_TA"
]].copy()

# ensure QC columns present
for k in ["QC_Q_TA","QC_OPT_A_TA","QC_OPT_B_TA","QC_OPT_C_TA","QC_OPT_D_TA","QC_ANS_TA","QC_EXP_TA"]:
    if k not in ss.df.columns:
        ss.df[k] = ""

export_df["QC_Q_TA"]     = ss.df["QC_Q_TA"]
export_df["QC_OPT_A_TA"] = ss.df["QC_OPT_A_TA"]
export_df["QC_OPT_B_TA"] = ss.df["QC_OPT_B_TA"]
export_df["QC_OPT_C_TA"] = ss.df["QC_OPT_C_TA"]
export_df["QC_OPT_D_TA"] = ss.df["QC_OPT_D_TA"]
export_df["QC_ANS_TA"]   = ss.df["QC_ANS_TA"]
export_df["QC_EXP_TA"]   = ss.df["QC_EXP_TA"]

# put two small download buttons under the edit console (they’re lightweight)
xlsx_io = io.BytesIO()
with pd.ExcelWriter(xlsx_io, engine="xlsxwriter") as writer:
    export_df.to_excel(writer, index=False, sheet_name="QC")
xlsx_bytes = xlsx_io.getvalue()
csv_bytes = export_df.to_csv(index=False).encode("utf-8")

dl1, dl2, _ = st.columns([1.4,1.4,3])
with dl1:
    st.download_button("⬇️ Export Excel", data=xlsx_bytes,
        file_name="sme_qc_edits.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True)
with dl2:
    st.download_button("⬇️ Export CSV", data=csv_bytes,
        file_name="sme_qc_edits.csv", mime="text/csv",
        use_container_width=True)

# ---------------------- Optional: right-side Glossary mini drawer ----------------------
with st.expander("📚 Glossary / சொற்க்களஞ்சியம் (optional)", expanded=False):
    q = st.text_input("🔎 Search / Add (English starts-with)", value=ss.vocab_query)
    ss.vocab_query = q
    if _render_matches_lib:
        html = _render_matches_lib(ss.glossary, q)
        st.markdown(html, unsafe_allow_html=True)
    else:
        # tiny fallback rendering
        rows = [g for g in ss.glossary if g.get("en","").lower().startswith(q.lower())]
        if not rows:
            st.caption("No matches.")
        else:
            for g in rows:
                st.write(f"• **{g.get('en','')}** → {g.get('ta','')}")
    c1, c2 = st.columns(2)
    with c1:
        en_new = st.text_input("English term", key="g_en")
    with c2:
        ta_new = st.text_input("Tamil term", key="g_ta")
    if st.button("➕ Add to glossary"):
        if en_new.strip() and ta_new.strip():
            ss.glossary.append({"en": en_new.strip(), "ta": ta_new.strip()})
            ss.vocab_query = en_new.strip()
            st.success("Added.")
        else:
            st.warning("Enter both English and Tamil.")
