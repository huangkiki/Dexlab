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
  learning-number:
    textColor: '{colors.accent}'
    typography: '{typography.step-number}'
  evidence-video:
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

The homepage shares the existing dexterous-simulation guide's warm paper, charcoal text, muted green links and serif opening title. It is an editorial research entrance: the first screen establishes the project and primary index action; scrolling reveals the authored architecture diagram, a four-stage research trace and five pre-expanded topic groups. Fine rules and open rows carry the hierarchy.

This system governs the Chinese and English research homepages, the MuJoCo learning route and every Sphinx content page. Ordinary articles use the unified reader in `_templates/reader-page.html`: the learning route's slim masthead, chapter rail, 760px reading column and section rail now frame reports, documentation and course pages as well. The canonical Blog page owns the pre-expanded category index. The existing article remains the visual reference; report content and scientific scope stay independently maintained. The separate browser application retains its own design system.

**Key Characteristics:**

- Warm paper and charcoal, with restrained green reading accents.
- A horizontal masthead, oversized serif opening title and one ruled content entrance.
- The original architecture diagram followed by a scroll-linked research trace and asymmetric topic rows.
- Original experiment media, native controls and explicit evidence boundaries.
- A MuJoCo learning column with chapter navigation, explicit reading bookmarks and small teaching interactions.

Source of truth: `_static/research-home.css`, `_templates/research-home.html`, `_static/research-home.js`, and `zh/index.md` / `en/index.md`. The Blog index uses `zh/blog.md` and `_static/blog-index.css` inside the shared reader. The reference is `_static/research/dexterous-simulation.html`; the homepage composition is recorded in the root `.impeccable/surfaces/research-home.md`. Frontmatter contains implemented tokens. The sidecar adds component previews and responsive metadata; its tonal ramps are preview aids, not production colors.

The learning surface uses `_static/simulation-learning.css`, `_templates/simulation-learning.html`, `_static/simulation-learning.js`, and both languages' `learning.md` / `mujoco-learning/` lessons. Its route contract is in the root `.impeccable/surfaces/mujoco-learning.md`. The shared reader uses `_static/reader-page.css`, `_templates/reader-page.html` and `_static/reader-page.js`; it imports the learning styles and the existing evidence-component styles before applying report-specific layout overrides.

## Colors

One restrained green accent sits among warm, low-chroma neutrals shared with the article.

### Primary

- **Reading Green** (`accent`): links, the first navigation destination, selected topic controls, learning numbers and the improvement branch in the research loop.

### Neutral

- **Warm Paper** (`page`): the page canvas and text on the focused skip link.
- **Paper Wash** (`panel`): the native video's backdrop.
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

The first screen is at least the viewport height minus the masthead. The DexLab title, thesis, lead and one ruled index action occupy the main column; a small scroll cue anchors at the lower right. The next section introduces the task-to-evidence architecture and displays the authored (1774×887) diagram across the reading column. The research trace then uses a sticky left statement and a four-stage right column. The topic map uses one ruled row per theme: an editorial heading on the left and direct article links in two columns on the right. A final ruled action opens the exhaustive Blog index.

- At (1100px) and below, the masthead wraps navigation onto a second row; gutters become (32px), and the trace and topic columns use tighter gaps.
- At (800px) and below, the architecture introduction, trace and topic rows stack into one column; the left statement stops being sticky.
- At (700px) and below, gutters become (22px), navigation labels are (13px), topic links use one column, and the scroll cue moves into normal flow. The architecture image keeps an (820px) reading width inside a keyboard-focusable horizontal scroll region.

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

**Motion thesis:** one scroll relationship explains how a failed task becomes a checked finding. The vertical trace and reached node are the focal sequence; the page-progress hairline provides quiet orientation. Article rows do not receive repeated entrance animations.

The trace uses a transform-only draw at roughly a (120ms) linear response cadence to follow scroll, while stage contrast and the node fill settle over (220–320ms) with `cubic-bezier(.16, 1, .3, 1)`. The sticky current-stage label changes as the line reaches a stage. There is no autoplay loop, parallax or unrelated hover motion.

With `prefers-reduced-motion: reduce`, the trace is complete from the start, all stages retain their active-level contrast, and no draw transition runs. Scroll remains the only way the sequence advances.

## Shapes

The homepage defines no component radius scale. Its directory entrance and topic rows remain unfilled; the research-trace nodes are (13px) editorial circles, not controls. Learning numbers are plain serif numerals. Chapter and engine links wrap within similarly open ruled groups.

The course reader's `learning-control` radius belongs only to its outlined buttons and chapter links. The teaching panel remains rectangular; native ranges, radios, progress and disclosures keep their browser affordances. The filled read button is an explicit reading state, not a homepage action style.

## Components

### Research entrance and navigation

The first screen shows the project title, a two-line research thesis, a scope paragraph and one primary content action. The directory entrance is a full-width open row bounded by fine rules, with a (20px) action label, a (14px) explanatory line and a (22px) inline arrow. A downward line and label indicate that more content follows. The entrance turns green on hover and focus without becoming a filled button.

Navigation is one horizontal masthead row on desktop and wraps below the brand on smaller screens. The guide destination is green and semibold; other destinations are muted. Hover adds an underline and charcoal text. Language and repository links stay beside the masthead. A skip link becomes visible on focus; all links and buttons retain keyboard focus.

### Architecture view

The architecture section follows the first screen and explains the system before the research trace. A serif heading and short scope paragraph introduce the official diagram; the (1774×887) diagram spans the reading column between fine rules without cropping, recoloring or overlaying explanatory chrome. The homepage uses a (199 KB) WebP rendition and falls back to the (2.1 MB) authored PNG; both preserve the source dimensions. Its authored blue, green, peach and dark diagram colors are treated as source-evidence colors, not as a second interface palette.

