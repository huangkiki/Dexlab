---
name: DexLab Research Homepage
description: A warm-paper reading index shaped by the existing dexterous-simulation guide.
colors:
  accent: '#4f664c'
  page: '#fafaf6'
  panel: '#f0f1eb'
  ink: '#282b26'
  muted: '#60675a'
  rule: '#dcded4'
typography:
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
---

# Design System: DexLab Research Homepage

## Overview

**Creative North Star: "The Research Reading Index"**

The homepage shares the existing dexterous-simulation guide's warm paper, charcoal text, muted green links and serif opening title. A quiet reading rail, comfortable line lengths and fine rules establish hierarchy. Open rows and restrained labels keep attention on the research and its evidence.

This system governs only the Chinese and English research homepages. The existing article is the visual reference; its content and styles remain independently maintained. Other Sphinx pages and the separate web application retain their own design systems.

**Key Characteristics:**

- Warm paper and charcoal, with restrained green reading accents.
- A serif opening title beside a desktop reading rail; navigation wraps above the title on smaller screens.
- Open sections and ruled reading rows, with hierarchy carried by spacing and type.
- Original experiment media, native controls and explicit evidence boundaries.

Source of truth: `_static/research-home.css`, `_templates/research-home.html`, `_static/research-home.js`, and `zh/index.md` / `en/index.md`. The reference is `_static/research/dexterous-simulation.html`; the homepage composition is recorded in the root `.impeccable/surfaces/research-home.md`. Frontmatter contains implemented tokens. The sidecar adds component previews and responsive metadata; its tonal ramps are preview aids, not production colors.

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

**The Evidence Color Rule.** Interface color organizes reading; recorded experiment colors retain their original meaning.

## Typography

The opening title and masthead use the serif stack; the body, section headings and controls use the sans-serif stack. Both use installed system fallbacks without an external font request. The opening title is regular weight; section headings are semibold, while topic headings inherit the browser's bold heading weight. Learning numbers return to the serif face.

Use display for the full linked guide title, headline for major sections, title for research questions, body for reading text, label for navigation and caption for the replay explanation. The lead is larger (18px) and limited to (700px); supporting introductions and evidence-boundary prose use a measure of up to (740px). Research-direction headings use (23px), case headings (20px), and learning headings (18px).

At the intermediate breakpoint, the opening title becomes (46px). On mobile it uses `clamp(28px, 8.7vw, 34px)` with line height (1.48); the lead and guide link become (16px), section headings (24px), and the research-direction heading (21px). English removes its explicit title line breaks on mobile; Chinese retains them. Let the languages wrap naturally rather than forcing matching line counts.

## Layout

The desktop header has a maximum width of (1440px) and padding of (24px 40px). Navigation forms a fixed left rail at (160px) from the top, with width (190px), left inset `max(40px, calc((100vw - 1440px) / 2 + 40px))`, and an inner inset of (18px). The masthead itself is in normal document flow.

The reading column uses width `calc(100% - 310px)`, maximum width (1100px), left margin `max(270px, calc((100vw - 1440px) / 2 + 270px))`, and padding (24px 40px 0). The opening and research-direction sections stop at (840px). The opening title is left aligned; a prominent text link and three chapter links make the guide the first reading entry. Research direction, recorded findings, question-led reading and learning follow. This composition belongs to this homepage, not every article.

Evidence uses equal columns with a (28px) gap; question and reading columns use (0.8fr / 1.2fr) with a (36px) gap. Learning uses two columns with a (32px) gap. Main reading sections have a top rule and padding (32px 0 56px).

- At (1100px) and below, the rail becomes a static, wrapping row below the masthead, bounded by horizontal rules. The main column centers at a maximum width of (940px), with (32px) gutters and (20px) top padding. The header uses (22px 32px 0) padding.
- At (700px) and below, gutters become (22px) and main top padding becomes (12px). Navigation labels are (13px) with a minimum height of (32px). Evidence, topic content and learning stack into one column. Learning gaps become (26px); major sections use padding (28px 0 36px). Engine links move below their label, and concept/experiment bridges use a three-column row.

