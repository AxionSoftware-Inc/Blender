# Showcase Development Status — 2026-09-06

This file tracks only the canonical product/showcase sequence. For architecture and historical handoff context, see `docs/CHAT_LIMIT_HANDOFF_2026-09-06.md`. When older handoff prose conflicts with the current source tree, the current source tree and dedicated validation handoffs take precedence.

| # | Showcase | Runtime status | Validation status | Main scientific reuse |
|---|---|---|---|---|
| 1 | Maxwell Electromagnetic Wave | Implemented | Dedicated handoff + Blender smoke exist; promote only from actual local results | plane-wave EM semantics, generic field views, Scene/Timeline, presentation |
| 2 | Electrostatic Field Laboratory | Implemented | Dedicated handoff + Blender smoke exist; local promotion pending | point-source deposition, electrostatic Poisson, potential fields, field dynamics, quantitative presentation |
| 3 | Quantum 2D Wavepacket | Implemented | Dedicated handoff + Blender smoke exist; local promotion pending | Schrodinger 2D, complex PDE, probability mass, quantitative/phase presentation |
| 4 | Thermoelastic Heating | Implemented | Dedicated handoff + Blender smoke added; local validation pending | heat conduction, thermoelastic thermal strain, quantitative solid presentation |
| 5 | Schwarzschild / Black-hole Geodesics | Planned next | Not started | relativity + differential geometry + geodesics |

## Showcase rules

Every showcase must:

1. reuse existing scientific domains/capabilities instead of duplicating formulas;
2. use a bounded deterministic canonical configuration;
3. produce a renderer-neutral Scene/Timeline first;
4. keep display scale separate from scientific scale;
5. use presentation intent rather than backend-specific styling in science code;
6. add Python acceptance tests;
7. add targeted Blender smoke where native behavior matters;
8. add a dedicated validation handoff;
9. be labeled `IMPLEMENTED / PENDING VALIDATION` until the local gate passes.

## Current engineering point

The first four canonical showcases now have source-level implementations. Quantum and Thermoelastic code are ahead of the original chat-limit handoff and must not be downgraded to "not started" merely because that historical document predates their commits.

Before flagship #5 is implemented, the Schwarzschild path needs a numerical audit of geodesic derivative scaling. The current generic finite-difference Christoffel capability uses one absolute derivative step across all coordinate axes, while the Schwarzschild chart mixes length-like `(ct, r)` coordinates with angular `(theta, phi)` coordinates. A black-hole trajectory must not be promoted from visually plausible output without addressing or quantitatively validating that mixed-scale derivative behavior.

The next safe product sequence is therefore:

```text
Thermoelastic local validation gate
    -> geodesic derivative-scale hardening/validation
    -> Schwarzschild / black-hole geodesic flagship
```
