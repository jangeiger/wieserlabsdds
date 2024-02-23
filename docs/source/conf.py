# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Wieserlabs DDS'
copyright = '2024'
author = ''

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',               # For automatically generating docs
    'sphinx.ext.autosummary',           # For automatically generating docs
    'sphinx.ext.inheritance_diagram',   # For visualizing dependencies
    'sphinx.ext.napoleon',              # To support numpy docs style
    "sphinx_rtd_theme",                 # Custom theme
    "sphinx.ext.mathjax"                # display equations
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
