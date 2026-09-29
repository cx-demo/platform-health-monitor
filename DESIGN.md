---
name: Platform Health & Mission Readiness Service
description: Read-only fleet plate in statistical-atlas language, constrained to ICD-PHM-002 revision D.
colors:
  paper: "#e5e1d8"
  plate: "#f4f2ec"
  ink: "#16130f"
  ink-2: "#55504a"
  ink-hair: "#16130f26"
  ink-rule: "#16130f14"
  blue: "#16496e"
  vermillion: "#c1321c"
typography:
  display:
    fontFamily: "Helvetica Neue, Helvetica, Arial, Liberation Sans, sans-serif"
    fontSize: "clamp(1.5rem, 0.95rem + 2.3vw, 2.5rem)"
    fontWeight: 700
    lineHeight: 1.04
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Helvetica Neue, Helvetica, Arial, Liberation Sans, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 700
    lineHeight: 1.5
    letterSpacing: "0.14em"
  body:
    fontFamily: "Helvetica Neue, Helvetica, Arial, Liberation Sans, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  body-small:
    fontFamily: "Helvetica Neue, Helvetica, Arial, Liberation Sans, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "normal"
  mono-label:
    fontFamily: "ui-monospace, SF Mono, SFMono-Regular, Menlo, Consolas, Liberation Mono, monospace"
    fontSize: "0.6875rem"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "0.06em"
  micro-label:
    fontFamily: "Helvetica Neue, Helvetica, Arial, Liberation Sans, sans-serif"
    fontSize: "0.625rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0.12em"
spacing:
  unit: "0.5rem"
  sub-gap: "0.75rem"
  sub-value: "3.75rem"
  sub-name: "clamp(6.5rem, 11vw, 9rem)"
  sheet-margin: "clamp(1.25rem, 0.5rem + 3.5vw, 5rem)"
components:
  plate-frame:
    backgroundColor: "{colors.plate}"
    textColor: "{colors.ink}"
    padding: "calc({spacing.unit} * 3.5) calc({spacing.unit} * 3.5) calc({spacing.unit} * 4)"
  status-mark-filled:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.ink}"
    width: "0.625rem"
    height: "0.625rem"
  status-mark-outline:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    width: "0.625rem"
    height: "0.625rem"
  published-bar:
    backgroundColor: "{colors.blue}"
    textColor: "{colors.ink}"
    height: "0.625rem"
  peak-bar:
    backgroundColor: "{colors.vermillion}"
    textColor: "{colors.vermillion}"
    height: "0.625rem"
---

# Design System: Platform Health & Mission Readiness Service

## Overview

**Creative North Star: "The Printed Engineering Plate"**

The shipped `GET /dashboard` surface is a read-only fleet plate, not an operations console. It belongs to the statistical-atlas data-graphic tradition: Otto Neurath and Gerd Arntz ISOTYPE for countable unit signs, Jacques Bertin for shared visual variables, and Edward Tufte for measured restraint. The world is paper, ink, rule, figure, and reserved absence.

Mode is **Operate**. Engineers scan published facts, compare three platforms on one shared scale, see the measured extremity, and also see the contract gap drawn as hatched reserved space. Interface absence is not hidden and not dramatised; it is dimensioned as an engineering fact.

Binding constraints are law for this surface: it is read-only; it may render only fields published by ICD-PHM-002 revision D (`platformId`, `designation`, `platformType`, `operational`, `readinessState`, `readinessConfidence`, and subsystem `subsystemId`, `name`, `temperatureCelsius`, `operational`); `readinessState` and `readinessConfidence` are rendered as neutral text only; no third-party origins or webfonts; presentation routes such as `/` and `/dashboard` stay out of `/openapi.json` and `/v2/openapi.json`. Readiness is read from `/v2`; `/platforms` (revision C) carries none.

**Key Characteristics:**
- Light ground with printed plate, black ink, hairline rules, square corners.
- Figures, bars, marks, and hatched reserved voids instead of dashboard cards.
- Status encoded as mark plus text, never hue alone.
- One authored motion moment only: bars rule out with `scaleX`; default state is already legible.
- Air-gapped by design: system fonts, inline CSS/JS/SVG, no external assets.

## Colors

Palette is deliberately narrow: two paper values, two ink values, two ink alphas for rules, one atlas blue for published quantity, one vermillion for measured extremity and focus/error emphasis.

