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
extensions = ['myst_parser', 'sphinx_design', 'sphinx.ext.mathjax']
source_suffix = {'.md': 'markdown'}
root_doc = 'index'
myst_enable_extensions = ['colon_fence', 'deflist', 'dollarmath', 'amsmath']
myst_heading_anchors = 6
html_theme = 'pydata_sphinx_theme'
html_title = 'DexLab · ' + ('仿真器与模型共同进化' if language == 'zh_CN' else 'Simulator and model co-evolution')
html_static_path = [str(HERE / '_static'), str(ROOT / 'docs/evidence')]
html_css_files = ['dexlab.css']
html_js_files = [('replay.js', {'defer': 'defer'}), ('cutting.js', {'defer': 'defer'}), ('live-lab.js', {'defer': 'defer'}), ('learning-diagrams.js', {'type': 'module'})]
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
    def select_home_template(app, pagename, templatename, context, doctree):
        # Nested course pages need a language switch relative to their own route.
        context['other_language_root'] = '../' * (len(pagename.split('/')) + 1) + (
            'en/latest/' if app.config.language == 'zh_CN' else 'zh-cn/latest/')
        if pagename == 'index':
            context['homepage_is_chinese'] = app.config.language in ('zh_CN', 'zh')
            return 'research-home.html'

    app.connect('html-page-context', select_home_template)

    # Sphinx 9.1 selects the JS constructor from language_name, but Chinese
    # indexing deliberately uses english-stemmer.js. Retain Chinese tokenization.
    from sphinx.search.zh import SearchChinese

    class ChineseSearch(SearchChinese):
        language_name = 'English'

    app.add_search_language(ChineseSearch)
