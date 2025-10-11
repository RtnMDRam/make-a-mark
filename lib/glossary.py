# lib/glossary.py (stub)
import streamlit as st

def ui(glossary: list, query: str = "") -> str:
    """Very small placeholder: shows glossary and returns possibly updated query."""
    st.markdown("### Vocabulary / சொற்கஞ்சியம்")
    if glossary:
        st.write(", ".join(f"{g.get('en','')} → {g.get('ta','')}" for g in glossary))
    else:
        st.info("No glossary yet. Add below.")
    with st.expander("Add to glossary"):
        en = st.text_input("English")
        ta = st.text_input("Tamil")
        if st.button("➕ Add term"):
            if en.strip() and ta.strip():
                glossary.append({"en": en.strip(), "ta": ta.strip()})
                st.success("Added.")
    return st.text_input("🔎 Quick lookup (type English word)", value=query)
