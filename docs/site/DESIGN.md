---
name: DexLab Research Homepage and Learning
description: A warm-paper research index and learning route shaped by the existing dexterous-simulation guide.
colors:
  accent: '#4f664c'
  page: '#fafaf6'
  panel: '#f0f1eb'
  ink: '#282b26'
  muted: '#60675a'
  rule: '#dcded4'
  media: '#111820'
typography:
  hero-display:
    fontFamily: Georgia, "Noto Serif CJK SC", "Source Han Serif SC", "Songti SC", serif
    fontSize: 96px
    fontWeight: 400
    lineHeight: .88
    letterSpacing: -.04em
  display:
    fontFamily: Georgia, "Noto Serif CJK SC", "Source Han Serif SC", "Songti SC", serif
    fontSize: 52px
    fontWeight: 400
    lineHeight: 1.42
    letterSpacing: -.025em
  headline:
    fontFamily: Arial, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 26px
    fontWeight: 600
    lineHeight: 1.55
  title:
    fontFamily: Arial, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 21px
    fontWeight: 700
    lineHeight: 1.55
  body:
    fontFamily: Arial, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 16px
    lineHeight: 1.95
  label:
    fontFamily: Arial, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 14px
    lineHeight: 1.95
  caption:
    fontFamily: Arial, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 13px
    lineHeight: 1.8
  meta-label:
    fontFamily: Arial, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 12px
    fontWeight: 700
    lineHeight: 1.8
  micro-label:
    fontFamily: Arial, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 11px
    fontWeight: 700
    lineHeight: 1.8
  guide-link:
    fontFamily: Arial, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 18px
    fontWeight: 600
    lineHeight: 1.95
  step-number:
    fontFamily: Georgia, "Noto Serif CJK SC", "Source Han Serif SC", "Songti SC", serif
    fontSize: 22px
    lineHeight: 1.55
  learning-display:
    fontFamily: Georgia, "Noto Serif CJK SC", "Source Han Serif SC", "Songti SC", serif
    fontSize: 36px
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: -.02em
  learning-display-compact:
    fontFamily: Georgia, "Noto Serif CJK SC", "Source Han Serif SC", "Songti SC", serif
    fontSize: 30px
    fontWeight: 400
    lineHeight: 1.4
  learning-display-narrow:
    fontFamily: Georgia, "Noto Serif CJK SC", "Source Han Serif SC", "Songti SC", serif
    fontSize: 28px
    fontWeight: 400
    lineHeight: 1.4
  learning-headline:
    fontFamily: Arial, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 24px
    fontWeight: 600
    lineHeight: 1.5
  learning-title:
    fontFamily: Arial, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 19px
    fontWeight: 700
    lineHeight: 1.9
  learning-body:
    fontFamily: Arial, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 16px
    lineHeight: 1.9
  learning-label:
    fontFamily: Arial, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 14px
    lineHeight: 1.9
  learning-caption:
    fontFamily: Arial, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 13px
    lineHeight: 1.9
  learning-output:
    fontFamily: Arial, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 22px
    fontWeight: 700
    lineHeight: 1.9
rounded:
  learning-control: 4px
spacing:
  compact: 8px
  inline: 12px
  text: 16px
  group: 24px
  media-gap: 28px
  learning-gap: 32px
  column-gap: 36px
  desktop-gutter: 40px
