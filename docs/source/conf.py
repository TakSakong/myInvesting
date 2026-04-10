import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'myInvesting'
copyright = '2026, TakSakong'
author = 'TakSakong'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',      # 파이썬 소스코드의 독스트링(docstring)을 자동으로 가져와 문서화
    'sphinx.ext.napoleon',     # Google 및 NumPy 스타일의 독스트링을 깔끔하게 파싱
    'sphinx.ext.viewcode',     # 빌드된 문서에 소스코드를 볼 수 있는 링크 추가
    'sphinx.ext.intersphinx',  # 다른 프로젝트(Python, Flask 등)의 공식 문서로 자동 링크
    'sphinx_rtd_theme',        # Read the Docs 테마 적용 (alabaster보다 훨씬 가독성이 좋음, 이미 pip로 설치하셨습니다)
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'flask': ('https://flask.palletsprojects.com/en/latest/', None),
}

templates_path = ['_templates']
exclude_patterns = []

language = 'ko'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
