---
name: DexLab Research Homepage
description: A clear white-and-blue reading index for reciprocal agent and simulation research.
colors:
  accent: '#2358c4'
  accent-hover: '#173d8e'
  accent-soft: '#edf3ff'
  page: '#fff'
  panel: '#f5f6f8'
  ink: '#202634'
  muted: '#596171'
  rule: '#dce1e9'
typography:
  display:
    fontFamily: Inter, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 54px
    fontWeight: 750
    lineHeight: 1.23
    letterSpacing: -.035em
  headline:
    fontFamily: Inter, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 32px
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: -.025em
  title:
    fontFamily: Inter, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 25px
    lineHeight: 1.3
    letterSpacing: -.02em
  body:
    fontFamily: Inter, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 16px
    lineHeight: 1.75
  label:
    fontFamily: Inter, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 14px
    fontWeight: 550
  caption:
    fontFamily: Inter, "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif
    fontSize: 13px
    lineHeight: 1.7
rounded:
  action: 8px
  media-panel: 12px
  loop: 14px
  step: 50%
spacing:
  compact: 12px
  text: 16px
  control: 20px
  panel: 24px
  gutter: 28px
  group: 30px
  column: 36px
  section: 64px
  section-end: 76px
components:
  button-primary:
    backgroundColor: '{colors.accent}'
    textColor: '{colors.page}'
    rounded: '{rounded.action}'
    padding: 12px 22px
  button-primary-hover:
    backgroundColor: '{colors.accent-hover}'
    textColor: '{colors.page}'
  text-link:
    textColor: '{colors.accent}'
  navigation-link:
    textColor: '{colors.muted}'
    typography: '{typography.label}'
    padding: 7px 0
  topic-button:
    backgroundColor: transparent
    textColor: '{colors.muted}'
    rounded: '0'
    padding: 14px 0
  topic-button-selected:
    textColor: '{colors.accent}'
  research-loop:
    backgroundColor: '{colors.panel}'
    textColor: '{colors.ink}'
    rounded: '{rounded.loop}'
    padding: 22px 24px
  reading-link:
    textColor: '{colors.ink}'
    padding: 19px 2px
  learning-step:
    backgroundColor: '{colors.accent-soft}'
    textColor: '{colors.accent}'
    rounded: '{rounded.step}'
    width: 34px
    height: 34px
  evidence-boundary:
    textColor: '{colors.muted}'
    padding: 16px 0
---

# Design System: DexLab Research Homepage

## Overview

**Creative North Star: "The Research Reading Index"**

A clean white-and-blue index, following the confirmed reference at rl-robotics.github.io. Generous space and clear type make research questions, evidence and next reading steps easy to find. The character is calm, direct and precise; the implementation is code-led, with no approved image comp or generated scientific imagery.

Scope is limited to the Chinese and English homepages rendered by the dedicated homepage template and stylesheet. This file does not govern other Sphinx pages, the long-form research article, or the separate web application. Keep their existing styles and web/DESIGN.md intact.

**Key Characteristics:**

- White reading canvas, restrained blue actions and pale neutral grouping.
- Clear hierarchy, open section spacing and thin rules instead of raised cards.
- The same visual grammar in Chinese and English, with room for different text lengths.
- Actual experiment media with native, reader-controlled playback.

Source of truth: `_static/research-home.css`, `_templates/research-home.html`, `_static/research-home.js`, and the matching `zh/index.md` / `en/index.md`. Frontmatter records implemented tokens; the sidecar adds preview snippets, responsive metadata and descriptive color ramps. Those ramps are preview aids, not additional production colors.

## Colors

The palette uses one clear blue accent against cool, quiet neutrals.

### Primary

- **Research Blue** (`accent`): primary actions, links, selected topics, step numbers and the improvement branch in the loop.
- **Deep Research Blue** (`accent-hover`): hovered primary actions and ordinary links.
- **Pale Research Blue** (`accent-soft`): the numbered learning markers.

### Neutral

- **White Canvas** (`page`): the reading surface and text on the primary action.
- **Cool Panel** (`panel`): the research loop, engine directory, replay backdrop and footer.
- **Graphite** (`ink`): headings, body text and reading-list titles.
- **Slate** (`muted`): supporting explanations, prerequisites, captions and resting navigation.
- **Quiet Rule** (`rule`): section boundaries, reading rows and learning connectors.

**The Evidence Color Rule.** Interface color organizes reading; recorded experiment colors retain their original meaning.

## Typography

Display and body share the frontmatter's sans-serif stack. Inter is requested first, followed by Chinese system fonts and a generic sans-serif fallback; the homepage template does not load an external font. The system must remain readable with those fallbacks.

