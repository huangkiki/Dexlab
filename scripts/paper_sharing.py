"""Validate bilingual paper sources and render the shared reader around each article."""

from html import escape
from pathlib import Path
from posixpath import relpath
import re
from urllib.parse import quote, urlsplit

from bs4 import BeautifulSoup

PAPER_DIRECTORY = Path("_static/research/paper-sharing")
HEADING_TAGS = ("h2", "h3", "h4", "h5", "h6")
LANGUAGES = (("paper-en", "en"), ("paper-zh", "zh-CN"))


def bilingual_text(block):
    children = block.find_all(class_=["paper-en", "paper-zh"], recursive=False)
    if len(children) == len(LANGUAGES) and all(
        name in child.get("class", ()) and child.get("lang") == lang
        for child, (name, lang) in zip(children, LANGUAGES)
    ):
        english, chinese = (child.get_text(" ", strip=True) for child in children)
        if english and chinese:
            return english, chinese
    context = block.get("id") or block.get_text(" ", strip=True)[:70]
    raise ValueError(f"Expected English followed by Chinese in <{block.name}> {context}")


def outline_html(sections, depth=3):
    indent = "  " * depth
    lines = [f"{indent}<ul>"]
    for section in sections:
        heading = section.find(HEADING_TAGS, recursive=False)
        anchor = section.get("id")
        if not anchor or heading is None:
            raise ValueError("Each paper section needs an ID and a bilingual heading")
        english, chinese = bilingual_text(heading)
        if "ltx_abstract" in section.get("class", ()):
            english = english.removesuffix(".")
        lines.extend([
            f'{indent}  <li><a href="#{quote(anchor, safe="")}">',
            f'{indent}    <span class="paper-en" lang="en">{escape(english)}</span>',
            f'{indent}    <span class="paper-zh" lang="zh-CN">{escape(chinese)}</span>',
            f"{indent}  </a>",
        ])
        children = section.find_all("section", recursive=False)
        if children:
            lines.append(outline_html(children, depth + 2))
        lines.append(f"{indent}  </li>")
    lines.append(f"{indent}</ul>")
    return "\n".join(lines)


def render_paper(source, asset_path):
    page = BeautifulSoup(source, "html.parser")
    if page.body is None or [tag.name for tag in page.body.find_all(recursive=False)] != ["article"]:
        raise ValueError("Paper sources must contain one article directly inside the body")
    article = page.article
    if article.h1 is None or not bilingual_text(article.h1)[0].endswith("："):
        raise ValueError("Use an English：Chinese title with the colon at the end of the English span")

    authors = article.select_one(".translation-meta .authors")
    sources = article.select(".translation-meta a[href]")
    if not authors or not authors.get_text(strip=True) or not any(
        urlsplit(link["href"]).hostname == "arxiv.org" for link in sources
    ):
        raise ValueError("Include the authors and the original arXiv link in the paper metadata")
    if not article.select_one("p.paper-pair"):
        raise ValueError("Mark bilingual paragraphs with the paper-pair class")
    for block in article.select(".paper-pair"):
        bilingual_text(block.find(class_="paper-algorithm-text", recursive=False) or block)

    ids = [element["id"] for element in article.select("[id]")]
    if len(ids) != len(set(ids)):
        raise ValueError("Paper anchor IDs must be unique")
    sections = article.find_all("section", recursive=False)
    if not sections:
        raise ValueError("Paper sources need at least one section")
    abstract = article.find(class_="ltx_abstract", recursive=False)
    if abstract is not None:
        sections.insert(0, abstract)
    outline = outline_html(sections)
    expected = [f'#{quote(section.get("id", ""), safe="")}' for section in article.find_all("section")]
    if abstract is not None:
        expected.insert(0, f'#{quote(abstract["id"], safe="")}')
    links = BeautifulSoup(outline, "html.parser").select("a[href]")
    if [link["href"] for link in links] != expected:
        raise ValueError("The outline must link each section in document order. Nest sections directly.")

    # Insert the reader around the original bytes so scientific HTML and fragment IDs stay intact.
    head, end_head, body = source.partition("</head>")
    body, end_body, footer = body.rpartition("</body>")
    opening = re.match(r"\s*<body\b[^>]*>", body)
    if not end_head or not end_body or opening is None:
        raise ValueError("Paper sources need explicit head and body tags")
    assets = escape(asset_path)
    return (
        f'{head}<link href="{assets}/paper-bilingual.css" rel="stylesheet"/>\n'
        f'<link href="{assets}/paper-index.css" rel="stylesheet"/>\n'
        f'<script defer src="{assets}/paper-index.js"></script>\n'
        f"{end_head}{body[:opening.end()]}\n"
        '<main class="paper-reader">\n'
        '<aside class="paper-index">\n'
        '  <details class="paper-index-panel">\n'
        "    <summary>\n"
        "      <span>目录</span>\n"
        '      <span class="paper-index-position"></span>\n'
        "    </summary>\n"
        '    <nav aria-label="目录">\n'
        f"{outline}\n"
        "    </nav>\n"
        "  </details>\n"
        "</aside>\n"
        f"{body[opening.end():].strip()}\n</main>\n{end_body}{footer}"
    )


def prepare_paper_readers(site):
    directory = site / PAPER_DIRECTORY
    rendered = {}
    for path in sorted(directory.rglob("*.html")):
        destination = path.relative_to(site)
        try:
            rendered[destination] = render_paper(
                path.read_text(encoding="utf-8"), relpath(directory, path.parent)
            )
        except ValueError as error:
            raise ValueError(f"{destination}: {error}") from error
    return rendered