components:
  guide-title:
    textColor: '{colors.ink}'
    typography: '{typography.display}'
  guide-link:
    textColor: '{colors.accent}'
    typography: '{typography.guide-link}'
  text-link:
    textColor: '{colors.accent}'
    typography: '{typography.label}'
  navigation-link:
    textColor: '{colors.muted}'
    typography: '{typography.label}'
    padding: 4px 0
  topic-button:
    backgroundColor: transparent
    textColor: '{colors.muted}'
    padding: 12px 0
  topic-button-selected:
    textColor: '{colors.accent}'
  research-loop:
    textColor: '{colors.ink}'
    typography: '{typography.label}'
  reading-link:
    textColor: '{colors.ink}'
    padding: 18px 0
  concept-field:
    textColor: '{colors.accent}'
    opacity: .17
  concept-trigger:
    textColor: '{colors.accent}'
    typography: '{typography.caption}'
  concept-term:
    textColor: '{colors.ink}'
    typography: '{typography.label}'
    padding: 7px 0
  concept-term-related:
    textColor: '{colors.accent}'
  concept-term-contrast:
    textColor: '{colors.ink}'
  concept-filter:
    backgroundColor: transparent
    textColor: '{colors.muted}'
    padding: 6px 0
  concept-filter-selected:
    textColor: '{colors.accent}'
  concept-lens:
    textColor: '{colors.ink}'
    padding: 20px 0 24px
  learning-number:
    textColor: '{colors.accent}'
    typography: '{typography.step-number}'
  evidence-gif:
    backgroundColor: '{colors.panel}'
    width: 100%
  evidence-boundary:
    textColor: '{colors.muted}'
    typography: '{typography.label}'
    padding: 16px 0 0
  learning-action:
    backgroundColor: transparent
    textColor: '{colors.accent}'
    typography: '{typography.learning-body}'
    rounded: '{rounded.learning-control}'
    padding: 8px 14px
  learning-action-read:
    backgroundColor: '{colors.accent}'
    textColor: '{colors.page}'
  learning-chapter-current:
    backgroundColor: '{colors.panel}'
    textColor: '{colors.accent}'
    typography: '{typography.learning-label}'
    rounded: '{rounded.learning-control}'
    padding: 10px 12px
  learning-time-example:
    backgroundColor: '{colors.panel}'
    textColor: '{colors.ink}'
    padding: 24px
---

# Design System: DexLab Research Homepage and Learning

## Overview

**Creative North Star: "The Research Reading Index"**

The homepage shares the existing dexterous-simulation guide's warm paper, charcoal text, muted green links and serif opening title. It is an editorial research entrance: the first screen establishes the project and primary index action; scrolling reveals the authored architecture diagram, a concept field, a separate research-topic index, a five-case evidence sequence, three research judgments and direct continuation links. Fine rules and open rows carry the hierarchy.

This system governs the Chinese and English research homepages, the MuJoCo learning route and every Sphinx content page. Ordinary articles use the unified reader in `_templates/reader-page.html`: one global masthead, a 760px reading column and an optional current-page outline. The dedicated left chapter rail remains only on the course route, where it represents an ordered lesson sequence rather than the entire website. The canonical Blog page owns the pre-expanded category index. The existing article remains the visual reference; report content and scientific scope stay independently maintained. The separate browser application retains its own design system.

**Key Characteristics:**

- Warm paper and charcoal, with restrained green reading accents.
- A horizontal masthead, oversized serif opening title and one ruled content entrance.
- A semantic field of curated concepts and canonical solver options below the opening entry, resolving into view with scroll, with individual hover focus and a searchable relationship atlas.
- A separate, compact research-topic index for cross-experiment articles, so article titles do not break the concept cloud or compete with individual terms.
- The original architecture diagram and ruled scroll-revealed evidence sequence, with the hardware-free validation boundary closing the research reading order.
- A grouped research-guide taxonomy with two foundation lanes and four persistent research topics.
- A flat site hierarchy: global masthead first, current-page outline second, no repeated all-site tree.
- Engine comparisons led by a conclusion, explicit criteria, synchronized panes and a compact result matrix.
- Original experiment media, native controls and explicit evidence boundaries.
- A MuJoCo learning column with chapter navigation, explicit reading bookmarks and small teaching interactions.

Source of truth: `_static/research-palette.css`, `_static/research-home.css`, `_static/concept-atlas.css`, `_static/concept-atlas.js`, `_templates/research-home.html`, `docs/concept-atlas.json`, and `zh/index.md` / `en/index.md`. The Blog index uses `zh/blog.md` inside the shared reader. The reference is `_static/research/dexterous-simulation.html`. Frontmatter contains implemented tokens. The sidecar adds component previews and responsive metadata; its tonal ramps are preview aids, not production colors.

The learning surface uses `_static/simulation-learning.css`, `_templates/simulation-learning.html`, `_static/simulation-learning.js`, and both languages' `learning.md` / `mujoco-learning/` lessons. Its route contract is in the root `.impeccable/surfaces/mujoco-learning.md`. The shared reader uses `_static/reader-page.css`, `_templates/reader-page.html` and `_static/reader-page.js`; it imports the learning styles and the existing evidence-component styles before applying report-specific layout overrides.

The standalone research guide in `_static/research/dexterous-simulation.html` keeps its self-contained HTML and filters. Its taxonomy and responsive page contract are recorded in `.impeccable/surfaces/research-guide.md`.

## Colors

