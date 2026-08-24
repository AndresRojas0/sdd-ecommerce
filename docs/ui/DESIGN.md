---
version: alpha
name: "Wickes Bold Retail"
description: "Wickes is a UK DIY and home improvement retailer with a bold, high-energy visual identity built on a navy (#003087) and gold/yellow (#ffd700) dual-tone palette. The design uses condensed typefaces (Oswald for headings/labels, Roboto Condensed for body) to pack maximum information into compact spaces. All interactive elements. buttons, nav items, category tiles. use sharp 0px border-radius corners with flat offset box-shadows (3px 3px) that give a retro-stamp quality. The hero section uses a deep navy background with large Oswald headlines in white and gold, reinforcing the brand's authoritative, value-driven personality. An orange accent stripe (#e85d04 / oklch 0.65 0.22 45) appears as a promotional banner and border highlight. The layout is dense and promotional, typical of a value-focused home improvement retailer."
colors:
  orange-accent: "#e85d04"
  light-gray: "#f0f0f0"
  navy-primary: "#003087"
  white: "#ffffff"
  dark-navy-text: "#1a1f3a"
  gold-yellow: "#ffd700"
  mid-gray: "#666666"
  border-gray: "#cccccc"
typography:
  hero-headline:
    fontFamily: "Oswald"
    fontSize: "48px"
    fontWeight: "700"
    lineHeight: "52.8px"
    letterSpacing: "0.96px"
  section-heading:
    fontFamily: "Oswald"
    fontSize: "22.4px"
    fontWeight: "700"
    lineHeight: "26.88px"
    letterSpacing: "0.36px"
  nav-label:
    fontFamily: "Oswald"
    fontSize: "12px"
    fontWeight: "700"
    lineHeight: "17.4px"
    letterSpacing: "0.6px"
  category-tile-label:
    fontFamily: "Oswald"
    fontSize: "14.4px"
    fontWeight: "700"
    lineHeight: "17.28px"
    letterSpacing: "0.288px"
  body-text:
    fontFamily: "Roboto Condensed"
    fontSize: "14px"
    fontWeight: "400"
    lineHeight: "20.3px"
  small-body:
    fontFamily: "Roboto Condensed"
    fontSize: "12px"
    fontWeight: "400"
    lineHeight: "16.8px"
  badge-label:
    fontFamily: "Oswald"
    fontSize: "13.6px"
    fontWeight: "700"
    lineHeight: "19.72px"
    letterSpacing: "0.68px"
  button-label:
    fontFamily: "Oswald"
    fontSize: "19.2px"
    fontWeight: "700"
    lineHeight: "27.84px"
rounded:
  none: "0px"
  xs: "0.125rem"
spacing:
  xs: "1.6px"
  sm-1: "3px"
  sm-2: "3.2px"
  sm-3: "4px"
  sm-4: "4.8px"
  sm-5: "5.6px"
  base: "6.4px"
  md-1: "8px"
  md-2: "9.6px"
  md-3: "12px"
  md-4: "16px"
  lg-1: "20px"
  lg-2: "24px"
  xl: "32px"
---

## Overview