Anchor scroll padding is (32px). Print removes navigation and footer chrome, exposes all topic panels, and avoids splitting the principal content grids.

## Elevation & Depth

There are no shadows, gradients or decorative transitions. Thin rules, whitespace and typography separate content; the paper wash is confined to the replay backdrop. Hover changes are immediate. Keyboard focus uses a green outline (2px) with an offset (4px).

**The Flat Reading Rule.** Use spacing, type and fine rules to separate content without enclosing it in raised panels.

## Shapes

The homepage defines no rounded-corner scale. Reading actions and topic buttons remain unfilled, the video is rectangular, and learning numbers are plain serif numerals. Topic selection uses a bottom stroke (2px). Reading entries are open rows with single-pixel rules; chapter and engine links wrap within similarly open ruled groups.

## Components

### Guide entry and navigation

The full guide title links directly to the article in charcoal and turns green on hover. The separate guide link is underlined green text with an inline arrow (22px), a gap of (12px) and a minimum height of (44px). Ordinary links turn charcoal on hover. Chapter links wrap beneath a fine rule and retain a minimum height of (36px). The English homepage identifies the guide's language.

Navigation is a reading rail on desktop and a wrapping row at the intermediate breakpoint. The guide destination is green and semibold; other destinations are muted. Hover adds an underline and charcoal text. Language and repository links stay beside the masthead. A skip link becomes visible on focus; all links, buttons and summaries retain keyboard focus.

### Research loop

The task–diagnose–improve–retest sequence is an unboxed, wrapping text row (14px). The improvement branch is green; arrows and the next-question return are muted. On mobile the return occupies a new row. This describes a research direction, with the existing note preserving the boundary around an unverified autonomous loop.

### Recorded comparison and evidence disclosure

Use the original comparison MP4 in a native video with controls, inline playback and `preload="none"`; do not autoplay. The HTML declares dimensions (896px × 504px), and CSS scales it to its column. Retain the existing provenance-bearing PNG poster and the caption identifying the two conditions and original playback speed. Place the finding, evidence, takeaway and scope beside the video, stacking beneath it on mobile.

A native details/summary disclosure follows under a top rule. Its text is muted (14px), its summary is charcoal, and its expanded paragraphs retain the evidence limits. Keep it a native disclosure rather than a custom animated accordion.

### Topic controls and reading rows

Three transparent buttons use muted text (15px), padding (12px 0), and a green label and bottom stroke when selected. They become (13px) on mobile. Preserve `aria-pressed` and `aria-controls`; the implementation uses buttons, not tab-widget semantics. JavaScript reveals the controls and selects one panel; without it, all three panels remain readable.

Each panel pairs a research question with an open reading list. Links use regular charcoal text (15px), padding (18px 0), and green underlined hover. The current rows contain titles without secondary descriptors.

### Learning and knowledge bridges

Four steps form two columns on desktop and a single column on mobile. Each has a plain green serif number, a content inset of (38px), a heading, subjects, prerequisite and course link. Engine choices sit between fine rules; related concepts link across to experiments. Course and engine links open the on-site `learn/` reader. The authored courses remain maintained by Sim Learning; the English homepage retains its language note.

## Do's and Don'ts

### Do:

- **Do** keep the homepage aligned with the article's warm paper, serif opening title and green links.
- **Do** let spacing, hierarchy and open rows explain the page before adding secondary labels.
- **Do** preserve visible keyboard focus, native video and disclosure controls, and complete reading access without JavaScript.
- **Do** maintain Chinese/English parity, on-site learning links and original evidence provenance.

### Don't:

- **Don't** restore the old blue-white centered hero, filled action buttons or rounded promotional panels.
- **Don't** restyle the article, other Sphinx pages or the separate web application through this homepage system.
- **Don't** replace recorded evidence with generated imagery, autoplay the replay or imply an autonomous result.
- **Don't** invent component variants, radius scales or motion tokens absent from the implementation.
