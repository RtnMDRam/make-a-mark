# lib/ux_mobile.py
import streamlit as st
from typing import List, Dict, Tuple

def enable_ipad_keyboard_aid():
    # adds bottom padding + auto scroll on focus so the keyboard doesn't hide inputs
    st.markdown("""
    <style>
      .block-container { padding-bottom: max(28dvh, env(safe-area-inset-bottom)); }
      .stTextInput, .stTextArea, .stNumberInput, .stSelectbox { margin-bottom: .25rem !important; }
    </style>
    <script>
      (function(){
        function bringIntoView(e){
          try{
            const el=e.target;
            const rect=el.getBoundingClientRect();
            const bottomSafe = window.innerHeight * 0.30;
            if(rect.bottom > window.innerHeight - bottomSafe){
              el.scrollIntoView({block:"center",behavior:"smooth"});
            }
          }catch(err){}
        }
        document.addEventListener('focusin', bringIntoView, {passive:true});
      })();
    </script>
    """, unsafe_allow_html=True)

def glossary_drawer(glossary: List[Dict[str,str]], query: str) -> Tuple[str, str, str]:
    """
    Minimal right-side slide drawer:
    - returns (new_query, new_en, new_ta)
    """
    st.markdown("""
    <style>
      #gToggle { position: fixed; right: 12px; top: calc(var(--header-h,5dvh) + 8px); z-index: 9999;}
      .gPanel {
        position: fixed; top: calc(var(--header-h,5dvh) + 4px); right: 0; width: min(46vw, 360px);
        height: calc(100dvh - var(--header-h,5dvh) - 8px);
        background: #0b3d27; color: #fff; border-left: 2px solid #0e603b;
        transform: translateX(100%); transition: transform .25s ease; z-index: 9998;
        padding: 10px 12px; overflow:auto; box-shadow: -4px 0 12px rgba(0,0,0,.25);
      }
      .gPanel.show { transform: translateX(0%); }
      .gBtn { background:#0e603b; color:#fff; border:none; padding:8px 10px; border-radius:6px; }
      .gTerm { background:#0f4a31; border-radius:6px; padding:6px 8px; margin-bottom:6px; }
      .gTerm b { color:#d5ffdf; }
    </style>
    <button id="gToggle" class="gBtn">📚 Glossary</button>
    <div id="gPanel" class="gPanel"></div>
    <script>
      const gT=document.getElementById('gToggle');
      const gP=document.getElementById('gPanel');
      if(gT && gP){
        gT.onclick=()=>{ gP.classList.toggle('show'); }
      }
    </script>
    """, unsafe_allow_html=True)

    # Streamlit inputs (live)
    col = st.sidebar if False else st  # keep logic simple; panel is HTML, inputs below feed it
    q = col.text_input("🔎 Vocabulary search", value=query, placeholder="Type English word to search…")
    en = col.text_input("➕ Add English")
    ta = col.text_input("➕ Add Tamil")
    if en.strip() and ta.strip():
        st.session_state.setdefault("glossary", [])
    # Render the matches list inside page (compact)
    if glossary:
        matches = [g for g in glossary if q.strip().lower() in (g.get("en","").lower())] if q.strip() else glossary
        st.markdown("**Matches:**")
        for g in matches[:50]:
            st.markdown(f"<div class='gTerm'><b>{g.get('en','')}</b><br>{g.get('ta','')}</div>", unsafe_allow_html=True)
    return q, en, ta