Use the display role for the centered opening statement, headline for section headings, title for question introductions, body for prose, label for navigation and caption for media explanations. Supporting prose uses muted ink. Headlines are balanced; body text stays left aligned outside the hero. The hero lead is capped at (700px), and section introductions at (720px).

The desktop scale is normative in frontmatter. At the tablet breakpoint the hero becomes (46px); on mobile it becomes (34px) with line height (1.3), section headings become (27px), and topic titles become (23px). Do not force equal line counts across languages.

## Layout

The centered page and header use a maximum width of (1200px), with horizontal gutters from the gutter spacing token. The header is sticky; its desktop minimum height is (76px). The hero has an open top inset of (82px), centered copy and a compact research-loop panel. Below it, left-aligned evidence and reading sections use thin separators and substantial vertical spacing.

The evidence grid uses (1.1fr / 1fr); the question-and-reading layout uses (0.8fr / 1.2fr). The learning route is four columns. At (1000px) or below, the evidence columns become equal, the learning route becomes two columns, and engine links wrap beneath their label. At (650px) or below, the header navigation moves to a second row, gutters become (20px), evidence and topic layouts stack, and the learning route becomes a vertical sequence with connectors. Anchor offsets are (100px), increasing to (128px) on mobile.

The homepage's committed composition moves from mutual agent/simulation improvement and its task–diagnose–improve–retest loop to the actual Wuji comparison, then question-led reading and the four-step learning map. This describes this surface; it is not a prescribed layout for other pages. Print hides chrome and topic buttons, exposes all topic panels, and avoids splitting the principal content grids.

## Elevation & Depth

The implemented system has no box shadows, gradients or elevation animation. Pale panels separate grouped material; quiet rules separate adjacent reading sections. Interactive state changes are immediate color or underline changes. Keyboard focus uses a blue outline (3px) with an offset (5px).

**The Flat Reading Rule.** Use whitespace, tonal grouping and rules to establish hierarchy without raising content above the page.

## Shapes

Actions use the compact action radius; media and the engine directory use the media-panel radius; the research loop uses its slightly softer loop radius. Learning markers are circular. Topic buttons remain square and are distinguished by an underline, not a pill. Reading entries are open rows bounded by thin rules, not enclosed cards.

## Components

### Actions and navigation

The primary action is a solid blue inline link with white text and a darker hover. Secondary actions are blue text links that gain an underline on hover. Navigation uses muted labels that turn blue on hover; language and repository access remain in the header. Mobile primary actions reduce padding to (11px 18px) and type to (14px). Every interactive element retains visible keyboard focus, and a skip link appears on focus.

### Research loop

A pale rounded panel carries the short task sequence, with the skill/simulation improvement branch emphasized in blue. Its next-question return sits on a separate line. It wraps on desktop and becomes a compact grid on mobile. This is explanatory content, not a live experiment-status display.

### Recorded comparison and evidence disclosure

Use the existing native video element with controls, inline playback and no autoplay. It is initially paused with `preload="none"`; its source is the existing comparison MP4. The homepage PNG poster is a lossless extraction of original GIF frame 33 with embedded origin metadata. Keep the source framing, speed, labels and evidence meaning. The caption explains the left/right comparison; the adjacent story leads to the full report. A native details/summary disclosure exposes the scope and limitations beneath the comparison.

### Topic switcher and reading rows

Three plain buttons identify the selected topic with blue text and a bottom stroke (2px). Preserve `aria-pressed` and `aria-controls`; do not present these controls as a tab widget without implementing tab semantics. JavaScript reveals the buttons and selects one panel. Without JavaScript, all three topic panels remain readable. Each panel pairs a question and introduction with ruled reading rows, using a bold title and smaller muted descriptor.

### Learning route and knowledge bridges

Numbered pale-blue circles establish the four-step route. Each step has a heading, short subject list, prerequisite and course link. A pale engine directory follows, then text links connect course concepts with corresponding experiments. Keep those links directed to their canonical sources; course contents are maintained elsewhere. The English surface retains its note about course language.

## Do's and Don'ts

### Do:

- **Do** apply these tokens only to the dedicated research homepages.
- **Do** preserve visible keyboard focus, native disclosure and video controls, and the complete reading index without JavaScript.
- **Do** keep both languages aligned while allowing their text to wrap independently.
- **Do** reuse original evidence assets and retain their provenance and explanatory captions.

### Don't:

- **Don't** restyle existing articles, Sphinx documentation or the web application through this homepage system.
- **Don't** replace recorded evidence with generated scientific imagery or autoplay the replay.
- **Don't** turn the flat reading index into a grid of raised decorative cards.
- **Don't** invent input fields, chips, animation tokens or component variants that this homepage does not use.
