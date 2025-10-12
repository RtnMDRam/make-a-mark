# pages/03_Email_QC_Panel.py
# SME QC Panel – compact iPad layout + safe glossary + admin loader

import io
import pandas as pd
import streamlit as st

# ---- optional imports (guarded) ----
try:
    from lib.header_bar import render_header
except Exception:
    def render_header(*_, **__):
        st.markdown(
            "<div style='height:5vh;display:flex;align-items:center;justify-content:center;"
            "background:#0e1117;color:#fff;border-radius:8px;margin:2px 0;'>"
            "<b>SME QC Panel</b></div>", unsafe_allow_html=True
        )

try:
    from lib.ux_mobile import enable_ipad_keyboard_aid, glossary_drawer  # may not exist or may need args
except Exception:
    def enable_ipad_keyboard_aid(*_, **__):  # no-op fallback
        return
    glossary_drawer = None  # signal unavailable

try:
    from lib.admin_uploader import render_admin_loader
except Exception:
    # Minimal inline uploader if module not present
    def render_admin_loader():
        ss = st.session_state
        with st.container():
            st.markdown(
                "<div style='border:1px solid #d9d9d9;border-radius:10px;padding:8px 10px;"
                "background:#f7f9fc; margin:4px 0;'>"
                "<b>Paste the CSV/XLSX link sent by Admin, or upload the file.</b>"
                "</div>", unsafe_allow_html=True
            )
            c1, c2, c3 = st.columns([4, 3, 1])
            with c1:
                upl = st.file_uploader(" ", type=["csv", "xlsx"], label_visibility="collapsed")
            with c2:
                link = st.text_input(" ", value=st.session_state.get("link_in", ""),
                                     placeholder="https://… .csv or .xlsx", label_visibility="collapsed")
                st.session_state["link_in"] = link
            with c3:
                if st.button("Load", use_container_width=True):
                    try:
                        if upl is not None:
                            if str(upl.name).lower().endswith(".csv"):
                                df = pd.read_csv(upl)
                            else:
                                df = pd.read_excel(upl)
                        else:
                            if not link.strip():
                                raise RuntimeError("Upload a file or paste a link, then press Load.")
                            try:
                                df = pd.read_csv(link)
                            except Exception:
                                df = pd.read_excel(link)
                        # normalize minimal columns; keep originals if already matching
                        def pick(d, *names):
                            cols = {c.lower(): c for c in d.columns}
                            for n in names:
                                if n and n.lower() in cols:
                                    return cols[n.lower()]
                            return None
                        cm = {
                            "ID": pick(df, "ID", "id"),
                            "Question (English)": pick(df, "Question (English)", "Q_EN", "question_english"),
                            "Options (English)": pick(df, "Options (English)", "OPT_EN", "options_english"),
                            "Answer (English)": pick(df, "Answer (English)", "ANS_EN", "answer_english"),
                            "Explanation (English)": pick(df, "Explanation (English)", "EXP_EN", "explanation_english"),
                            "Question (Tamil)": pick(df, "Question (Tamil)", "Q_TA", "question_tamil"),
                            "Options (Tamil)": pick(df, "Options (Tamil)", "OPT_TA", "options_tamil"),
                            "Answer (Tamil)": pick(df, "Answer (Tamil)", "ANS_TA", "answer_tamil"),
                            "Explanation (Tamil)": pick(df, "Explanation (Tamil)", "EXP_TA", "explanation_tamil"),
                            "QC_TA": pick(df, "QC_TA", "QC Verified (Tamil)", "qc_tamil"),
                        }
                        # build normalized frame
                        out = pd.DataFrame()
                        for k, src in cm.items():
                            out[k] = df[src] if src is not None else ""
                        # support deep-link subset ?ids= or ?rows=1-25
                        qp = st.query_params
                        ids = qp.get("ids", [])
                        rows = qp.get("rows", [])
                        if ids:
                            id_list = [x for x in ids[0].replace(",", " ").split() if x]
                            out = out[out["ID"].astype(str).isin(id_list)].reset_index(drop=True)
                        elif rows:
                            import re
                            m = re.match(r"\s*(\d+)\s*-\s*(\d+)\s*$", rows[0])
                            if m:
                                a, b = int(m.group(1)), int(m.group(2))
                                a, b = min(a, b), max(a, b)
                                out = out.iloc[a-1:b].reset_index(drop=True)

                        st.session_state.qc_src = out.copy()
                        st.session_state.qc_work = out.copy()
                        st.session_state.qc_idx = 0
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))


# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="SME QC Panel", page_icon="🧩",
                   layout="wide", initial_sidebar_state="collapsed")

# ---------- HEADER (5% vh) ----------
render_header(top_height_vh=5)

# ---------- iPad keyboard aid ----------
enable_ipad_keyboard_aid()

# ---------- ADMIN STRIP (10% area target via tight CSS) ----------
render_admin_loader()

# If no data yet, stop (SMEs see just the admin strip)
ss = st.session_state
if "qc_work" not in ss or ss.qc_work is None or getattr(ss.qc_work, "empty", True):
    st.stop()

