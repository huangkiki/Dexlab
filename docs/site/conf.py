"""Bilingual documentation; building it never imports a physics runtime."""
import os
from pathlib import Path
import tomllib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
project = 'DexLab'
author = 'DexLab contributors'
copyright = '2026, DexLab contributors'
release = tomllib.loads((ROOT / 'pyproject.toml').read_text())['project']['version']
language = os.environ.get('DEXLAB_DOCS_LANGUAGE', 'zh_CN')
assert language in ('zh_CN', 'en')
extensions = ['myst_parser', 'sphinx_design']
source_suffix = {'.md': 'markdown'}
root_doc = 'index'
myst_enable_extensions = ['colon_fence', 'deflist']
myst_heading_anchors = 3
html_theme = 'pydata_sphinx_theme'
html_title = 'DexLab · ' + ('接触动力学实验' if language == 'zh_CN' else 'Contact dynamics experiments')
html_static_path = [str(HERE / '_static'), str(ROOT / 'docs/evidence')]
html_css_files = ['dexlab.css']
html_js_files = [('replay.js', {'defer': 'defer'})]
templates_path = [str(HERE / '_templates')]
html_show_sourcelink = False
html_theme_options = {
    'logo': {'text': 'DexLab'},
    'github_url': 'https://github.com/huangkiki/Dexlab',
    'navigation_depth': 2,
    'show_nav_level': 1,
    'header_links_before_dropdown': 6,
    'navbar_end': ['theme-switcher', 'languages', 'navbar-icon-links'],
    'footer_start': ['copyright'],
    'footer_end': ['sphinx-version', 'theme-version'],
}
html_context = {
    'default_mode': 'light',
    'other_language': 'English' if language == 'zh_CN' else '简体中文',
    'other_language_root': '../../en/latest/' if language == 'zh_CN' else '../../zh-cn/latest/',
}


def setup(app):
    # Sphinx 9.1 selects the JS constructor from language_name, but Chinese
    # indexing deliberately uses english-stemmer.js. Retain Chinese tokenization.
    from sphinx.search.zh import SearchChinese

    class ChineseSearch(SearchChinese):
        language_name = 'English'

    app.add_search_language(ChineseSearch)
