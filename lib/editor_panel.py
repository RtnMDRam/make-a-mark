# lib/editor_panel.py
import re
import streamlit as st

def _split_opts(v:str):
    if not v or not str(v).strip(): return ["","","",""]
    parts = re.split(r"\s*\|\s*|[\n\r]+|[;•]\s*", str(v).strip())
    parts = [p for p in parts if p is not None]
    while len(parts) < 4: parts.append("")
    return parts[:4]

def render_references_and_editor():
    ss = st.session_state
    i  = ss.qc_idx
    row = ss.qc_work.iloc[i]
    rid = str(row["ID"])

    # --- Reference boxes (read-only) ---
    def view_block(title, q, op, ans, exp, cls):
        st.markdown(f"""
        <div class="box {cls}">
            <span style="font-weight:700;background:#00000022;padding:4px 10px;border-radius:12px;">{title}</span><br>
            <b>Q:</b> {q}<br>
            <b>Options (A–D):</b> {op}<br>
            <b>Answer:</b> {ans}<br>
            <b>Explanation:</b> {exp}
        </div>
        """, unsafe_allow_html=True)

    view_block("English Version / ஆங்கிலம்",
               row["Question (English)"], row["Options (English)"],
               row["Answer (English)"], row["Explanation (English)"], "en")
    view_block("Tamil Original / தமிழ் மூலப் பதிப்பு",
               row["Question (Tamil)"], row["Options (Tamil)"],
               row["Answer (Tamil)"], row["Explanation (Tamil)"], "ta")

    # --- SME Edit Console: small subtitle ---
    st.markdown('<div class="sme-sub">SME Edit Console / ஆசிரியர் திருத்தம்</div>', unsafe_allow_html=True)

    # Values into Session for this rid (so Save buttons in top strip can read them)
    A,B,C,D = _split_opts(row["Options (Tamil)"])
    defaults = {
        f"q_ta_{rid}"  : row["Question (Tamil)"],
        f"a_ta_{rid}"  : A,
        f"b_ta_{rid}"  : B,
        f"c_ta_{rid}"  : C,
        f"d_ta_{rid}"  : D,
        f"ans_ta_{rid}": row["Answer (Tamil)"],
        f"exp_ta_{rid}": row["Explanation (Tamil)"],
    }
    for k,v in defaults.items():
        if k not in ss: ss[k]=v

    # Question (keep ≈2 lines)
    st.text_area(" ", key=f"q_ta_{rid}", value=ss[f"q_ta_{rid}"], height=64, label_visibility="collapsed")

    # Options grid 2x2 (A,B on first row; C,D on second) — very compact
    st.markdown('<div class="optrow">', unsafe_allow_html=True)
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.text_input("A", key=f"a_ta_{rid}", value=ss[f"a_ta_{rid}"], label_visibility="visible")
    with r1c2:
        st.text_input("B", key=f"b_ta_{rid}", value=ss[f"b_ta_{rid}"], label_visibility="visible")
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.text_input("C", key=f"c_ta_{rid}", value=ss[f"c_ta_{rid}"], label_visibility="visible")
    with r2c2:
        st.text_input("D", key=f"d_ta_{rid}", value=ss[f"d_ta_{rid}"], label_visibility="visible")
    st.markdown('</div>', unsafe_allow_html=True)

    # Glossary + Answer row (inline, minimal)
    g1, g2 = st.columns([1,1])
    with g1:
        st.text_input("சொல் அகராதி / Glossary", placeholder="(Type the word)", key=f"gloss_{rid}")
        st.button("Go", key=f"go_{rid}", use_container_width=True)
    with g2:
        st.text_input("பதில் / Answer", key=f"ans_ta_{rid}", value=ss[f"ans_ta_{rid}"], label_visibility="visible")

    # Explanation (taller)
    st.text_area("விளக்கங்கள் :", key=f"exp_ta_{rid}", value=ss[f"exp_ta_{rid}"], height=180)
