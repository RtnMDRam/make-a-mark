# lib/__init__.py
# -------------------------------------------------------------------
# Initialize the "lib" package and expose key helper modules for Streamlit.
# This version is cleaned up for the new 3-panel SME QC layout.
# -------------------------------------------------------------------

# Common library imports
import streamlit as st

# Submodules (only the active ones)
from .top_strip import render_top_strip
from .qc_state import render_layout_only

# You can add new utility functions or constants here in future if needed.
__all__ = ["render_top_strip", "render_layout_only"]