One restrained green accent sits among warm, low-chroma neutrals shared with the article.

### Primary

- **Reading Green** (`accent`): links, the first navigation destination, selected topic controls, learning numbers and the improvement branch in the research loop.

### Neutral

- **Warm Paper** (`page`): the page canvas and text on the focused skip link.
- **Paper Wash** (`panel`): the stage behind recorded GIF previews.
- **Recorded Media** (`media`): the neutral stage behind recorded GIF previews.
- **Charcoal** (`ink`): titles, body text, reading rows, summary labels and hovered ordinary links.
- **Muted Olive Gray** (`muted`): supporting text, captions and resting navigation.
- **Fine Rule** (`rule`): reading-rail edge, section separators and reading rows.

The learning surface reuses these colors. Paper Wash also marks the current chapter, teaching example, code and blockquotes; Reading Green identifies links, controls and explicit read state. Its CSS names `page` as `--paper` and `accent` as `--green` without changing their values.

**The Evidence Color Rule.** Interface color organizes reading; recorded experiment colors retain their original meaning.

## Typography

The opening title and masthead use the serif stack; the body, section headings and controls use the sans-serif stack. Both use installed system fallbacks without an external font request. The homepage opening title uses the 96px hero display at regular weight; the two-line thesis and major map headings return to the serif face. Topic headings and article titles use the sans stack at semibold or bold weight.

Use hero display for the DexLab title, display for the two-line thesis and map headings, title for research questions and topic headings, body for reading text, label for navigation and caption for evidence explanations. The homepage lead is (17px) and limited to (700px); the entrance action is (20px) with a (14px) supporting line.

The homepage title uses `clamp(4.2rem, 12vw, 6rem)`. At (700px) and below it becomes `clamp(4rem, 18vw, 5rem)`, the thesis (30px), map headings (36px), lead (16px), entrance action (18px), and navigation labels (13px). The entrance stacks its arrow below the text rather than shrinking the action.

### MuJoCo learning typography

The `learning-*` tokens apply only to the course reader: a regular serif lesson title, sans-serif section and subsection headings, readable body text, smaller navigation and supporting text, and bold numeric outputs. The article measure stops at (74ch). At (800px) and below, the lesson title becomes (30px) and section headings (23px); at (440px) and below, the title becomes (28px) and timing outputs (19px). These steps preserve the homepage scale above.

## Layout

The homepage header has a maximum width of (1440px), padding (24px 40px) and one horizontal navigation row beside the brand. The page body has a maximum width of (1120px) and (40px) gutters.

The first screen is capped at (760px) rather than stretching to the viewport, so the project introduction does not leave a large empty gap before the research content. The DexLab title, thesis, personal-project statement, method paragraph and a small scope note occupy the main column. The next section introduces the task-to-evidence architecture and displays the authored (1774×887) diagram across the reading column. After that system explanation, a concept field, a separate two-column research-topic index and one ruled index action form a compact transition into evidence browsing. Five evidence cases follow in one vertical reading sequence, then three numbered research judgments and three continuation links. The hardware-free validation boundary closes the main research path immediately before the contact footer: four evidence layers establish the proof model, and six experiment-specific records use open rows for physical guarantee, regression after parameter change and claim boundary.

The concept band contains only physical concepts, validation terms and canonical solver or numerical options. Cross-experiment research articles sit immediately below it in a separate, headed article index. Group membership remains metadata for the atlas, where explicit filters still organize the searchable map. Solver concepts are identified by token rather than `engine + token`; engine registrations remain separate context. Individual visible terms accept pointer hover: the field temporarily sharpens, other terms recede and the active term enlarges. A concept click and the masthead’s “Concepts” link open the atlas; each topic link opens its article directly.

The representative-experiment section is one open, vertically ordered case sequence. Each case begins with its number, title and headline result, followed by synchronized media and a ledger for conclusion, control variable, native readback, criterion/result and scope. There is no selection control: scrolling is the only progression through the cases. Content remains visible without JavaScript, while progressive enhancement gives each case a short bounded reveal as it enters the viewport.

- At (1100px) and below, the masthead wraps navigation onto a second row; gutters become (32px), and each evidence case stacks media above its readback.
- At (800px) and below, the architecture introduction stacks and the evidence case header meters wrap beneath the case title.
- At (800px) and below, the research-topic index uses two columns and its heading stacks. At (700px) and below, gutters become (22px), navigation labels are (13px), topic links use one column, and the scroll cue moves into normal flow. The architecture image keeps an (820px) reading width inside a keyboard-focusable horizontal scroll region.