# ---------- CSS: ultra-compact ----------
st.markdown("""
<style>
[data-testid="stSidebar"]{display:none;}
header, footer, .stAppToolbar {visibility:hidden;height:0;}
main .block-container{padding:6px 10px 6px !important;}
.element-container{margin-bottom:6px !important;}
h4, h5, h6 {margin:0 0 6px;}
.card{border:1px solid #d9e1ff;background:#eef4ff;border-radius:12px;padding:10px;margin:6px 0;}
.card.ta{border:1px solid #cfe8cf;background:#f1fbf1;}
.sme{border:1px solid #e3e3e3;background:#fff;border-radius:12px;padding:10px;margin:8px 0;}
.grid2>div{margin-bottom:6px;}
.opt4 .stTextInput>div>div, .opt4 .stTextInput input{font-size:16px;}
label {font-size:0.88rem;}
.btnrow{display:flex;justify-content:center;gap:14px;margin-top:6px;}
</style>
""", unsafe_allow_html=True)

# ---------- CURRENT ROW ----------
idx = ss.qc_idx if "qc_idx" in ss else 0
idx = max(0, min(idx, len(ss.qc_work)-1))
row = ss.qc_work.iloc[idx]

st.caption(f"English ⇄ Tamil • Row {idx+1}/{len(ss.qc_work)} • ID: {row.get('ID', '')}")

# ---------- ENGLISH REFERENCE ----------
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**English Version / ஆங்கிலம்**")
    st.write(f"**Q:** {row['Question (English)']}")
    st.write(f"**Options (A–D):** {row['Options (English)']}")
    st.write(f"**Answer:** {row['Answer (English)']}")
    st.write(f"**Explanation:** {row['Explanation (English)']}")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- TAMIL REFERENCE ----------
with st.container():
    st.markdown('<div class="card ta">', unsafe_allow_html=True)
    st.markdown("**Tamil Original / தமிழ் மூலப் பதிப்பு**")
    st.write(f"**Q:** {row['Question (Tamil)']}")
    st.write(f"**Options (A–D):** {row['Options (Tamil)']}")
    st.write(f"**Answer:** {row['Answer (Tamil)']}")
    st.write(f"**Explanation:** {row['Explanation (Tamil)']}")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- SME EDIT CONSOLE ----------
st.markdown('<div class="sme">', unsafe_allow_html=True)
st.markdown("### SME Edit Console / ஆசிரியர் திருத்தம்")

# Q (≈ 2 lines), then options as tight grid, then answer, then explanation
q_val = st.text_area(" ", value=row["Question (Tamil)"], height=70, label_visibility="collapsed",
                     placeholder="கேள்வி / Question (TA)")

# options grid
st.markdown("<div class='grid2 opt4'>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    a_val = st.text_input(" ", value=row["Options (Tamil)"], key="opA", label_visibility="collapsed",
                          placeholder="A)")
with c2:
    b_val = st.text_input(" ", value="", key="opB", label_visibility="collapsed",
                          placeholder="B)")
c3, c4 = st.columns(2)
with c3:
    c_val = st.text_input(" ", value="", key="opC", label_visibility="collapsed",
                          placeholder="C)")
with c4:
    d_val = st.text_input(" ", value="", key="opD", label_visibility="collapsed",
                          placeholder="D)")
st.markdown("</div>", unsafe_allow_html=True)

ans_val = st.text_input("பதில் / Answer", value=row["Answer (Tamil)"])

exp_val = st.text_area("விளக்கம் / Explanation", value=row["Explanation (Tamil)"], height=120)

# ---------- ACTION BUTTONS (center, minimal slack) ----------
st.markdown('<div class="btnrow">', unsafe_allow_html=True)
b1, b2, b3 = st.columns(3)
with b1:
    if st.button("💾 Save", use_container_width=True):
        ss.qc_work.at[idx, "Question (Tamil)"] = q_val
        # Join A–D back if you split them in future; for now keep original Options (Tamil)
        ss.qc_work.at[idx, "Answer (Tamil)"] = ans_val
        ss.qc_work.at[idx, "Explanation (Tamil)"] = exp_val
        st.toast("Saved")
with b2:
    if st.button("✅ Mark Complete", use_container_width=True):
        ss.qc_work.at[idx, "QC_TA"] = "✅"
        st.toast("Marked complete")
with b3:
    if st.button("➡ Save & Next", use_container_width=True):
        ss.qc_work.at[idx, "Question (Tamil)"] = q_val
        ss.qc_work.at[idx, "Answer (Tamil)"] = ans_val
        ss.qc_work.at[idx, "Explanation (Tamil)"] = exp_val
        ss.qc_work.at[idx, "QC_TA"] = "✅"
        if idx < len(ss.qc_work) - 1:
            ss.qc_idx = idx + 1
        st.rerun()
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)  # end .sme

# ---------- GLOSSARY DRAWER (SAFE) ----------
# Only call if it exists; support both no-arg and keyword-arg versions.
try:
    if callable(glossary_drawer):
        try:
            glossary_drawer()  # most recent signature
        except TypeError:
            # fallback if your function expects keywords
            glossary_drawer(anchor="right", auto_open=False)
except Exception:
    # swallow any unexpected library mismatch so SMEs can keep working
    pass
