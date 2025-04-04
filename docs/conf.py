"""Sphinx configuration."""
project = "OneMeter Cloud Integration"
author = "OneMeter Contributors"
copyright = "2023-2024, OneMeter Contributors"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_rtd_theme",
    "myst_parser",
    "sphinx_copybutton",
]
autodoc_typehints = "description"
html_theme = "sphinx_rtd_theme"
myst_heading_anchors = 3