Homepage section rhythm uses (72–84px) vertical padding on desktop and (56–60px) on narrow screens. The concept-to-topic transition uses a (22px) rule gap; the ruled experiment entrance follows the topic grid after (36px).

The research guide uses a fixed (190px) reading rail with six labeled groups and the same six-entry guide map below the opening statistics. The map is an open two-column set of ruled rows, not cards. Core evidence items use a two-column grid; the six problem layers use two columns; the three starting experiments use three equal open columns. Long prose remains at its (740px) reading measure, while grouped evidence can use (900px).

- At (1000px) and below, the guide rail becomes a static three-column group map above the article, and the main column centers at (900px).
- At (760px) and below, the guide map, evidence grids, layer grid and experiment routes stack to one column.
- At (600px) and below, the internal reading rail becomes a native “阅读目录” disclosure; its expanded groups use two columns and the article keeps a (22px) gutter. The separate guide map below the hero remains visible.

The shared Sphinx reader centers a (760px) article with an optional (160px) current-page outline, inside a (1040px) maximum grid. It does not render a second full-site toctree. Pages without a useful outline collapse to an (840px) centered column. The Blog uses an (880px) centered index with no section rail. At (1200px) and below, the outline disappears and the article centers; at (800px) and below, the grid becomes a single flow with the shared page gutters.

Comparative experiment pages may widen the article to (960px) through their own content components. A comparison summary uses a two-column open rule between the claim and its criteria/scope. A three-column GIF guide names pane order, what to watch and what the image cannot establish. Result matrices keep (760px) minimum width in their own horizontal scroll region and mark pass, failure, partial result and invalid evidence with text plus color, never color alone.

Anchor scroll padding is (32px). Print removes navigation and footer chrome, exposes all topic panels, and avoids splitting the principal content grids.

### MuJoCo learning layout

The learning masthead is in normal flow, (80px) tall with (40px) horizontal padding and a maximum width of (1600px). The centered course grid has columns (240px / minmax(0, 760px) / 160px), a (40px) gap, maximum width (1440px) and padding (36px 40px 72px). Chapter and section rails stick (28px) below the viewport top; the central article remains the reading focus.

- At (1200px) and below, the section rail disappears and the grid uses a (220px) chapter rail, flexible article, (32px) gap and maximum width (1120px).
- At (800px) and below, the article stacks under a native chapter disclosure, with page padding (20px 22px 48px). JavaScript initially collapses the chapter disclosure; without it, the links remain visible. Chapter links use two columns, becoming one at (440px). The masthead wraps, and its tools take a separate row at the narrow breakpoint.
- The teaching example uses two numeric result columns. Print removes reading navigation and bookmark controls and lets the article fill the page. Learning anchor scroll padding is (100px), becoming (24px) on mobile.

## Elevation & Depth

There are no shadows, gradients or decorative transitions. Thin rules, whitespace and typography separate content; the homepage remains entirely on the paper surface, while learning uses paper wash for the teaching and reading states described above. Hover changes are immediate. Keyboard focus uses a green outline (2px) with an offset (4px).

**The Flat Reading Rule.** Use spacing, type and fine rules to separate content without enclosing it in raised panels.

## Motion

**Motion thesis:** the concept field forms the atmospheric entry and the evidence cases form the sequential reading cadence. Both use bounded, progressively enhanced scroll reactions; the page-progress hairline is supporting orientation, and media plays only after an explicit control action.

There is no page-load choreography. The concept field uses a short, bounded vertical response and a small contrast increase as it enters view; every term is readable at rest. Pointer entry into one concept sharpens the field, reduces unrelated terms to a still-readable secondary contrast and enlarges the active word by roughly 1.5× with a short exponential ease-out. A click opens the atlas and focuses the matching entry. Evidence panels enter in source order with a restrained rise and contrast transition, and remain fully visible if JavaScript fails.

With `prefers-reduced-motion: reduce`, the concept field and evidence sequence are fully visible without scroll-linked movement, hover scaling is removed, and the hover/click contrast feedback remains. Media remains user-controlled.

## Shapes

The homepage defines no component radius scale. Its directory entrance, evidence case headers and continuation rows remain unfilled and rule-separated. Learning numbers are plain serif numerals. Chapter and engine links wrap within similarly open ruled groups.

