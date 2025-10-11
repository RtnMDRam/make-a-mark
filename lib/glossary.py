# lib/glossary.py
from typing import List, Dict

def sort_glossary(items: List[Dict[str,str]]):
    return sorted(items, key=lambda x: (x.get("en","") or "").lower())

def render_matches(glossary: List[Dict[str,str]], query: str) -> str:
    if not query.strip():
        if glossary:
            gl = sort_glossary(glossary)
            return "<b>Recently added</b><br>" + "<br>".join([f"• <b>{g['en']}</b> → {g['ta']}" for g in gl[-8:]])
        return "No glossary yet. Add below."
    hits = [g for g in glossary if (g.get("en") or "").lower().startswith(query.strip().lower())]
    if not hits:
        return "No matches."
    return "<b>Matches</b><br>" + "<br>".join([f"• <b>{g['en']}</b> → {g['ta']}" for g in sort_glossary(hits)])
