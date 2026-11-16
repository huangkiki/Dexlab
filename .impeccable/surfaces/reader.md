# Shared content reader

Mode: Read. Scope: Sphinx article, report, documentation and Blog pages rendered by `_templates/reader-page.html`.

## Direction contract

THESIS: Use one site-level navigation and one page-level orientation layer. Readers should never compare a global category against the same site tree repeated in a sidebar before reaching the article.

OWN-WORLD: Warm paper, charcoal type and fine rules. The masthead remains horizontal; the article is centered; an optional current-page outline sits on the right.

STORY: Choose a site section from the masthead, read the page, and use the right outline only when the current page is long enough to need it.

FIRST VIEWPORT: Global masthead, article title and lead. No "all content" chapter rail. Long pages reveal a current-page outline at the right after the masthead.

ADAPTATION: The desktop reader uses a 760px article plus 160px outline within 1040px. At 1200px and below the outline is removed and the article centers at 840px. At 800px and below the layout is a single flow using the shared page gutters. Blog uses an 880px centered index without an outline.

REMOVED: The left rail's generated full-site Sphinx toctree and duplicate "All content / 全部内容" disclosure. Site sections remain reachable from the masthead; page headings remain reachable from the right outline.
