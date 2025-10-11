# pages/03_Email_QC_Review.py
import os, io, re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SME Editor (QC Panel)", page_icon="📝", layout="wide")
st.title("📝 SME QC Panel (Row-wise, iPad friendly)")

# ---------------- Session & seed ----------------
if "qc_df" not in st.session_state: st.session_state.qc_df = pd.DataFrame()
if "qc_idx" not in st.session_state: st.session_state.qc_idx = 0
if "glossary" not in st.session_state: st.session_state.glossary = []  # [{en, ta, source}]
if "vocab_query" not in st.session_state: st.session_state.vocab_query = ""

# small helpers
def _sorted_glossary(items): return sorted(items, key=lambda x: x["en"].lower())
def _digits_only(s, n=None):
    v = re.sub(r"\D", "", str(s or ""))
    return v[:n] if n else v
def _pill(text, color, bg):
    return f"<span style='padding:.15rem .45rem;border-radius:999px;color:{color};background:{bg};font-size:.8rem'>{text}</span>"

# ---------------- File upload & column mapping ----------------
st.markdown("#### 📥 Load bilingual source (CSV/XLSX)")
up = st.file_uploader("Upload bilingual file", type=["csv","xlsx"])

# Canonical fields we want to operate with
CANON = [
    "ID",
    "Q_EN","OPT_EN","ANS_EN","EXP_EN",
    "Q_TA","OPT_TA","ANS_TA","EXP_TA"
]

def _try_read(uploaded):
    if uploaded is None: return None
    if uploaded.name.lower().endswith(".csv"):
        return pd.read_csv(uploaded)
    try:
        return pd.read_excel(uploaded, engine="openpyxl")
    except Exception:
        return pd.read_excel(uploaded)

if up is not None and st.session_state.qc_df.empty:
    try:
        raw = _try_read(up)
        st.success(f"Loaded **{up.name}** with **{len(raw)}** rows.")
        # auto-guess by substring
        def guess(name_like):
            for c in raw.columns:
                if name_like.lower() in c.lower(): return c
            return None

        # simple guesses
        guess_map = {
            "ID": guess("id") or raw.columns[0],
            "Q_EN": guess("question en") or guess("question_eng") or guess("question english") or guess("q_en"),
            "OPT_EN": guess("option en") or guess("options en") or guess("opt_en"),
            "ANS_EN": guess("answer en") or guess("ans en") or guess("ans_en"),
            "EXP_EN": guess("explan") or guess("exp en") or guess("exp_en"),
            "Q_TA": guess("question ta") or guess("question tamil") or guess("q_ta"),
            "OPT_TA": guess("option ta") or guess("options ta") or guess("opt_ta"),
            "ANS_TA": guess("answer ta") or guess("ans ta") or guess("ans_ta"),
            "EXP_TA": guess("exp ta") or guess("exp_ta"),
        }

        with st.expander("🔧 Map columns (adjust if needed)", expanded=True):
            cols = list(raw.columns)
            sel = {}
            c1, c2 = st.columns(2)
            with c1:
                sel["ID"]     = st.selectbox("ID", cols, index=cols.index(guess_map["ID"]) if guess_map["ID"] in cols else 0)
                sel["Q_EN"]   = st.selectbox("Question (EN)", cols, index=cols.index(guess_map["Q_EN"]) if guess_map["Q_EN"] in cols else 0)
                sel["OPT_EN"] = st.selectbox("Options (EN)", cols, index=cols.index(guess_map["OPT_EN"]) if guess_map["OPT_EN"] in cols else 0)
                sel["ANS_EN"] = st.selectbox("Answer (EN)", cols, index=cols.index(guess_map["ANS_EN"]) if guess_map["ANS_EN"] in cols else 0)
                sel["EXP_EN"] = st.selectbox("Explanation (EN)", cols, index=cols.index(guess_map["EXP_EN"]) if guess_map["EXP_EN"] in cols else 0)
            with c2:
                sel["Q_TA"]   = st.selectbox("Question (TA)", cols, index=cols.index(guess_map["Q_TA"]) if guess_map["Q_TA"] in cols else 0)
                sel["OPT_TA"] = st.selectbox("Options (TA)", cols, index=cols.index(guess_map["OPT_TA"]) if guess_map["OPT_TA"] in cols else 0)
                sel["ANS_TA"] = st.selectbox("Answer (TA)", cols, index=cols.index(guess_map["ANS_TA"]) if guess_map["ANS_TA"] in cols else 0)
                sel["EXP_TA"] = st.selectbox("Explanation (TA)", cols, index=cols.index(guess_map["EXP_TA"]) if guess_map["EXP_TA"] in cols else 0)

            if st.button("✅ Confirm mapping & start QC"):
                df = raw.rename(columns=sel)[CANON].copy()
                # hold edited Tamil fields (start with originals)
                for col in ["Q_TA","OPT_TA","ANS_TA","EXP_TA"]:
                    df[f"EDIT_{col}"] = df[col]
                st.session_state.qc_df = df.reset_index(drop=True)
                st.session_state.qc_idx = 0
    except Exception as e:
        st.error(f"Could not read file: {e}")

df = st.session_state.qc_df
if df.empty:
    st.stop()

