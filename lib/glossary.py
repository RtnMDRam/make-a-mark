import streamlit as st
import pandas as pd
import os

BASE_DIR = "./glossaries"  # Change to your actual shared/cloud dir
os.makedirs(BASE_DIR, exist_ok=True)

def get_csv_path(subject, unit=None):
    """Get CSV path for a master/unit glossary."""
    if unit:
        return os.path.join(BASE_DIR, f"{subject.lower()}_unit{unit}.csv")
    return os.path.join(BASE_DIR, f"{subject.lower()}_master.csv")

def get_pending_path(subject, unit=None):
    if unit:
        return os.path.join(BASE_DIR, f"{subject.lower()}_unit{unit}_pending.csv")
    return os.path.join(BASE_DIR, f"{subject.lower()}_master_pending.csv")

def load_glossary(subject, unit=None):
    path = get_csv_path(subject, unit)
    if os.path.exists(path):
        df = pd.read_csv(path)
        return [{"en": row['en'], "ta": row['ta']} for _, row in df.iterrows()]
    return []

def save_glossary(glossary, subject, unit=None):
    path = get_csv_path(subject, unit)
    pd.DataFrame(glossary).to_csv(path, index=False)

def load_pending(subject, unit=None):
    path = get_pending_path(subject, unit)
    if os.path.exists(path):
        df = pd.read_csv(path)
        return [{"en": row['en'], "ta": row['ta']} for _, row in df.iterrows()]
    return []

def save_pending(pending, subject, unit=None):
    path = get_pending_path(subject, unit)
    pd.DataFrame(pending).to_csv(path, index=False)

def sort_glossary(items):
    return sorted(items, key=lambda x: (x.get("en", "") or "").lower())

def render_matches(glossary, query):
    if not query.strip():
        return "**Recently added**<br>" + "<br>".join(
            [f"• <b>{g['en']}</b> → {g['ta']}" for g in sort_glossary(glossary)[-8:]]
        ) if glossary else "_No glossary yet. Add below._"
    hits = [g for g in glossary if query.strip().lower() in (g.get("en", "") or "").lower()]
    return "**Matches**<br>" + "<br>".join(
        [f"• <b>{g['en']}</b> → {g['ta']}" for g in sort_glossary(hits)]
    ) if hits else "_No matches._"

def glossary_panel_sme(subject, unit):
    st.subheader(f"Glossary: {subject.capitalize()} – Unit {unit if unit else 'Master'} (Teacher/SME)")
    glossary = load_glossary(subject, unit)
    query = st.text_input("Type English word to look up:", key=f"glossary_query_{subject}_{unit}")
    st.markdown(render_matches(glossary, query), unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Add new glossary term (pending review):**")
    new_en = st.text_input("New English term", key=f"new_en_{subject}_{unit}")
    new_ta = st.text_input("Tamil translation", key=f"new_ta_{subject}_{unit}")
    add_btn = st.button("➕ Submit for Approval", key=f"add_btn_{subject}_{unit}")
    pending = load_pending(subject, unit)
    if add_btn:
        exists = any(
            (new_en.strip().lower() == g['en'].strip().lower() and new_ta.strip() == g['ta'].strip())
            for g in glossary
        ) or any(
            (new_en.strip().lower() == g['en'].strip().lower() and new_ta.strip() == g['ta'].strip())
            for g in pending
        )
        if not new_en.strip() or not new_ta.strip():
            st.warning("Both fields required.")
        elif exists:
            st.info("Already present or pending approval.")
        else:
            pending.append({"en": new_en.strip(), "ta": new_ta.strip()})
            save_pending(pending, subject, unit)
            st.success("Submitted for admin review.")

def glossary_panel_admin(subject, unit):
    st.subheader(f"Pending Terms: {subject.capitalize()} – Unit {unit if unit else 'Master'} (Admin)")
    pending = load_pending(subject, unit)
    glossary = load_glossary(subject, unit)
    master = load_glossary(subject)  # always subject-level master
    if not pending:
        st.info("No pending terms to approve.")
        return
    for idx, entry in enumerate(pending.copy()):
        c1, c2, c3 = st.columns([4, 4, 2])
        with c1: st.write(f"**English**: {entry['en']}")
        with c2: st.write(f"**Tamil**: {entry['ta']}")
        with c3:
            approve = st.button("✅ Approve", key=f"approve_{subject}_{unit}_{idx}")
            reject = st.button("❌ Reject", key=f"reject_{subject}_{unit}_{idx}")
        if approve:
            glossary.append(entry)
            save_glossary(glossary, subject, unit)
            if entry not in master:
                master.append(entry)
                save_glossary(master, subject)
            pending.remove(entry)
            save_pending(pending, subject, unit)
            st.success("Approved and added.")
            st.experimental_rerun()
        if reject:
            pending.remove(entry)
            save_pending(pending, subject, unit)
            st.warning("Rejected.")
            st.experimental_rerun()

# --- Example driver code ---
subject = st.selectbox("Select Subject", ["biology", "physics", "chemistry"])
unit = st.text_input("Unit (leave blank for master glossary)", key="unit_id")
panel_type = st.radio("Panel Type", ["Teacher/SME", "Admin"])
if panel_type == "Teacher/SME":
    glossary_panel_sme(subject, unit if unit else None)
else:
    glossary_panel_admin(subject, unit if unit else None)