The course reader's `learning-control` radius belongs only to its outlined buttons and chapter links. The teaching panel remains rectangular; native ranges, radios, progress and disclosures keep their browser affordances. The filled read button is an explicit reading state, not a homepage action style.

## Components

### Research entrance and navigation

The first screen shows the project title, a two-line research thesis, a clear personal-project statement, a shorter method paragraph, a scope paragraph, a search field and one primary content action. The personal-project statement uses the serif voice at a smaller display scale and names DexLab as the author's own research project before the method description. The scope paragraph states explicitly that every current experiment is simulation-only and that physical correctness is bounded by the frozen model. The search field is a native GET form to the site search page, with an inline icon, accessible label and 44px action target. Focusing an empty field reveals six ruled suggested searches with a short category label; choosing one starts the live search. It lazily loads the generated Sphinx index on first use and displays a debounced, six-item live result list beneath the field; the typed terms are marked in result titles and excerpts, and submitting still opens the complete search page. The directory entrance is a full-width open row bounded by fine rules, with a (20px) action label, a (14px) explanatory line and a (22px) inline arrow. A downward line and label indicate that more content follows. The entrance turns green on hover and focus without becoming a filled button.

Navigation is one horizontal masthead row on desktop and wraps below the brand on smaller screens. The guide destination is green and semibold; other destinations are muted. Hover adds an underline and charcoal text. Language and repository links stay beside the masthead. A skip link becomes visible on focus; all links and buttons retain keyboard focus.

### Concept field and atlas

The concept field is a dedicated band below the opening index action, not a card grid and not a backdrop behind the hero. All concept categories share one continuous, centered flex-wrapped surface: normalized positions within each group determine a deterministic cross-group interleave, so the solver vocabulary does not collapse into a separate bottom block. Group order remains stable inside each source category and is exposed explicitly in the atlas. Label length and the core/advanced distinction set the typographic tier, letting short concepts anchor the wall while long solver or numerical tokens remain legible at a smaller scale; size does not encode popularity or importance. A token such as FP64, Euler or Newton is one concept even when several engines register it; engine names appear only in a separated context list. Every term is readable at rest and remains visible when another term is hovered. Hovering enlarges the active word; unrelated terms fall only to a secondary reading contrast. The masthead “Concepts” link remains the accessible non-hover path.

The research-topic index follows the concept field as a separate section. A serif heading and short explanatory line introduce equal article links in a two-column open grid. A ruled filter row classifies articles as `Sim-to-Real`, `Physics & Contact`, `Solvers & Runtime` or `Skills & Evaluation`; every article has exactly one taxonomy topic, while the default `All` view remains globally sorted by `updated` date, newest first. Each row repeats its topic label beside the visible update date, uses a compact serif article title that always wraps in full, one supporting summary and a green reading action; there are no cards, shadows or enlarged blocks inside the cloud. The grid becomes one column below (700px).

The atlas uses a native full-viewport `dialog`. Search, group filters, the six concept clusters, the research-synthesis group, and a single reading lens share one ruled reading surface. At rest the clusters show words only; hovering or focusing a term highlights direct relations and contrasts and draws only that local set of edges. The lens states the selected item, its one-sentence definition, a direct link to the concept entry or synthesis article, and related terms without moving the reader’s place in the map.

On desktop the map occupies the wide column and the lens stays in a narrow side column. Below (800px), the map and lens stack, controls become a single column, relation highlighting remains available to pointer and keyboard users, and every term retains a large-enough hit target. Closing returns focus to the trigger. Without JavaScript, the trigger opens the generated concept index, where every term and relationship remains a normal link.

Each generated concept page is a one-screen reading entry: term and aliases, concise definition, one concrete distinction grounded in DexLab evidence, likely confusion, relation links, sources, and a return to the atlas. Longer experiments and papers remain linked rather than duplicated.

### Architecture view

The architecture section follows the first screen and explains the system before the evidence inspector. A serif heading and short scope paragraph introduce the official diagram; the (1774×887) diagram spans the reading column between fine rules without cropping, recoloring or overlaying explanatory chrome. The homepage uses a (199 KB) WebP rendition and falls back to the (2.1 MB) authored PNG; both preserve the source dimensions. Its authored blue, green, peach and dark diagram colors are treated as source-evidence colors, not as a second interface palette.

