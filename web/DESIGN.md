---
name: "DexLab claw-machine surface"
description: "Scoped dark dreamy cabinet, claw and supporting play interface."
colors:
  page-plum: "#15111e"
  scene-plum: "#1c1627"
  control-plum: "#251c30"
  quiet-plum: "#241a30"
  quiet-hover: "#3b294a"
  move-plum: "#40304e"
  move-hover: "#5c426c"
  text-pale: "#f3eaf6"
  text-muted: "#c9b9d4"
  edge-plum: "#4a3959"
  action-rose: "#e8afe0"
  action-hover: "#f6d1ef"
  action-ink: "#321e37"
  focus-lilac: "#dec1f5"
  cabinet-enamel: "#30223f"
  cabinet-mauve: "#885e93"
  cabinet-silver: "#e2c2eb"
  seam-rose: "#e8a5d5"
  moon-gold: "#ffe3ad"
  comparison-gold: "#f4cc79"
  claw-lilac: "#d7b6df"
typography:
  body:
    fontFamily: "ui-sans-serif, system-ui, sans-serif"
    fontSize: "14px"
    lineHeight: 1.6
  explanation:
    fontSize: "14px"
    lineHeight: 1.75
  ui-heading:
    fontSize: "clamp(24px, 3vw, 31px)"
    lineHeight: 1.25
    letterSpacing: "-0.025em"
  section:
    fontSize: "21px"
    letterSpacing: "-0.02em"
  action:
    fontSize: "20px"
    fontWeight: 700
  label:
    fontSize: "11px"
rounded:
  hint: "4px"
  label: "6px"
  control: "8px"
  action: "9px"
  enclosure: "12px"
spacing:
  compact: "5px"
  small: "8px"
  group: "12px"
  panel: "16px"
  section: "18px"
  page: "24px"
components:
  button-primary:
    backgroundColor: "{colors.action-rose}"
    textColor: "{colors.action-ink}"
    typography: "{typography.action}"
    rounded: "{rounded.action}"
    width: "100%"
  button-primary-hover:
    backgroundColor: "{colors.action-hover}"
  button-quiet:
    backgroundColor: "{colors.quiet-plum}"
    textColor: "{colors.text-pale}"
    rounded: "{rounded.control}"
    padding: "8px 13px"
  button-quiet-hover:
    backgroundColor: "{colors.quiet-hover}"
  button-direction:
    backgroundColor: "{colors.move-plum}"
    textColor: "{colors.text-pale}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
  button-direction-held:
    backgroundColor: "{colors.move-hover}"
  select:
    backgroundColor: "{colors.quiet-plum}"
    textColor: "{colors.text-pale}"
    rounded: "{rounded.label}"
    padding: "8px"
  scene-caption:
    backgroundColor: "{colors.quiet-plum}"
    textColor: "{colors.text-pale}"
    rounded: "{rounded.label}"
    padding: "5px 8px"
  scene-container:
    backgroundColor: "{colors.scene-plum}"
    rounded: "{rounded.enclosure}"
---

# Design System: DexLab claw-machine surface

## Overview

**Creative North Star: "Dark dreamy cute claw machine"**

This record applies only to the claw-machine scene and its supporting play, collection and comparison interface in `web/src/claw*`. It captures the user-approved dark dreamy cabinet and claw change. It does not redefine the DexLab documentation site, the older solver page or the repository brand.

Deep plum enamel, rose luminous seams, dimensional moon and star ornaments, a silver-lilac moving claw and a dense pile of warm prizes establish the scene. One fixed cabinet contains 30 toy instances spanning all 16 Nai-family identities; there is no lineup selector. The surrounding interface uses the same plum family with one clear rose action. Compact interface typography remains; no new display-font identity was approved.

The cabinet housing and ornaments are decorative meshes. Toy materials suggest plush, while MuJoCo still owns rigid-body poses and contact. WebGL is the public renderer; local OVRTX receives exported scene materials and native pose snapshots. Rendering, replay and material appearance do not establish physical accuracy. Motion follows native state or an explicit replay/inspection command, with no ambient interface animation.

**Key Characteristics:**

- Plum enclosure with rounded physical edges and rose luminous seams.
- Thirty enlarged textured toys in a gravity-driven pile, a complete silver-lilac claw and a raised gold-rimmed chute.
- Quiet bordered controls, visible input focus and scene-independent caption backing.
- One aiming view; synchronized comparison views share camera and time.

## Colors

Plum grounds the scene and controls; rose identifies the main action and luminous seams, silver-lilac articulates the moving claw, and warm gold makes the chute and moon legible.

### Primary

- **Action rose:** Drop/Re-aim, completion outlines and selected text; its lighter hover color marks an available action.
- **Seam rose:** emissive cabinet seams and star details, implemented as material-bearing geometry.

