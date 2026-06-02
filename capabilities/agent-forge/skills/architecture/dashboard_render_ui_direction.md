# Dashboard Render UI Direction

Use this skill when changing the generated Glyf dashboard UI shell, controls, cards, or supporting chart presentation.

This guidance is specific to the rendered dashboard artifact under `src/glyf/dashboard/`.

## Purpose

Keep the rendered dashboard output visually consistent, readable, and artifact-friendly.

The output is a static build artifact, not an app shell that depends on a runtime frontend framework.

## Design Goals

- crisp, intentional, black-and-white-first dashboard chrome
- readable typography at normal desktop viewing distance
- local assets over remote dependencies when possible
- consistent chart and shell presentation
- controls that are visible enough to read without feeling heavy
- portable static output that works from local files, S3, CI artifacts, and static hosts

## Typography

- Use `Hanken Grotesk` for the dashboard shell UI.
- Ship font files locally with dashboard assets instead of relying on remote font CDNs.
- Keep body and label sizes readable; do not optimize for overly compact density.
- Monospace UI should be limited to code-like affordances:
  - source toggle
  - version labels
  - SQL/source drawers
  - small build metadata where appropriate

## Icons

- Prefer a standard Lucide-style icon language over ad hoc hand-drawn inline icons.
- Icons should use black or near-black stroke by default for visibility.
- Avoid decorative filled icons unless the state calls for it.
- Keep icon sizing and stroke consistent across:
  - toolbar
  - metadata rows
  - filters row
  - alerts
  - AI panel

## Controls

- Avoid native browser UI when it breaks visual consistency:
  - prefer custom button/menu over native `<select>` when practical
- `Source`, version controls, filter chips, and metadata bars should be clearly legible.
- Thin UI is acceptable, but not faint UI.
- If a control is important to understanding the artifact, it should have enough contrast to be noticed.

## Cards And Layout

- Favor small radii, not pill-heavy or overly soft cards.
- Avoid “AI slop” styling:
  - oversized rounding
  - weak contrast
  - generic gradient cards unless intentionally used
- Use disciplined spacing and borders.
- Section chrome should feel close to a Vercel/Geist-style static product surface:
  - clean borders
  - restrained accent usage
  - visible but minimal interaction states

## Modal And Drawer Guidance

- Lookback, source, and AI panels should be more visible than the background content.
- Use stronger backdrop contrast and clear card shadow/border separation.
- Titles and supporting copy inside overlays should be slightly stronger than surrounding metadata text.
- Avoid popups that feel too faint or blend into the page.

## Chart Consistency

- Keep chart typography visually aligned with the shell.
- Prefer post-processing or browser-side config updates over renderer-time font assumptions that break `vl-convert`.
- It is acceptable for static chart generation to use size/config tuning plus post-processing, as long as the exported artifact stays consistent.

## Asset Portability

- Prefer local assets in `src/glyf/dashboard/assets/`.
- If `single_file` output is supported, inline dependent assets where necessary so the artifact remains portable.
- Do not introduce remote runtime dependencies for core dashboard presentation unless there is a strong reason.

## Implementation Boundaries

- Dashboard shell structure belongs in:
  - `src/glyf/dashboard/templates/`
  - `src/glyf/dashboard/assets/dashboard.css`
- Asset copying/inlining belongs in:
  - `src/glyf/dashboard/assets.py`
- Chart renderer consistency belongs in:
  - `src/glyf/ggsql/renderer.py`

## When Updating The UI

Before changing the rendered dashboard UI:

1. confirm whether the change affects shell only, chart output only, or both
2. preserve artifact portability
3. prefer improving readability over adding new visual decoration
4. rebuild at least one example dashboard locally
5. refresh committed docs example dashboards if the visual output changed materially

## Anti-Patterns

Avoid:

- pretending to use a font that is not actually shipped
- native controls that break the visual language when a simple custom control is feasible
- faint metadata bars that hide useful state
- excessive rounding and generic card styling
- remote font dependencies for static dashboard artifacts
- introducing framework-heavy frontend machinery for simple generated output