The image itself opens the original asset. On narrow screens, the figure becomes a keyboard-focusable horizontal scroll region with an (820px) image width so labels remain legible; a visible “scroll horizontally” hint appears above it, and the caption also provides an explicit original-image link. This is the only nested scroll surface on the homepage.

### Physical validation boundary

The validation section is the final research section before the contact footer. It starts with an explicit “hardware experiments: 0” statement and separates simulation-internal consistency from real-world accuracy. A ruled boundary row links the prepared hardware-collection protocol while stating that no acceptable hardware dataset exists.

Four evidence layers use the same open three-rule grammar as the conclusions: frozen input identity, positive and negative controls, native numerical readback, and parameter-change regression. Six experiment records follow as open ruled rows. Each names the experiment, its physical guarantee, the exact regression design after a parameter change, and what the result cannot prove. Results include both passes and retained failures, including the MuJoCo apple timestep case that is expected to fail.

At (1100px) and below the evidence layers use two columns. At (800px) and below the validation boundary and experiment records become one column, with guarantee, regression and boundary stacked in reading order.

### Evidence inspector

The representative-experiment section lists five cases in editorial order. Every case remains in the page and contains its recorded GIF or paired GIFs, a conclusion, and a four-row ledger for control variable, native readback, criterion/result and scope. Links open the complete experiment record rather than expanding an unbounded transcript on the homepage.

Scrolling carries the reader from one case to the next; there is no radio or tab selection. Each case occupies an open ruled row with its own header and stacks on narrow screens. With motion enabled, panels begin slightly low and translucent and settle as they intersect the viewport; without JavaScript or with reduced motion, all five remain fully visible. Print shows the same five-panel sequence without transitions. Every result keeps its governing condition and evidence boundary beside the media.

### Research-guide lanes

The research guide uses two foundation lanes and four semantic topics rather than a single numbered sequence: 核心导读, 证据索引, 任务与执行, 物理与感知, 数据与技能, 评测与收益. A two-column open guide map repeats these groups below the opening counts. The desktop rail uses the same group labels, and the current destination receives `aria-current="location"` without moving content.

Core reading keeps a (740px) prose measure but allows equivalent evidence groups to share a (900px) editorial field. The six-layer problem model uses two columns; seven key paper trade-offs use two columns with the odd final item spanning both; the three proposed experiments use three open columns. Borders stay above or below groups rather than enclosing cards. Appendices use `TOPIC / ...` or `SYSTEM / ...` labels, and a month is retained only as supporting publication metadata rather than a top-level category.

### Blog index and reading rows

The Chinese Blog is a first-class reader page and the canonical complete content index. A short jump row links to five sections: research guide, contact and physics, failure and diagnosis, policy/skills/evaluation, and simulation learning. All headings, article rows and course links remain visible without tabs or hidden panels. The policy section divides into four two-column subtopics. The page omits the right-hand outline rail and uses a wider reading column so the grouped index is visible at once.

Legacy `#blog` links resolve to `blog.html`; the English Blog entry points to the same canonical Chinese index.

### Learning and knowledge bridges

The simulation-learning page uses four steps in two columns on desktop and a single column on mobile. Each has a plain green serif number, a content inset of (38px), a heading, subjects, prerequisite and course link. Engine choices sit between fine rules; related concepts link across to experiments. Course and engine links open the on-site `learn/` reader. The authored courses remain maintained by Sim Learning.

### MuJoCo learning controls

Six ordered chapter links retain `aria-current`, with a paper-wash current row and explicit read labels. Previous/next links and the deeper-course links remain ordinary navigation. The optional section rail follows the lesson headings. A skip link, visible focus and native mobile disclosure keep the reader keyboard accessible.

Readers mark or unmark lessons explicitly. A thin native progress bar counts read lessons; browser-local storage also supplies a last-lesson link. Neither page visits nor quiz results mark a lesson read. Storage failure produces a readable status message. The bookmark counts reading, not competence; both languages share the same lesson identifiers.

Native explanations can be expanded together. Self-checks use labeled radios, a fieldset and textual status feedback, with explanations available without JavaScript. The timing example uses native ranges, numeric outputs and an SVG timeline to connect physics-step duration to control-update period. It depicts simulated time, not wall-clock speed or measured engine behavior. Script-only controls are revealed after initialization; lesson text, disclosures and navigation remain usable without JavaScript.

### Unified content reader

