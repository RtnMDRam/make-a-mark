# lib/glossary.py

import streamlit as st
import pandas as pd
import os

# --- FILE LOCATIONS ---

GLOSSARY_FILE = "glossary_terms.csv"
PENDING_FILE = "pending_glossary.csv"

# --- LOADING & SAVING HELPERS ---

def load_glossary(path=GLOSSARY_FILE):
    if os.path.exists(path):
        df = pd.read_csv(path)
        return [{"en": row['en'], "ta": row['ta']} for _, row in df.iterrows()]
    return []

def save_glossary(glossary, path=GLOSSARY_FILE):
    pd.DataFrame(glossary).to_csv(path, index=False)

def load_pending(path=PENDING_FILE):
    if os.path.exists(path):
        df = pd.read_csv(path)
        return [{"en": row['en'], "ta": row['ta']} for _, row in df.iterrows()]
    return []

def save_pending(pending, path=PENDING_FILE):
    pd.DataFrame(pending).to_csv(path, index=False)

# --- INITIALIZE SESSION ---

if "glossary" not in st.session_state:
    st.session_state.glossary = load_glossary()
if "pending_glossary" not in st.session_state:
    st.session_state.pending_glossary = load_pending()

# --- GLOSSARY UTILITIES ---

def sort_glossary(items):
    return sorted(items, key=lambda x: (x.get("en","") or "").lower())

def render_matches(glossary, query):
    if not query.strip():
        if glossary:
            gl = sort_glossary(glossary)
            return "**Recently added**<br>" + "<br>".join([f"• <b>{g['en']}</b> → {g['ta']}" for g in gl[-8:]])
        return "_No glossary yet. Add below._"
    hits = [g for g in glossary if query.strip().lower() in (g.get("en", "") or "").lower()]
    if not hits:
        return "_No matches._"
    return "**Matches**<br>" + "<br>".join([f"• <b>{g['en']}</b> → {g['ta']}" for g in sort_glossary(hits)])

# --- SME PANEL ---

def glossary_panel_sme():
    st.subheader("Glossary Search & Add (Teacher/SME)")
    query = st.text_input("Type English word to look up:", key="glossary_query")
    st.markdown(render_matches(st.session_state.glossary, query), unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Add a new glossary term (pending admin review):**")
    new_en = st.text_input("New English term", key="new_en")
    new_ta = st.text_input("Tamil translation", key="new_ta")
    add_btn = st.button("➕ Submit for Approval")
    if add_btn:
        exists = any(
            (new_en.strip().lower() == g['en'].strip().lower() and new_ta.strip() == g['ta'].strip())
            for g in st.session_state.glossary
        ) or any(
            (new_en.strip().lower() == g['en'].strip().lower() and new_ta.strip() == g['ta'].strip())
            for g in st.session_state.pending_glossary
        )
        if not new_en.strip() or not new_ta.strip():
            st.warning("Both fields required.")
        elif exists:
            st.info("Already present in glossary or pending approval.")
        else:
            st.session_state.pending_glossary.append({"en": new_en.strip(), "ta": new_ta.strip()})
            save_pending(st.session_state.pending_glossary)
            st.success(f"Submitted for admin review: {new_en.strip()} → {new_ta.strip()}")

# --- ADMIN PANEL ---

def glossary_panel_admin():
    st.subheader("Pending Glossary Terms (Admin Review)")
    if not st.session_state.pending_glossary:
        st.info("No pending glossary terms to approve.")
        return
    for idx, entry in enumerate(st.session_state.pending_glossary.copy()):
        c1, c2, c3 = st.columns([4, 4, 2])
        with c1:
            st.write(f"**English**: {entry['en']}")
        with c2:
            st.write(f"**Tamil**: {entry['ta']}")
        with c3:
            approve = st.button("✅ Approve", key=f"approve_{idx}")
            reject = st.button("❌ Reject", key=f"reject_{idx}")
        if approve:
            st.session_state.glossary.append(entry)
            save_glossary(st.session_state.glossary)
            st.session_state.pending_glossary.remove(entry)
            save_pending(st.session_state.pending_glossary)
            st.success(f"Approved and added: {entry['en']} → {entry['ta']}")
            st.experimental_rerun()
        if reject:
            st.session_state.pending_glossary.remove(entry)
            save_pending(st.session_state.pending_glossary)
            st.warning(f"Rejected: {entry['en']} → {entry['ta']}")
            st.experimental_rerun()

# --- PANEL TOGGLE FOR TESTING ---
panel = st.radio("Choose panel", ["Teacher/SME Glossary", "Admin Glossary Review"])
if panel == "Teacher/SME Glossary":
    glossary_panel_sme()
else:
    glossary_panel_admin()