### Secondary

- **Silver-lilac:** cabinet trim and articulated claw segments; the claw uses its own slightly deeper material tone.
- **Mauve:** trolley, ornament relief and secondary cabinet trim.
- **Warm gold:** moon and the open prize-chute rim. Preserve this destination cue against the plum deck.

### Neutral

- **Page, scene and control plum:** separate the outer page, rendered viewport and controls through tone rather than ornamental page effects.
- **Quiet/move plum:** subordinate action surfaces; their hover/held variants remain in the same hue family.
- **Pale text, muted text and plum edge:** primary information, supporting explanations and structural borders.
- **Focus lilac:** keyboard focus and links. It also labels the first comparison view; the second uses action rose and the third retains the separate comparison-gold accent.

**The Rose Action Rule.** Use the rose fill for Drop/Re-aim and the same accent for collection completion; retain pale text and muted lilac for ordinary information.

**The Readable Overlay Rule.** Keep scene captions on their dark backing so moving geometry cannot determine text contrast.

## Typography

The inherited compact sans stack is interface typography. This record does not prescribe a system font as a new brand display face. The existing page heading remains an interface title; the cabinet is the visual focal point.

The token roles cover the observed interface title, section title, primary action, explanatory body and small labels. Heading descriptions and teaching introductions use the body role; longer teaching paragraphs use the explanation role and a maximum width of 74ch. The footer and compact controls use small supporting text. Numerical scores and replay measurements use tabular figures.

At 480px and below, the interface title is 24px, the primary action becomes 23px, and secondary button labels become 11px. These are the implemented responsive values, not a new global type scale. The tiny collection counts and inherited status styling are recorded as existing behavior, not a mandate for future small text.

## Layout

The page is centered at a maximum width of 1160px with 24px outer padding. The ordinary enclosure places a flexible scene beside a 220px control column. Its canvas fills the column height with a 480px minimum. Collection portraits sit below the enclosure and round feedback, so the inventory no longer determines the control-column height.

At 760px and below, outer padding becomes 16px, the scene moves above controls and the canvas is 390px tall. At 480px and below, outer padding becomes 12px, the canvas is 350px tall and the D-pad and primary action sit side by side. Direction targets are at least 46px high and the primary action is 82px high in this narrow layout. Secondary controls retain a 44px minimum; selects have a 40px minimum.

The collection inventory uses eight columns on desktop and four columns at 760px and below. Its block has 20px top and 28px bottom margins, with 14px row gaps and 10px column gaps; narrow screens at 480px and below reduce the column gap to 6px and place each portrait above its name and count. These local inventory measurements do not change the shared spacing tokens.

Comparison mode uses the full enclosure width. At scene-container widths of 700px or more, three synchronized views sit side by side in a 440px-high canvas. Below 700px they stack in a 1080px-high canvas. This is a container breakpoint, not a page-width assumption. Comparison controls wrap underneath; aim controls and the collection inventory are hidden during comparison.

Spacing uses compact 5–8px internal gaps and repeated 12–24px group, panel and page spacing. The 19px by 17px desktop control padding is an existing local fit, not a new spacing-system increment. The ordinary camera targets the prize pile and complete claw, with field of view and position adjusted for compact aspects. The lower collection well intentionally extends outside this play-bay framing. Portrait inspection and top view provide alternate compositions; fitting the full cabinet base is no longer an overview requirement.

## Elevation & Depth

The interface is flat: tonal surfaces, thin borders and focus outlines provide hierarchy without CSS box shadows. Physical depth comes from the rendered cabinet, rounded edges, light, material response and contact shadows. Emission belongs to the rose seams, moon and aim marker; there is no CSS glow or bloom requirement.

The cabinet's reused Three.js materials have these configured source settings: enamel metalness 0.35 / roughness 0.28; mauve 0.5 / 0.3; silver 0.65 / 0.24; rose roughness 0.4 with emissive intensity 0.65; moon metalness 0.25 / roughness 0.4 with emissive intensity 0.4. The native claw's visible material uses metalness 0.65 / roughness 0.26. Toy models use roughness 0.92 and metalness 0; their textures carry the warm character colors. These are rendering parameters, not measured material properties.

OVRTX imports exported base color, roughness, metallicity, emission and base-color textures through USD materials. Its lighting and image pipeline differ from WebGL, so this document does not promise pixel-identical renderers. Faint orbit-aid walls are omitted from the RTX export, and top-view-hidden parts do not cover the view. The local renderer's current status remains visible.

**The Geometry First Rule.** Keep the moon, stars, cabinet seams and claw details as scene geometry; do not substitute floating page decoration for the approved cabinet materials.

## Shapes

