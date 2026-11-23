# UM-102 · Planetary simulation data lenses

**Status:** proposed, independent UI feature branch `feature/um-102-planetary-data-lenses`, not merged or deployed. Source: `index.html`, `observatory.mjs`, `world.css`, `tests/smoke.py`. This is a five-channel overlay on the **GitHub v5 prototype**, not the existing public Living World website.

## Purpose and implementation

Move UMBRA from an ornamental-only glow to **visible, inspectable projections of the active synthetic model state**. The planet itself remains a Canvas 2D renderer; these overlays do not create a WebGL engine, a physically accurate geographic raster, or an externally validated measurement. Planet locations are the existing 42 fixed synthetic region coordinates.

The accessible **Planetary Data Lens** selector exposes:

| Lens | Actual derived signal | Brightness semantics |
| --- | --- | --- |
| Settlement population | `sqrt(town.p / 300)`, clamped 0–1 | Larger simulated settlement population |
| Food/water scarcity | Clamped combination of food and water shortfall relative to population-weighted synthetic thresholds | Brighter means relatively fewer local resources |
| Disease burden | `town.infected / max(1,town.p) × 3.6`, clamped | Brighter means a greater synthetic infected fraction |
| Climate exposure | `.58 × site.vulnerability + .42 × world.climate`, reduced to 32% for empty regions | Brighter means greater synthetic vulnerability × current exposure proxy; **not** real climate risk |
| Low council support | `(1 - council.support) × 1.65`, clamped | Brighter means lower simulated council support, **not** measured social unrest |

**Off** disables the additional field and preserves the prior globe, trade arcs, settlement markers and selection interactions. Every overlay is computed from the existing `world` object. Its projection uses the existing orbit camera and positive visible-hemisphere depth, while Canvas clipping keeps field pixels on the globe.

The lenses do not change state, randomness, model rules, trade, scientific outputs, or archived world histories.

## Performance and accessibility

- Only sites on the visible hemisphere are painted. Rendering the field is limited to the existing 42-region list.
- The existing adaptive-quality mode cuts field points in half when graphics quality degrades.
- If `prefers-reduced-motion` is enabled, the field does not pulse. Planet control and keyboard-accessible selection remain available.
- The selector, visible textual status/legend and a non-color-only explanation accompany each color gradient.
- FPS is **measured frame interval**, not a claimed hardware maximum. The feature may increase Canvas drawing cost; record actual frame timings under load and on real phones before calling performance production-ready.
- Existing browser smoke tests now switch all modes on desktop, tablet and phone and verify an explicit reduced-motion phone scenario. They do not replace real-device FPS profiling.

## Acceptance and evidence

Run `node --test tests/*.test.mjs` and `python tests/smoke.py`. The browser test must report no JS errors, zero horizontal overflow, correct mode selection, functional turn controls, and no disabled functionality. CI evidence and final branch SHA must be recorded before claiming a verified improvement. Served ESM and real-worker verification is tracked separately in PR #7 and is not included until integration.

**Known gaps:** no measured production iPhone frame histogram, no screen-reader usability study, no WebGL pipeline, no online atlas/camera deployment and no automatic transfer to the existing live `chatgpt.site` site.

## Change record / handoff

- **Reason:** UM-102 requires visible behavior tied to actual simulated regional data rather than random visual effects.
- **Before:** a cinematic rotating globe, settlement markers and trade routes, but no selectable thematic region heat field.
- **Change:** a five-mode CSS/HTML selector, Canvas projected gradients driven from active model state, adaptive-quality/reduced-motion behavior, diagnostic lens status, tests, and this document.
- **Alternative rejected:** importing a large WebGL/GPU dependency before proving user value and mobile performance. The existing Canvas-based renderer can support a bounded, inspectable overlay without new assets.
- **Rollback:** remove the UI control and renderer additions on this feature branch; the underlying model is unchanged. No migration is required.
- **Next worker:** review visual projection mathematically, inspect side-by-side screenshots across viewports and reduced-motion settings, establish actual p50/p95 frame times on target devices, and coordinate with PR #7 for served-ESM verification. Do not merge unrelated feature branches blindly.
- **Stale when:** signal formulas, regional geometry, renderer, model version, CI, deployment path or PR status changes.
