# Sphinx configuration for OST AI Engine
project = 'OST AI Engine'
copyright = '2025, opensource-together'
author = 'spideyai-x'
release = '0.1.0'
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Furo theme
html_theme = 'furo'
html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
}

html_static_path = ['_static']