Reports, experiment pages, project documentation and generated course pages share one responsive shell. The global masthead is the only site-level navigation. Long documents may add a single right-hand current-page outline; Blog and short pages omit it. There is no second left rail containing the full Sphinx tree. This reduces navigation from “global category → all-site tree → current page” to “global category → current page”.

Sphinx-specific content keeps its native semantics: local toctrees become open ruled reading lists, tables scroll within the article, code blocks use the paper wash, admonitions use top and bottom rules, and GIF/experiment components retain their static data disclosures. No report introduces rounded promotional cards, shadows, gradients or a separate palette.

### Engine comparison experiment

Each experiment leads with a plain conclusion, then separates criteria from scope. The synchronized recorder follows with an annotation strip that names the pane order, what the visual evidence can show, and the numerical decision the video cannot make. Pane labels use the recorded series names above the media; playback remains muted and manually started.

A compact evidence matrix follows the replay. Rows identify the tested configuration; columns separate conditions or metrics and end with a total where meaningful. Results are expressed as counts and text labels—not isolated percentages—so an invalid record remains visible in the denominator. Every matrix includes a legend and a direct statement that fixed configurations do not become a cross-engine ranking.

Supporting conditions, source links and limitations remain below the matrix. Detailed curves, native state and raw data remain available in the existing replay panel and fallback disclosure.

## Do's and Don'ts

### Do:

- **Do** keep the homepage aligned with the article's warm paper, serif opening title and green links.
- **Do** let spacing, hierarchy and open rows explain the page before adding secondary labels.
- **Do** keep the concept field below the opening index action so it no longer competes with or obscures the hero copy.
- **Do** present the architecture diagram uncropped with its authored colors and a direct path to the original PNG.
- **Do** use the concept-field reveal as the authored scroll response, keep the page-progress hairline supporting, and preserve complete content without JavaScript or with reduced motion.
- **Do** keep individual concepts in one continuous cloud, resolve it gradually as it enters view, and preserve category filters in the complete atlas plus a visible non-JavaScript path to the index.
- **Do** keep cross-experiment article titles in a separate research-topic index with compact open rows and complete bilingual links.
- **Do** make one hovered concept clear and larger while the rest of the field recedes, and open the matching atlas entry on click.
- **Do** draw only the selected concept’s local relationships; keep the atlas readable before adding any connection lines.
- **Do** keep every experiment case visible without JavaScript and reveal the vertical evidence sequence through scroll rather than click-based selection.
- **Do** close the homepage research path with the physical-validation boundary after experiments, findings and continuation links.
- **Do** classify the long research guide by reading intent and keep equivalent evidence groups in responsive open columns.
- **Do** keep one global site navigation and at most one current-page outline in the shared reader.
- **Do** put an experiment's conclusion, criteria, synchronized comparison and result matrix before its long protocol.
- **Do** preserve visible keyboard focus and complete GIF, figure and disclosure access without JavaScript.
- **Do** maintain Chinese/English parity, on-site learning links and original evidence provenance.
- **Do** preserve explicit reading bookmarks and distinguish teaching calculations, sourced MuJoCo 4 changes and native measurements; retain the detailed courses' pinned baseline.
- **Do** send every ordinary content page through the shared reader template so navigation, type, spacing and responsive behavior stay identical across the Blog.

### Don't:

- **Don't** restore the homepage's old blue-white centered hero, filled action buttons or rounded promotional panels.
- **Don't** reintroduce the old wide Sphinx report shell or restore per-page report palettes; the separate browser application remains outside this reading system.
- **Don't** crop the architecture diagram or shrink it below readable label size on mobile.
- **Don't** replace recorded evidence with generated imagery, autoplay the replay or imply an autonomous result.
- **Don't** turn the evidence index into repeated fade-and-rise cards, parallax layers or a sequence of equal-height panels.
- **Don't** hide content before an IntersectionObserver reveal, blur or fade whole experiment groups on load.
- **Don't** animate every concept independently or use resting font size to imply unsupported popularity.
- **Don't** present a complete relation graph at rest or use cards and shadows for the concept atlas.
- **Don't** append newly added systems or observations as more chapter numbers in the original guide sequence.
- **Don't** restore the full-site Sphinx tree as a second left sidebar on article pages.
- **Don't** present an engine table as a universal ranking when cohorts, tuning budgets or invalid records differ.
- **Don't** invent component variants, radius scales or motion tokens absent from the implementation.
