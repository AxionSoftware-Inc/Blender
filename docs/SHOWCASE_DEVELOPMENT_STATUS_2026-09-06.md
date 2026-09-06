# Showcase Development Status — 2026-09-06

This file tracks only the canonical product/showcase sequence. For full architecture and validation context, see `docs/CHAT_LIMIT_HANDOFF_2026-09-06.md`.

| # | Showcase | Runtime status | Validation status | Main scientific reuse |
|---|---|---|---|---|
| 1 | Maxwell Electromagnetic Wave | Implemented | Dedicated handoff/smoke exists; promote only from actual local results | plane-wave EM semantics, generic field views, Scene/Timeline, presentation |
| 2 | Electrostatic Field Laboratory | Implemented | Pending local promotion | point-source deposition, electrostatic Poisson, potential fields, field dynamics, quantitative presentation |
| 3 | Quantum 2D Wavepacket | Audited, not completed | Not started | Schrodinger 2D, complex PDE, probability mass, quantitative/phase presentation |
| 4 | Thermoelastic Heating | Planned next | Not started | heat conduction, thermoelasticity, solid views |
| 5 | Schwarzschild / Black-hole Geodesics | Planned | Not started | relativity + differential geometry + geodesics |

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

## Current handoff point

Electrostatic implementation was completed and documented. Quantum was being audited when the chat-limit handoff was requested. The first unfinished engineering action is therefore Quantum 2D showcase implementation, unless the user chooses to run validation first.