### Primary
- **Atlas Blue** (`blue`): Used only for published measured quantities: ordinary subsystem temperature bars. Do not use it for status, navigation, decoration, or sentiment.

### Secondary
- **Vermillion Extremity** (`vermillion`): Used only for measured extremity and necessary attention treatments: peak bar, peak value, callout figure, error notice border/head, and focus outline. It does not mean danger, failure, or readiness.

### Neutral
- **Paper Ground** (`paper`): Body background; outer page stock.
- **Plate Paper** (`plate`): Figure panels and reserved label backing; inner sheet stock.
- **Black Ink** (`ink`): Primary text, filled unit signs, status marks, plate borders, hard rules.
- **Muted Ink** (`ink-2`): Standfirsts, notes, metadata, labels, subdued annotations.
- **Hairline Ink** (`ink-hair`): Gridlines, quiet borders, hatched fills, link underlines.
- **Rule Ink** (`ink-rule`): Row dividers and skeleton hatch texture.

### Named Rules

**The Chromatic Quantity Rule.** Blue is quantity and vermillion is extremity. Neither colour may encode serviceability, readiness, severity, or tasking authority.

**The Absence Is Reserved Rule.** Missing or unpublished information is hatched reserved space in ink, never red/amber warning colour and never a zero value.

**The Contrast Override Rule.** High-contrast mode strengthens `ink-hair`, `ink-rule`, and `ink-2`; do not replace this with a separate colour theme.

## Typography

**Display Font:** system grotesque stack (`Helvetica Neue`, Helvetica, Arial, `Liberation Sans`, sans-serif)
**Body Font:** same system grotesque stack
**Label/Mono Font:** platform monospace stack (`ui-monospace`, `SF Mono`, SFMono-Regular, Menlo, Consolas, `Liberation Mono`, monospace)

**Character:** Industrial grotesque typography carries the plate's captions and explanatory prose. Mono type is reserved for identifiers, revision metadata, measurement values, records, and code-like interface names.

### Hierarchy
- **Display** (700, `clamp(1.5rem, 0.95rem + 2.3vw, 2.5rem)`, line-height `1.04`, uppercase): Page title. Tight, all-caps, slightly negative tracking.
- **Tally Read** (700, `clamp(1.0625rem, 0.95rem + 0.6vw, 1.375rem)`, line-height `1.3`): Primary operational sentence under unit signs.
- **Plate Title** (700, `0.75rem`, uppercase, letter-spacing `0.14em`): Figure titles.
- **Body** (400, `1rem`, line-height `1.5`): Default reading rhythm on body.
- **Small Body** (400, `0.9375rem`, line-height `1.55` or `1.6`): Standfirsts, qualifiers, intro copy, void questions.
- **Micro Label** (`0.625rem`, uppercase, letter-spacing `0.12em` to `0.14em`): Axis labels, notice heads, reserved labels.
- **Mono Label** (`0.6875rem`, letter-spacing `0.04em` to `0.06em`): Revision values, IDs, figure numbers, temperature values.

### Named Rules

**The No Webfont Rule.** No network fonts, icon fonts, or third-party font origins. The deployment is assumed air-gapped.

**The Identifier Mono Rule.** Use mono for machine-facing facts: identifiers, revisions, endpoint names, measurements, and records. Do not set explanatory prose in mono.

## Layout

The sheet is centered with `max-width: 78rem` and fluid outer margin `sheet-margin`. It uses a caption grid first: left narrative block, right revision ledger, then figure plates stacked vertically.

The base spatial unit is `--u: 0.5rem`. Major gaps are multiples of that unit: plate top margin `4u`, plate padding `3.5u 3.5u 4u`, plate-head bottom `3.5u`, row padding `2.5u`, tally sign gap `4u`, callout top `4u`, colophon top `4u`.

Measured rows use one shared scale grid: platform identity column `minmax(9rem, 14rem)`, state column `minmax(6.5rem, 8rem)`, and remaining scale column. Inside the scale, subsystem name, track, and value share `sub-name`, `sub-gap`, and `sub-value` so the axis, gridlines, and bars actually align.

At widths up to `54rem`, the axis is hidden, row layout collapses to one column, subsystem labels sit above tracks, void ledger items stack, and callouts become single-column. At `54.0625rem` and above, the tally body becomes a two-column read/qualifier composition.

## Elevation & Depth

No shadows ship. Depth is conveyed through material layering (`paper` behind `plate`), hard ink borders, dividers, gridlines, and tonal contrast. The system is printed, not floating; panels do not lift, hover, glow, blur, or cast ambient depth.

