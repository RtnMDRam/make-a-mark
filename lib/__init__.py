# make-a-mark/lib/__init__.py
"""
Library exports for the SME QC Panel.
Keep this in sync with what pages import.
"""

# Top controls (Save / Next / Download + Load)
from .top_strip import render_top_strip

# Main renderer (boxes + non-editable content + editor)
from .qc_state import render_reference_and_editor

__all__ = [
    "render_top_strip",
    "render_reference_and_editor",
]