# ---------------- Vocab (BLUE) ----------------
st.markdown("""
<style>
.box {border:1px solid #e6e6e6;border-radius:10px;padding:.8rem 1rem;margin-bottom:1rem;}
.box-blue {background:#eef6ff;}
.box-black {background:#111;color:#fff;}
.box-yellow {background:#fff8db;}
.box-red {background:#ffeaea;}
.box-green {background:#eaffea;}
.kv { line-height:1.4rem; }
.h { font-weight:600; margin:.2rem 0 .6rem 0; }
</style>
""", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="box box-blue">', unsafe_allow_html=True)
    st.subheader("📘 Vocabulary (EN ⇄ TA)")
    cva, cvb = st.columns([2,1])
    with cva:
        q = st.text_input("Find word (English):", value=st.session_state.vocab_query)
        st.session_state.vocab_query = q
        matches = [g for g in _sorted_glossary(st.session_state.glossary)
                   if q.strip() and g["en"].lower().startswith(q.strip().lower())]
        if q.strip():
            if matches:
                st.write("**Matches:**")
                for m in matches[:12]:
                    st.markdown(f"- **{m['en']}** → {m['ta']}")
            else:
                st.info("No matches.")
        else:
            if st.session_state.glossary:
                st.caption("Recently added:")
                for m in _sorted_glossary(st.session_state.glossary)[:6]:
                    st.markdown(f"- **{m['en']}** → {m['ta']}")
            else:
                st.caption("No glossary yet.")
    with cvb:
        st.write("**Add term**")
        with st.form("add_vocab"):
            ven = st.text_input("English")
            vta = st.text_input("Tamil")
            s = st.form_submit_button("➕ Add")
            if s and ven.strip() and vta.strip():
                st.session_state.glossary.append({"en": ven.strip(), "ta": vta.strip(), "source": "sme"})
                st.success("Added to glossary.")
                if not st.session_state.vocab_query:
                    st.session_state.vocab_query = ven.strip()
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Navigation ----------------
row = df.iloc[st.session_state.qc_idx]
top1, top2, top3, top4 = st.columns([1.2, 3, 3, 1.2])
with top1:
    if st.button("◀️ Prev", use_container_width=True, disabled=st.session_state.qc_idx <= 0):
        st.session_state.qc_idx = max(0, st.session_state.qc_idx - 1)
        st.rerun()
with top2:
    st.markdown(f"**ID:** {_pill(str(row['ID']), '#174ea6', '#e7f0fe')}", unsafe_allow_html=True)
with top3:
    st.progress((st.session_state.qc_idx + 1) / len(df))
with top4:
    if st.button("Next ▶️", use_container_width=True, disabled=st.session_state.qc_idx >= len(df)-1):
        st.session_state.qc_idx = min(len(df)-1, st.session_state.qc_idx + 1)
        st.rerun()

# Stepper
step = st.radio("Step", ["Question", "Options", "Answer", "Explanation"], horizontal=True, index=0)

# field pickers by step
STEP_EN = {"Question":"Q_EN", "Options":"OPT_EN", "Answer":"ANS_EN", "Explanation":"EXP_EN"}[step]
STEP_TA = {"Question":"Q_TA", "Options":"OPT_TA", "Answer":"ANS_TA", "Explanation":"EXP_TA"}[step]
STEP_EDIT = f"EDIT_{STEP_TA}"

# ---------------- Black: English (read-only) ----------------
st.markdown('<div class="box box-black">', unsafe_allow_html=True)
st.markdown("**English Version / ஆங்கில பதிப்பு**")
st.markdown(f"<div class='kv'>{row[STEP_EN]}</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Yellow: Tamil original (read-only) ----------------
st.markdown('<div class="box box-yellow">', unsafe_allow_html=True)
st.markdown("**Tamil Version / தமிழ் பதிப்பு**")
st.markdown(f"<div class='kv'>{row[STEP_TA]}</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Red: SME QC Verified (reflects latest edits) ----------------
st.markdown('<div class="box box-red">', unsafe_allow_html=True)
st.markdown("**SME QC Verified / ஆசிரியரால் தணிக்கை செய்யப்பட்டது**")
st.markdown(f"<div class='kv'>{row[STEP_EDIT]}</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Green: Editable ----------------
st.markdown('<div class="box box-green">', unsafe_allow_html=True)
st.markdown("**For SME QC Check / ஆசிரியர் தணிக்கை செய்திட**")

# main editor for the active step
new_text = st.text_area("Edit (Tamil)", value=str(row[STEP_EDIT] or ""), height=160, key=f"edit_{STEP_EDIT}_{st.session_state.qc_idx}")

# vocab feeder at bottom: paste English word to quickly search
vf = st.text_input("🔎 Vocab feeder (paste/copy English word)")
if vf.strip():
    st.session_state.vocab_query = vf.strip()

csa, csb, csc = st.columns([1.2, 1.2, 3])
with csa:
    if st.button("💾 Save this step", use_container_width=True):
        st.session_state.qc_df.at[st.session_state.qc_idx, STEP_EDIT] = new_text
        st.success("Saved.")
with csb:
    if st.button("💾 Save & Next ▶️", use_container_width=True):
        st.session_state.qc_df.at[st.session_state.qc_idx, STEP_EDIT] = new_text
        if st.session_state.qc_idx < len(df)-1:
            st.session_state.qc_idx += 1
        st.success("Saved.")
        st.rerun()
with csc:
    st.caption("Tip: turn on *Save & Next* rhythm; the red panel always shows the latest edit.")

st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Download edited CSV ----------------
st.divider()
out = st.session_state.qc_df[["ID","Q_EN","OPT_EN","ANS_EN","EXP_EN",
                              "Q_TA","OPT_TA","ANS_TA","EXP_TA",
                              "EDIT_Q_TA","EDIT_OPT_TA","EDIT_ANS_TA","EDIT_EXP_TA"]].copy()
out = out.rename(columns={
    "EDIT_Q_TA":"QC_Q_TA",
    "EDIT_OPT_TA":"QC_OPT_TA",
    "EDIT_ANS_TA":"QC_ANS_TA",
    "EDIT_EXP_TA":"QC_EXP_TA",
})
csv_bytes = out.to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ Download edited CSV", data=csv_bytes, file_name="qc_edited_bilingual.csv", mime="text/csv")