Wickes is a UK DIY and home improvement retailer with a bold, high-energy visual identity built on a navy (#003087) and gold/yellow (#ffd700) dual-tone palette. The design uses condensed typefaces (Oswald for headings/labels, Roboto Condensed for body) to pack maximum information into compact spaces. All interactive elements. buttons, nav items, category tiles. use sharp 0px border-radius corners with flat offset box-shadows (3px 3px) that give a retro-stamp quality. The hero section uses a deep navy background with large Oswald headlines in white and gold, reinforcing the brand's authoritative, value-driven personality. An orange accent stripe (#e85d04 / oklch 0.65 0.22 45) appears as a promotional banner and border highlight. The layout is dense and promotional, typical of a value-focused home improvement retailer.

**Signature traits:**
- Dual typeface system: Pairs Oswald and Roboto Condensed across the type hierarchy.
- Tight geometric corners: Near-square geometry with corner radii capped around 2px.
- Layered elevation: Depth comes from 5 validated shadow tokens.

## Colors

The palette uses 8 validated color tokens across 1 theme profile. Semantic roles stay attached to observed usage so generation agents can choose accents without inventing new color meaning.

**Semantic naming:**
- **action-background** maps to `navy-primary`: Role "background" is grounded by usage context "Hero background, nav background, sidebar, primary CTA button background, department tile backgrounds".
- **action-text** maps to `gold-yellow`: Role "text" is grounded by usage context "Hero headline accent text, promotional text, brand logo background, secondary button background".
- **surface-background** maps to `white`: Role "background" is grounded by usage context "Page background, card surfaces, search input background, nav text on dark".
- **action-accent** maps to `orange-accent`: Role "accent" is grounded by usage context "Promotional banner strip, nav active border-bottom, button shadow on yellow buttons, sale badge".

### Primary Brand
- **Orange Accent** (#e85d04): Promotional banner strip, nav active border-bottom, button shadow on yellow buttons, sale badge. Role: accent.

### Text Scale
- **Dark Navy Text** (#1a1f3a): Body text, heading text on light backgrounds, nav link text. Role: text.
- **Gold Yellow** (#ffd700): Hero headline accent text, promotional text, brand logo background, secondary button background. Role: text. {authored: rgba(255, 215, 0, 0.3), space: rgb, alpha: 0.3}
- **Mid Gray** (#666666): Secondary body text, footer links, muted labels. Role: text. {authored: rgb(102, 102, 102), space: rgb}

### Interactive
- **Border Gray** (#cccccc): Input borders, card dividers, subtle separators. Role: border. {authored: rgb(204, 204, 204), space: rgb}

### Surface & Shadows
- **Light Gray** (#f0f0f0): Muted surface backgrounds, section dividers. Role: background. {authored: rgb(240, 240, 240), space: rgb}
- **Navy Primary** (#003087): Hero background, nav background, sidebar, primary CTA button background, department tile backgrounds. Role: background. {authored: rgba(0, 48, 135, 0.8), space: rgb, alpha: 0.8}
- **White** (#ffffff): Page background, card surfaces, search input background, nav text on dark. Role: background. {authored: rgb(255, 255, 255), space: rgb, alpha: 0.2}

## Typography

Typography uses Oswald, Roboto Condensed across extracted hierarchy roles. Keep hierarchy mapped to these token rows before adding decorative type styles.

Mixes Oswald and Roboto Condensed for visual contrast. Weight range spans bold, regular. Sizes range from 12px to 48px.

### Font Roles
- **Headline Font**: Oswald
- **Body Font**: Oswald

### Type Scale Evidence
| Role | Font | Size | Weight | Line Height | Letter Spacing | Stack / Features | Notes |
|------|------|------|--------|-------------|----------------|------------------|-------|
| Primary hero heading — large, bold, uppercase Oswald for maximum impact | Oswald | 48px | 700 | 52.8px | 0.96px | Oswald, sans-serif | Extracted token |
| Section titles like 'Shop by Department' | Oswald | 22.4px | 700 | 26.88px | 0.36px | Oswald, sans-serif | Extracted token |
| Navigation menu items, category labels, uppercase department names | Oswald | 12px | 700 | 17.4px | 0.6px | Oswald, sans-serif | Extracted token |
| Department tile labels in the shop-by-department grid | Oswald | 14.4px | 700 | 17.28px | 0.288px | Oswald, sans-serif | Extracted token |
| Primary body copy, product descriptions, general paragraph text | Roboto Condensed | 14px | 400 | 20.3px | normal | Roboto Condensed, Arial, sans-serif | Extracted token |
| Secondary body text, footer links, helper text | Roboto Condensed | 12px | 400 | 16.8px | normal | Roboto Condensed, Arial, sans-serif | Extracted token |
| NEW badge, promotional pill labels | Oswald | 13.6px | 700 | 19.72px | 0.68px | Oswald, sans-serif | Extracted token |
| Primary CTA button text | Oswald | 19.2px | 700 | 27.84px | normal | Oswald, sans-serif | Extracted token |

## Layout

Responsive system uses 2 breakpoint tier(s): mobile, desktop.

This system uses a 8px base grid with scale values 1.6, 3, 3.2, 4, 4.8, 5.6, 6.4, 8, 9.6, 12, 16, 20, 24, 32.

### Responsive Strategy
- **mobile (<= 600px)**: Constrain layout for small viewports and prioritize vertical stacking.
- **desktop (Unknown)**: Expand layout density and horizontal composition for wide viewports.

### Spacing System
| Token | Value | Px | Notes |
|------|-------|----|-------|
| xs | 1.6px | 1.6 | Extracted spacing token |
| sm-1 | 3px | 3 | Extracted spacing token |
| sm-2 | 3.2px | 3.2 | Extracted spacing token |
| sm-3 | 4px | 4 | Extracted spacing token |
| sm-4 | 4.8px | 4.8 | Extracted spacing token |
| sm-5 | 5.6px | 5.6 | Extracted spacing token |
| base | 6.4px | 6.4 | Extracted spacing token |
| md-1 | 8px | 8 | Extracted spacing token |
| md-2 | 9.6px | 9.6 | Extracted spacing token |
| md-3 | 12px | 12 | Extracted spacing token |
| md-4 | 16px | 16 | Extracted spacing token |
| lg-1 | 20px | 20 | Extracted spacing token |
| lg-2 | 24px | 24 | Extracted spacing token |
| xl | 32px | 32 | Extracted spacing token |

## Elevation & Depth

Keep depth flat unless validated shadow or interaction evidence appears in the extraction payload. Do not invent shadows beyond this evidence boundary.

### Shadow Evidence
| Shadow Token | Layers | Details |
|--------------|--------|---------|
| Navy Offset Shadow | 1 | 0.13 3px 3px 0px |
| Black Soft Offset Shadow | 1 | 3px 3px 0px 0px rgba(0, 0, 0, 0.12) |
| Orange Offset Shadow | 1 | 0.2 2px 2px 0px |
| Navy Offset Shadow Small | 1 | 0.13 2px 2px 0px |
| Orange Offset Shadow Large | 1 | 0.2 3px 3px 0px |

### Interaction Signals
| Theme | Signal | Evidence |
|-------|--------|----------|
| Light | outline-color | oklab(0.26 -0.0156793 -0.149178 / 0.5) ; oklch(0.15 0.05 264) |
| Light | outline-width | 3px |
| Light | outline-offset | 0px |
| Light | transform | matrix(0.999848, -0.0174524, 0.0174524, 0.999848, 0, 0) ; matrix(0.999391, 0.0348995, -0.0348995, 0.999391, 0, 0) ; matrix(1, 0, 0, 1, 713.375, 0) |

## Shapes

Shape language maps directly to rounded tokens. Keep component corners consistent with the role mapping below before introducing bespoke geometry.

### Radius Roles
| Token | Value | Px | Role Mapping |
|------|-------|----|--------------|
| none | 0px | 0 | Hairline corner |
| xs | 0.125rem | 2 | Hairline corner |

### Geometry Evidence
| Radius Token | Shape | Units |
|--------------|-------|-------|
| none | 0 | px |
| xs | 0.125 | rem |

## Components

(none detected)

## Do's and Don'ts

Guardrails protect Dual typeface system, Tight geometric corners, Layered elevation without adding unsupported visual claims.

| Do | Don't |
|----|---------|
| Do maintain consistent spacing using the base grid | Don't make unsupported claims about absent visual features |
| Do maintain WCAG AA contrast ratios (4.5:1 for normal text) | Don't mix rounded and sharp corners in the same view |
| Do use the primary color only for the single most important action per screen |  |
| Do verify evidence before writing new design-system guidance |  |

## Responsive Evidence

### Breakpoints
| Name | Width | Key Changes |
|------|-------|-------------|
| Mobile | <= 600px | (max-width: 600px) |
| Breakpoint 2 | Unknown | (hover: none) and (pointer: coarse) |

## Agent Prompt Guide

### Example Component Prompts
- Create button component using validated primary color role and spacing tokens.
- Create card component with mapped radius role and evidence-backed elevation.
- Create form input component using inferred typography hierarchy and border roles.

### Iteration Guide
1. Start with extracted palette and typography roles only.
2. Map spacing and radius directly from token tables before visual polish.
3. Apply component patterns one section at a time and compare against source intent.
4. Keep elevation claims tied to explicit evidence in output.
5. Iterate with smallest diffs and re-check section hierarchy after each change.