### Named Rules

**The No Shadow Rule.** Do not add box shadows to this surface. Use paper contrast, borders, and rules.

## Shapes

The form language is square and mechanical. Plates, notices, marks, bars, skeleton rows, reserved fields, and unit signs use square corners. Shape contrast comes from filled versus outlined signs, bars versus hatched voids, and hand-built geometric SVG silhouettes, not from radius or softness.

Borders are structural: 2px ink for caption and callout separators, 1px ink for plate frames and reserved fields, 1.5px ink for status mark outlines, alpha ink for row dividers and gridlines.

## Components

### Plate Frame

A plate is the fundamental container: `plate` paper background, 1px black ink border, square corners, top margin `4u`, and padded interior `3.5u 3.5u 4u`. Every plate begins with a flexing head: all-caps figure title left, mono figure context right.

### Tally Unit Signs

Fleet count is drawn with inline SVG unit signs, not icons from a library. Solid fill means published platform `operational` is true; outline means false. The label under each sign is mono and subdued. Status meaning must also be stated in text.

### Status Mark

Serviceability state is a 0.625rem square mark plus text. Filled mark plus “Reports operational”; outlined mark plus “Reports not operational”. Never substitute traffic-light hue, badges or lamps.

### Readiness Text

The published `readinessState` and `readinessConfidence` (ICD-PHM-002 rev D, SYS-4412) appear under each platform identifier as one line of mono ink text: “Readiness NMC · confidence LOW”. No colour, mark, badge, lamp, icon or ranking. The plate repeats the service's verdict; it never derives its own.

### Measured Bar Row

Temperature rows align name, track, and value to the shared axis. Ordinary bars use atlas blue. The single fleet peak uses vermillion for bar and value, then receives explanatory callout copy. Bars show measured magnitude only; they do not classify threshold, severity, health, or readiness.

### Reserved Void

Unpublished fields are 1px ink boxes filled with 45-degree hatching and a centered mono “Reserved” label. The void has dimensions; it is not empty whitespace and not an error state.

### Record Link

Record links are mono, uppercase, subdued, underlined with hairline ink. Hover strengthens ink. Focus-visible uses a 2px vermillion outline with 3px offset.

### Notice and Skeleton

Loading skeletons use hatched rows; they do not shimmer. Empty and error notices use ink-framed blocks. Error may use vermillion only on border/head because it describes failed retrieval, not platform status.

### Motion

The only authored motion is `rule-out`: bar and void elements animate from `scaleX(0)` to `scaleX(1)` for `720ms` with `cubic-bezier(0.16, 1, 0.3, 1)`, only under `prefers-reduced-motion: no-preference`. Nothing starts invisible; with reduced motion or no animation support, all content remains complete and legible.

## Do's and Don'ts

### Do:
- **Do** keep the surface read-only and sourced from `GET /v2/platforms` (revision D) plus links to published `/v2` platform records.
- **Do** render only ICD-PHM-002 revision D fields and preserve the visible contract gap for fields that remain unpublished.
- **Do** encode state as mark plus text; colour may reinforce measurements only.
- **Do** use system grotesque and platform mono stacks only.
- **Do** keep presentation routes out of the generated interface contracts; `/openapi.json` and `/v2/openapi.json` must remain machine-readable ICD-PHM-002, not UI navigation.
- **Do** draw absence as hatched reserved space when a question is not answerable from revision D.

### Don't:
- **Don't** infer a readiness verdict of the plate's own, style `readinessState` or `readinessConfidence` with colour or badges, or publish any tasking conclusion.
- **Don't** use traffic lights, gauges, gauge rings, sparklines, vital-sign traces, ECG metaphors, lamps, severity badges, or red/amber/green status language.
- **Don't** re-propose the dark neon ops-centre dashboard; it was rejected as the category default and would imply live command authority the product does not have.
- **Don't** re-propose white SaaS analytics cards; they were rejected as the predictable opposite and would make the contract gap feel like business intelligence, not interface governance.
- **Don't** re-propose the ECG/vital-signs metaphor; it was rejected as the brief's literal reading and falsely suggests diagnosis, patient state, or continuous telemetry.
- **Don't** add webfonts, CDNs, third-party origins, icon libraries, or image dependencies.
- **Don't** add shadows, rounded card softness, neon glow, or animated dashboard spectacle.