The image itself opens the original asset. On narrow screens, the figure becomes a keyboard-focusable horizontal scroll region with an (820px) image width so labels remain legible; a visible “scroll horizontally” hint appears above it, and the caption also provides an explicit original-image link. This is the only nested scroll surface on the homepage.

### Scroll-linked research trace

The trace is the page's single authored motion moment. A fine vertical rule marks the complete path; a green line draws over it as the stage advances. Four open stages describe task failure, first failing layer, the skill/simulation fork and independent retest. The reached marker and active heading turn Reading Green, while the sticky summary names the current stage. Every stage keeps full readable contrast rather than being hidden or faded below body-text contrast.

A hairline page-progress rule stays at the top as supporting orientation. The enhancement is driven by passive scroll updates with `requestAnimationFrame`; without JavaScript the complete trace and all stages remain visible. Under reduced motion the trace is shown complete, no draw transition runs, and the current-stage state remains textual.

### Topic map

Five ruled topic rows put the category name and question on the left and direct article titles on the right. Research guide, contact/physics, failure/diagnosis, policy/skills/evaluation and simulation learning use the same row grammar but keep their own emphasis: the first row leads with the full guide title and chapter anchors; policy includes the skill-memory link; learning leads with the on-site route. No row hides its contents behind a tab, accordion or category page.

A final open band names the exhaustive catalogue and opens the canonical Blog. Its serif statement and arrow are larger than ordinary link rows, making it the only closing call to action.

### Blog index and reading rows

The Chinese Blog is a first-class reader page and the canonical complete content index. A short jump row links to five sections: research guide, contact and physics, failure and diagnosis, policy/skills/evaluation, and simulation learning. All headings, article rows and course links remain visible without tabs or hidden panels. The policy section divides into four two-column subtopics. The page omits the right-hand outline rail and uses a wider reading column so the grouped index is visible at once.

The homepage opens this index from both the first-screen action and the closing catalogue band. Legacy `#blog` links resolve to `blog.html`; the English Blog entry points to the same canonical Chinese index.

### Learning and knowledge bridges

The simulation-learning page uses four steps in two columns on desktop and a single column on mobile. Each has a plain green serif number, a content inset of (38px), a heading, subjects, prerequisite and course link. Engine choices sit between fine rules; related concepts link across to experiments. Course and engine links open the on-site `learn/` reader. The authored courses remain maintained by Sim Learning.

### MuJoCo learning controls

Six ordered chapter links retain `aria-current`, with a paper-wash current row and explicit read labels. Previous/next links and the deeper-course links remain ordinary navigation. The optional section rail follows the lesson headings. A skip link, visible focus and native mobile disclosure keep the reader keyboard accessible.

Readers mark or unmark lessons explicitly. A thin native progress bar counts read lessons; browser-local storage also supplies a last-lesson link. Neither page visits nor quiz results mark a lesson read. Storage failure produces a readable status message. The bookmark counts reading, not competence; both languages share the same lesson identifiers.

Native explanations can be expanded together. Self-checks use labeled radios, a fieldset and textual status feedback, with explanations available without JavaScript. The timing example uses native ranges, numeric outputs and an SVG timeline to connect physics-step duration to control-update period. It depicts simulated time, not wall-clock speed or measured engine behavior. Script-only controls are revealed after initialization; lesson text, disclosures and navigation remain usable without JavaScript.

### Unified content reader

Reports, experiment pages, project documentation and generated course pages share one responsive shell. The desktop page header, brand, navigation spacing, chapter rail, article heading, body measure, right section rail and footer match the learning route. The left rail contains the generated Sphinx document tree rather than a second hand-maintained list. The current document uses the same paper-wash selected state as a current lesson.

Sphinx-specific content keeps its native semantics: local toctrees become open ruled reading lists, tables scroll within the article, code blocks use the paper wash, admonitions use top and bottom rules, and existing video/replay/experiment components retain their controls and scripts. No report introduces rounded promotional cards, shadows, gradients or a separate palette.

## Do's and Don'ts

### Do:

- **Do** keep the homepage aligned with the article's warm paper, serif opening title and green links.
- **Do** let spacing, hierarchy and open rows explain the page before adding secondary labels.
- **Do** present the architecture diagram uncropped with its authored colors and a direct path to the original PNG.
- **Do** use scroll motion only for the research trace and preserve complete content without JavaScript or with reduced motion.
- **Do** preserve visible keyboard focus, native video and disclosure controls, and complete reading access without JavaScript.
- **Do** maintain Chinese/English parity, on-site learning links and original evidence provenance.
- **Do** preserve explicit reading bookmarks and distinguish teaching calculations, sourced MuJoCo 4 changes and native measurements; retain the detailed courses' pinned baseline.
- **Do** send every ordinary content page through the shared reader template so navigation, type, spacing and responsive behavior stay identical across the Blog.

### Don't:

- **Don't** restore the homepage's old blue-white centered hero, filled action buttons or rounded promotional panels.
- **Don't** reintroduce the old wide Sphinx report shell or restore per-page report palettes; the separate browser application remains outside this reading system.
- **Don't** crop the architecture diagram or shrink it below readable label size on mobile.
- **Don't** replace recorded evidence with generated imagery, autoplay the replay or imply an autonomous result.
- **Don't** turn the topic map into repeated fade-and-rise cards, parallax layers or a sequence of equal-height panels.
- **Don't** invent component variants, radius scales or motion tokens absent from the implementation.