The enclosure has softly rounded corners; buttons, selects and caption backings use smaller radii from the token set. Borders remain thin and structural. The direction icons are inline SVG paths with text labels, not Unicode arrow glyphs.

The cabinet uses rounded boxes, beveled extruded crescent/star silhouettes and a cat-ear/moon claw hub. These objects are authored geometry; source settings include a common rounded-box radius of 0.008 m with smaller seams and trim. Exact object dimensions remain in `src/claw-cabinet.ts`, not in a global CSS shape scale. The open front, packed tray and gold-rimmed chute are functional parts of the scene composition.

The current source applies `TOY_SCALE = 1.6` to both loaded visual meshes and native collision meshes. Thirty instances begin at ten horizontal positions across three vertical spawn layers; gravity and contact determine their subsequent arrangement. The enlarged toy scale and layered initialization support the requested overlapping pile instead of separated miniature prizes on an empty floor. `CLAW_SCALE = 1.35` enlarges the articulated claw geometry, aim ring and hub charm. The chute lip is raised to 0.18 m and the gold rim follows it. These are scoped geometry settings, not CSS tokens or a claim that the resulting pile and grasp behavior have passed validation.

## Components

### Buttons

The rose primary button carries Drop/Re-aim and changes its visible text with the current task state. It has a 57px minimum height on desktop, no border and a lighter hover fill only when enabled. Secondary buttons use a plum fill, thin edge, compact padding and a 44px minimum height. Direction controls add an SVG arrow and visible direction text; hover and held input share the brighter move-plum state. Disabled buttons use 0.48 opacity and a default cursor. Focus uses a 3px lilac outline with 3px offset; portrait buttons use their existing 2px rose outline.

### Inputs / Fields

Native selects choose iteration cap, renderer and replay speed; the fixed 30-prize mixture has no selector. They use quiet plum, a thin border, rounded corners and visible focus. The replay range remains a native range input with the rose accent and a 28px minimum interaction height; its disabled appearance is 0.5 opacity. No custom text-entry field is introduced by this surface.

### Cards / Containers

One bordered scene/control enclosure carries the game; the interface is not a collection of decorative cards. The scene header caption and camera hint have dark backings. Comparison views use backed method labels and measured-state readouts separated by thin borders. The renderer readout sits below the camera hint and reports connection, delay or active frame status.

### Collection and inspection

Portraits identify the character assets and open an inspection of an actual model. The fixed mixture groups its 30 instances into all 16 character identities below the machine, with collected/available counts under each identity; a completed group receives the rose outline. The whole collection block is hidden during comparison. New cabinet resets and rearranges the same mixture rather than selecting another lineup. The portrait image is an identity aid, not a substitute for the in-scene 3D mesh. Asset provenance stays in `src/assets/README.md` and the corresponding manifest.

### Navigation and explanation

A quiet footer link reaches the older simple-scene comparison. Teaching sections use native details/summary disclosure with borders and readable paragraphs. Existing browser disclosure markers are native controls, not an invitation to introduce decorative glyph icons.

### Motion and renderer status

No CSS transitions or keyframe animations are defined for the claw interface. Camera inspection and top-view commands apply direct view changes. The moving claw, toys, trolley and cable follow native transforms; synchronized replay displays recorded poses on a shared timeline with explicit pause and speed controls. Layered spawn positions initialize the cabinet; ongoing gravity and contact produce motion. The aim ring follows a downward native ray hit on toy collision geometry. At Drop, the descent target is derived from that surface and frozen into the shared start state rather than continuously tracking or attaching to a toy. Hidden-page lifecycle pauses activity. The existing reduced-motion rule disables smooth scrolling; it does not claim to stop simulation or provide an alternative reduced-motion gameplay mode.

A stale local RTX image is hidden and WebGL becomes visible with an explicit status. A disconnected service also exposes WebGL and a message. Retain that truthful fallback rather than displaying an old image as a current simulation frame.

## Do's and Don'ts

### Do:

- **Do** preserve the plum, rose, silver-lilac and warm-gold material roles within the claw surface.
- **Do** frame the enlarged prize pile and complete claw prominently; let the lower collection well extend below the overview while retaining the gold chute cue.
- **Do** keep one fixed mix of 30 toy instances spanning all 16 identities, with grouped collection counts below the machine and no lineup selector.
- **Do** label the active renderer and visible WebGL fallback, and keep native outcome claims separate from appearance.

### Don't:

- **Don't** propagate this scoped palette or cabinet motif into the documentation site or older solver page without a separate decision.
- **Don't** add gratuitous background effects or decorative motion outside the cabinet.
- **Don't** describe plush-looking materials as deformable simulation or measured hardware fidelity.
- **Don't** use collected state, renderer status or decorative motion to imply a guaranteed physical catch.
