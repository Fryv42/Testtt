import os
import sys

sys.path.insert(0, os.path.abspath('..'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sapere_aude.settings')

import django

django.setup()

project = 'Quiz Service'
copyright = '2024, Team'
author = 'Team'
version = '0.1.0'

# Корневой документ: docs/docs/index.rst -> имя "docs/index"
master_doc = 'docs/index'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
html_theme = 'alabaster'
html_static_path = ['_static']