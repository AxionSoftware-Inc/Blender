# Spectra Science — Chat-Limit Handoff

**Date:** 2026-09-06 (Asia/Tashkent)  
**Repository:** `AxionSoftware-Inc/Blender`  
**Purpose:** canonical continuation document when the current ChatGPT conversation runs out of context.  

> This document is intentionally conservative. It separates **verified green milestones** from **implemented-but-not-yet-promoted work**. Do not call the current development stack green until the prescribed validation gates have passed.

---

## 1. Product identity

Spectra is no longer a Blender-centric addon. Its intended architecture is:

```text
scientific intent
→ domain semantics
→ reusable computation capabilities
→ numerical execution roles
→ semantic fields / trajectories / solutions
→ visualization compiler
→ renderer-neutral Scene + Timeline
→ presentation policy
→ presentation-enriched Scene
→ Scene.sample(t)
→ renderer backend
```

Blender is the first premium reference renderer/backend, not the scientific source of truth.

Core invariants:

- scientific meaning exists before renderer objects;
- domains depend on stable versioned capabilities, not private cross-domain implementations;
- high-level scientific code dispatches through stable numerical roles rather than hardcoded solvers;
- renderer-specific APIs (`bpy`, Geometry Nodes details, WebGPU handles, CUDA/Metal SDKs) do not leak into scientific domains;
- presentation may change display, framing, legends, color scales, typography, animation pacing, and quality, but it must not silently change scientific data, solver resolution, or numerical precision;
- scientific time and presentation/playback time are separate concepts;
- large repeated geometry must remain batched where the backend supports it;
- adding the 100th/500th scientific concept should not require engine or renderer rewrites.

---

## 2. Last trusted green baseline

The last fully verified local/native milestone before the later large numerical/experiments stack was:

**Commit:** `acb9e056326177fac49cc57b202ca80cca5090a7`

Verified there:

- `python -m compileall spectra` — PASS
- full `pytest` — **224 passed**
- initial failures — 0
- DomainCatalog — PASS
  - **106 unique deterministic domains**
  - **403 providers**
- numerical provenance — PASS
- 3D dynamics/fluid — PASS
- solid/thermal — PASS
- Maxwell/electrothermal — PASS
- chemistry/thermochemistry — PASS
- targeted Blender 5.2 smoke — PASS
  - elastodynamics deformed PointCloud
  - Maxwell E/B batched VectorGlyphSet
  - geometry updated at start/middle/end
  - object/datablock identity stable
  - no object-count leak
- root fixes required — none
- remaining blockers at that milestone — none

Earlier Blender checks also established:

- static scene smoke PASS;
- animated wave PASS;
- EM animation PASS;
- incremental identity PASS;
- cleanup/orphan handling PASS;
- 10k PointCloud batched into one Blender object;
- 10k VectorGlyphSet batched into one Blender object;
- 100/121-frame playback leak checks PASS.

**Benchmark warning:** exact 10k benchmark numbers conflict between historical notes and repository docs. Do not quote exact create/update milliseconds without revalidation. Safe claim: batched 10k paths were verified.

---

## 3. Implemented after the 224-test baseline — validation status

A large numerical and experiment architecture batch was implemented after the trusted baseline. It includes the following, but the entire later stack must be treated as **implemented / pending promotion** until full validation is rerun on current HEAD.

### 3.1 Solver interchangeability

Stable numerical role:

- `ode.first_order`

High-level dispatch:

- `ode.solve_first_order`

Reference implementations include:

- `rk4.reference`
- `heun.reference`
- `rk45.reference` (adaptive Dormand–Prince 5(4))

Registry behavior includes:

- multiple implementations per role;
- defaults;
- ordered policies;
- problem-aware selection;
- requirements matching;
- transactional rollback;
- explicit vs selected/tracked execution.

### 3.2 Execution metadata and policies

Key concepts include:

- `NumericalExecutionDescriptor`
- `NumericalSolverRequirements`
- `NumericalSolverImplementation`

Metadata covers:

- execution kind (`python`, `cpu`, `gpu`, `external`);
- backend;
- precision;
- device;
- in-place/batched flags;
- solver role;
- implementation ID;
- method/order/adaptive metadata;
- provider/tags/priority;
- problem compatibility.

### 3.3 Role dispatch propagation

Many scientific consumers were changed from concrete RK4 use to stable role dispatch, including:

- scalar/complex/coupled PDEs 1D/2D/3D;
- second-order scalar/vector PDEs;
- mechanics;
- particle dynamics;
- geodesics;
- field dynamics;
- chemistry kinetics;
- Maxwell 3D.

Goal: future native/GPU solver providers should be selected without rewriting science domains.

### 3.4 Numerical provenance

Tracked records include actual selected implementation metadata, start/end time, accepted steps, requested step hint, state size/tags, execution backend/device/precision, adaptive/fixed distinctions, and PDE MOL pipeline composition.

### 3.5 Reproducibility

`spectra/reproducibility.py` defines an environment snapshot carrying:

- domain versions;
- capability versions/providers;
- solver inventory/defaults;
- active solver policies;
- deterministic payload;
- SHA-256 fingerprint;
- deterministic round trip.

Policy changes are intended to change the fingerprint.

### 3.6 Experiments package

`spectra/domains/experiments/` includes architecture for:

- Cartesian parameter sweeps;
- deterministic cases/IDs;
- unit-aware metrics;
- failure policies;
- tracked sweeps;
- solver comparison;
- deterministic batching;
- objective ranking / best case / Pareto;
- fixed-step convergence studies and observed order;
- local central finite-difference sensitivity;
- weighted discrete uncertainty propagation;
- candidate-grid weighted least-squares calibration;
- renderer-neutral experiment views;
- `spectra.experiment` artifact v1;
- environment fingerprints;
- per-case numerical traces with multiple run records.

Fixed-step convergence APIs should not silently accept adaptive solver methodology.

### 3.7 Important tests added in this batch

Examples:

- `test_solver_interchangeability.py`
- `test_solver_policies.py`
- `test_adaptive_solver_selection.py`
- `test_reference_ode_solvers.py`
- `test_numerical_provenance.py`
- `test_convergence_experiments.py`
- `test_batched_experiments.py`
- `test_experiment_analysis.py`
- `test_experiment_sensitivity.py`
- `test_uncertainty_calibration.py`
- `test_reproducible_experiments.py`
- `test_reproducibility_policies.py`
- `test_experiment_artifacts.py`
- `test_experiment_tracing.py`
- `test_experiment_views.py`
- domain auto-discovery/catalog regressions.

Do not assume these are all passing on current HEAD until validation is run.

---

## 4. Renderer-neutral presentation architecture already specified

The repository now contains extensive design/spec documentation for the premium presentation layer. Key docs include:

- `docs/PREMIUM_PRESENTATION_SYSTEM.md`
- `docs/BLENDER_PREMIUM_PRESENTATION.md`
- `docs/MODULE_SDK.md`
- `docs/PLUGIN_PACKAGING.md`
- `docs/NAMING_CONVENTIONS.md`
- `docs/PROJECT_DOCUMENT_MODEL.md`
- `docs/PUBLIC_SDK_FACADE.md`
- `docs/PRODUCT_WORKFLOWS.md`
- `docs/SHOWCASE_SCENARIOS.md`
- `docs/POST_VALIDATION_IMPLEMENTATION_PLAN.md`
- `docs/DOMAIN_SYSTEM.md`
- `docs/NUMERICAL_PROVENANCE.md`

The intended presentation boundary is:

```text
base Scene + PresentationIntent
→ deterministic presentation composer
→ presentation-enriched Scene
→ renderer adapter
```

Presentation owns:

- camera/framing;
- background/theme;
- lighting intent;
- axes/grid;
- quantitative color scales;
- legends/colorbars;
- titles/subtitles/annotations;
- reveal/pacing;
- quality profiles;
- publication/presentation/cinematic presets.

Scientific domains own:

- quantities;
- formulas;
- units;
- physical semantics;
- computation;
- scientific view semantics.

Renderer backend owns native realization:

- materials/shaders;
- native camera/light objects;
- text realization;
- Geometry Nodes or equivalent batching mechanisms;
- render-engine-specific output.

---

## 5. Scene / quantitative presentation direction

Current architecture includes renderer-neutral visual attributes and quantitative color policy concepts. Important rules:

- scalar scientific values remain source attributes;
- `display_color` is derived presentation data, not a replacement for scientific values;
- quantitative surfaces/clouds should use one shared shader/material path rather than one material per value;
- signed scalar data should use symmetric/diverging policy when scientifically appropriate;
- phase is cyclic and should use a cyclic/phase palette;
- changing color policy must not recompute science;
- display decimation is presentation metadata, not solver decimation.

A targeted Blender quantitative smoke already exists:

- `examples/blender_quantitative_smoke.py`

It is intended to validate:

- native per-value color attribute creation;
- one material for many values;
- per-value alpha preservation;
- primitive opacity update;
- object/datablock/material identity preservation;
- cleanup.

This smoke must be rerun locally in Blender before promotion of the larger pending stack.

---

## 6. Canonical showcase layer

A dedicated `spectra/showcases/` layer exists so product/integration examples can compose existing science without becoming alternate solver/domain implementations.

Principle:

```text
existing domain semantics
+ existing computation capabilities
+ existing visualization compilers
+ presentation intent
= canonical showcase
```

Showcases must not fork scientific formulas or become alternate numerical engines.

---

## 7. Showcase #1 — Maxwell electromagnetic wave

Existing module:

- `spectra/showcases/maxwell_wave.py`

Public exports:

- `MaxwellWaveShowcaseConfig`
- `build_maxwell_wave_base_scene`
- `build_maxwell_wave_scene`

Design:

- canonical SI plane wave;
- propagation along +x;
- E and B orthogonal;
- E/B vector sets remain batched;
- trace polylines supplied for readable wave shape;
- B is displayed as `c·B` only for visual comparability with E;
- underlying magnetic field remains in Tesla;
- scientific timeline remains true SI nanoseconds;
- Blender/client playback duration is separate transport metadata;
- presentation reveal is deliberately disabled so second-scale presentation tracks do not corrupt nanosecond scientific time.

Targeted Blender smoke:

- `examples/blender_maxwell_showcase_smoke.py`

It is intended to verify:

- scientific duration remains SI;
- playback transport maps the short scientific interval into visible seconds;
- E/B remain batched;
- object/datablock identity is preserved over start/mid/end seek;
- cleanup succeeds.

A dedicated validation handoff already exists:

- `docs/MAXWELL_FLAGSHIP_VALIDATION_HANDOFF.md`

Treat Maxwell as a completed implementation checkpoint only after its local validation gate has been confirmed for the current development stack.

---

## 8. Showcase #2 — Electrostatic Field Laboratory

This was the active implementation immediately before this chat-limit handoff.

### 8.1 Scientific composition

The showcase deliberately reuses existing capabilities:

```text
PointChargeSource3D
→ conservative point-source deposition
→ electrostatic potential problem
→ generic 3D Poisson solve
→ scalar potential field V
→ electric field E = -∇V
→ scalar slice / vector field / field-line views
→ quantitative presentation
```

No new Coulomb solver or duplicate Poisson implementation was introduced.

Existing source/domain infrastructure used:

- `physics.potential_sources.3d`
- `physics.electrostatic_potential.3d`
- `physics.potential_fields.views3d`
- generic `field_dynamics` integral-curve bundle support.

### 8.2 Canonical scientific case

The intended canonical lab is a **dipole**:

- +q source on one side;
- −q source on the opposite side;
- z=0 potential slice;
- real electric potential scalar attribute in Volts;
- batched electric-field arrows;
- field lines seeded near the positive source;
- source markers and labels.

### 8.3 Presentation semantics

For potential:

- quantity ID: `electric_potential`;
- unit: `VOLT`;
- palette: `COOLWARM`;
- range mode: symmetric around 0 V;
- legend enabled.

Electric-field arrows keep semantic fixed color rather than stealing the signed potential color scale.

Vector length is a **display scale only**; it must not alter scientific E values.

The scene is static. Presentation reveal is disabled for this milestone so the static scientific/presentation identity path remains simple and backend-stable.

### 8.4 Files added/updated in this electrostatic milestone

Implementation and tests were added in the current development stack, including:

- `spectra/showcases/electrostatic_lab.py`
- `tests/test_electrostatic_lab_showcase.py`
- `examples/blender_electrostatic_showcase_smoke.py`
- public exports in `spectra/showcases/__init__.py`
- `docs/ELECTROSTATIC_LAB_VALIDATION_HANDOFF.md`

### 8.5 Important test invariants

The Python tests are intended to verify:

- potential Surface exists;
- source scalar attribute is real `electric_potential`;
- unit remains `VOLT`;
- dipole slice contains both negative and positive potential;
- signed range is approximately symmetric;
- E is one batched `VectorGlyphSet`;
- source markers exist at opposite positions;
- expected field-line bundle exists;
- presentation derives `display_color` without rewriting the scientific potential attribute;
- colorbar/legend is symmetric around zero;
- title/camera/axes are present;
- timeline remains static;
- invalid geometry config is rejected.

A key test design correction was made during source audit: field-line tests should **not** assert a concrete `steps + 1` point count because field-line integration dispatches through the stable solver role and may be adaptive/interchangeable. Tests should validate a meaningful curve, not hardcode RK4 output length.

### 8.6 Blender smoke intent

The electrostatic Blender smoke is intended to verify:

- potential Surface becomes one native mesh;
- native `FLOAT_COLOR` / point-domain quantitative color data exists;
- one quantitative material is used rather than material explosion;
- E vectors remain one batched Curve representation;
- field lines render as polylines;
- positive/negative source objects exist;
- object count remains bounded;
- cleanup removes the Spectra collection/resources.

### 8.7 Promotion status

**Status: implemented in the current development stack, not yet locally promoted to green in this conversation.**

The dedicated validation handoff must be followed before calling the electrostatic showcase verified.

---

## 9. Showcase #3 — Quantum wavepacket / Schrödinger audit status

Quantum was **audited but not yet fully implemented** when the user asked to write this handoff.

### 9.1 Existing reusable foundation

Relevant existing code includes:

- `spectra/domains/physics/quantum_spatial.py`
- `spectra/domains/physics/schrodinger2d.py`
- `spectra/domains/physics/schrodinger3d.py`
- complex PDE infrastructure;
- scalar Surface compiler;
- quantitative presentation/color palettes including `PHASE`.

`Schrodinger2DDomain` already supports:

- complex ψ samples on a 2D grid;
- mass as a dimension-safe quantity;
- optional energy potential field;
- fixed/periodic/zero-gradient boundary modes;
- normalization;
- probability mass computation;
- solution through the shared complex PDE / ODE dispatch stack.

`ComplexPDESolution2D.magnitude_squared_solution()` already yields `|ψ|²` scalar states.

### 9.2 Important gap discovered

The common complex view layer currently covers components such as:

- real;
- imaginary;
- magnitude;
- magnitude squared.

A common phase (`arg ψ`) view was not found during the audit.

**Do not create a new quantum solver just to show phase.**

The safe showcase-level approach is:

- preserve complex ψ as scientific source data;
- derive probability density `|ψ|²` for quantitative/scientific scalar display;
- derive phase with `atan2(Im ψ, Re ψ)` as a renderer-neutral **visual attribute**;
- use the cyclic `PHASE` palette;
- keep this derivation presentation/view-layer only unless a future reusable semantic phase capability is justified across domains.

### 9.3 Scale boundary discovered

A physically meaningful electron wavepacket is naturally nanometer-scale, but the generic Scene camera/backend defaults are display/meter-like.

Therefore the intended showcase should explicitly separate physical coordinates from display geometry:

- scientific grid remains in **meters**;
- display geometry may use an explicit mapping such as `1 nm → 1 display unit`;
- probability height should be a normalized display height, not a claim that probability density has length units;
- scalar attributes retain the physical probability-density values/units;
- no scientific solver input should be rescaled merely for camera convenience.

This is an important product invariant: **data scale is not display scale**.

### 9.4 Intended canonical quantum showcase

Recommended first case after continuation:

- 2D free-particle Gaussian wavepacket;
- non-zero mean momentum so phase structure is visible;
- small bounded grid and short bounded scientific time;
- `|ψ|²` represented as Surface height or one quantitative Surface;
- phase represented by a cyclic per-vertex `display_color`/phase visual attribute;
- physical coordinate → display-coordinate mapping explicit in config;
- optional probability normalization diagnostic at first/last state;
- timeline remains scientific time;
- client playback duration kept separate if scientific time is too short to watch directly.

Do not proceed to 3D volume rendering for the first quantum showcase; 2D provides a much better product-quality validation of complex-valued data, phase coloring, timeline updates, and scale separation with current primitives.

### 9.5 Quantum status

**Status at handoff: source audit complete enough to define implementation direction; runtime showcase code/tests/smoke not yet completed.**

---

## 10. Current recommended continuation order

When opening a new chat or handing work to another agent, continue in this order.

### Gate A — establish current repository state

First inspect:

```bash
git status
git log -1 --oneline
git pull
```

Record the exact current HEAD before making validation claims.

### Gate B — validate the pending development stack

Run:

```bash
python -m compileall spectra
pytest -q
```

Focus failures first on:

- auto-discovery/catalog;
- registry rollback;
- RK4/Heun/RK45 provider inventory and policy selection;
- fixed/adaptive provenance;
- PDE role dispatch;
- experiments (convergence/sensitivity/uncertainty/calibration/Pareto/artifacts/tracing/views);
- presentation/quantitative tests;
- Maxwell showcase tests;
- Electrostatic showcase tests.

Fix root causes. Do not rewrite tests merely to hide regressions unless the expectation is truly stale and the architectural contract changed intentionally.

### Gate C — targeted Blender validation

At minimum, on Blender 5.2:

- existing generic backend smoke;
- quantitative smoke;
- Maxwell showcase smoke;
- Electrostatic showcase smoke.

Check:

- batched geometry;
- native color attributes;
- material count;
- object/datablock identity where time/update paths apply;
- object-count stability;
- cleanup/orphans.

Do **not** recreate GitHub Actions. CI absence is intentional unless the user explicitly requests it.

### Gate D — promote new green checkpoint

Only after Gates B/C succeed, record:

- exact SHA;
- compileall result;
- full pytest count;
- initial failures and root-cause fixes;
- DomainCatalog unique domain/provider counts;
- solver inventory/default/policies;
- provenance checks;
- experiment checks;
- showcase checks;
- Blender smoke results;
- remaining blockers.

That SHA becomes the new trusted baseline.

### Then continue product work

1. Finish Showcase #3 Quantum 2D wavepacket.
2. Add its Python acceptance tests.
3. Add Blender 5.2 quantum smoke.
4. Add dedicated validation handoff.
5. Only then begin Showcase #4 Thermoelastic.
6. Follow with Showcase #5 Schwarzschild / black-hole geodesics.

Recommended first polished public suite remains:

- Electrostatic;
- Maxwell;
- Quantum;
- Thermoelastic;
- Black-hole geodesics.

CFD and reaction-diffusion should follow after numerical/performance maturity improves.

---

## 11. Scientific capability summary

Current architecture/foundation spans:

### Mathematics

- safe AST expressions;
- real/complex functions;
- scalar/vector fields 2D/3D, time-dependent fields;
- parametric curves/surfaces;
- derivative/integral/gradient/divergence/curl/Jacobian;
- probability/statistics/graph theory;
- real/complex linear algebra;
- eigensystems/operators;
- arbitrary-rank tensors;
- differential geometry, metrics, Christoffels, Riemann/Ricci/scalar curvature, geodesics.

### Relativity

- special-relativity events/intervals/proper time/four-velocity;
- Schwarzschild semantics;
- Einstein tensor through generic curvature foundation.

Not a full production GR simulator.

### PDE/numerics

- ODE first-order role and reference solvers;
- scalar PDE 1D/2D/3D method-of-lines;
- complex PDE 1D/2D/3D;
- coupled scalar PDE 3D;
- second-order scalar PDE 2D/3D;
- vector second-order PDE 3D;
- finite differences/grid operators;
- Poisson 2D/3D;
- wave 2D/3D;
- Schrödinger 1D/2D/3D;
- transport/advection-diffusion 3D;
- stability/integral diagnostics;
- sampled grids → continuous field adapters.

### Mechanics / particles

- particle trajectories;
- multi-particle systems;
- field-particle dynamics;
- Lorentz bridge.

### Fluids

- 3D kinematics;
- passive scalar transport;
- upwind convective term;
- incompressible Navier–Stokes 3D reference projection;
- pathlines/vector animation;
- kinetic energy/enstrophy/divergence;
- pressure/CFL diagnostics.

Not industrial CFD/RANS/LES/AMR/complex-mesh production CFD.

### Solids / thermal

- isotropic elasticity;
- strain/stress/von Mises/principal stresses;
- 3D elastodynamics;
- heat conduction 3D;
- typed heat sources;
- thermoelasticity;
- one-way thermoelastodynamics;
- thermal strain/stress.

Not production FEM/FEA with contact/plasticity/fracture/shells/nonlinear large-scale FEM.

### Electromagnetism

- electrostatics;
- generic potential fields;
- Maxwell 3D reference time-domain foundation;
- div diagnostics;
- field energy/Poynting;
- source semantics and continuity checks;
- particle coupling;
- electrothermal Joule heat.

Not production Yee-FDTD/PML/dispersive/RF solver.

### Quantum

- finite-dimensional state/observable basics;
- spatial wavefunctions;
- Schrödinger 1D/2D/3D;
- probability density/current;
- continuity-related diagnostics/foundation.

Not quantum chemistry/DFT/many-body.

### Chemistry

- reaction networks;
- mass-action kinetics;
- reaction-diffusion 3D;
- concentration fields/views;
- thermochemistry;
- chemistry → heat coupling.

### Acoustics/waves

- 3D wave/acoustic reference foundation.

### Multiphysics examples

- reaction → reaction heat → conduction → thermal strain/stress;
- current + E → Joule heat → temperature → thermoelastic response;
- charge deposition → Poisson → E → Lorentz trajectory;
- Maxwell → E/B → charged particle dynamics.

---

## 12. What Spectra still cannot honestly claim

Do not describe these as finished production capabilities:

- industrial CFD;
- production FEM/FEA;
- production Maxwell/FDTD/RF;
- quantum chemistry/DFT/many-body;
- validated general GPU numerical solver stack;
- polished standalone/WebGPU product;
- complete visual node graph/editor;
- mature project browser/collaboration system;
- huge simulations in the Python reference path;
- production-grade volume rendering for quantum/scalar fields;
- all canonical showcases verified on current HEAD.

The architecture is designed to make those possible later; architecture is not equivalent to validated implementation.

---

## 13. Repository documentation map for continuation

Before designing new architecture, read existing docs instead of duplicating concepts.

### Architecture / product

- `docs/SYSTEM_ARCHITECTURE_MAP.md`
- `docs/DOMAIN_SYSTEM.md`
- `docs/PRODUCT_WORKFLOWS.md`
- `docs/PROJECT_DOCUMENT_MODEL.md`
- `docs/PROJECT_STATE_MODEL.md`
- `docs/PUBLIC_SDK_FACADE.md`
- `docs/MODULE_SDK.md`
- `docs/PLUGIN_PACKAGING.md`
- `docs/NAMING_CONVENTIONS.md`

### Numerical execution

- `docs/NUMERICAL_PROVENANCE.md`
- `docs/NATIVE_NUMERICAL_BACKENDS.md`
- `docs/NUMERICAL_BUFFERS.md`
- `docs/NUMERICAL_BACKEND_VALIDATION.md`
- `docs/HIGH_PERFORMANCE_ROADMAP.md`
- `docs/NATIVE_CPU_IMPLEMENTATION_BLUEPRINT.md`

### Presentation / rendering

- `docs/PREMIUM_PRESENTATION_SYSTEM.md`
- `docs/BLENDER_PREMIUM_PRESENTATION.md`
- `docs/PRESENTATION_API_DRAFT.md`
- `docs/PRESENTATION_COMPOSER_PIPELINE.md`
- `docs/PRESENTATION_PRESET_DEFAULTS.md`
- `docs/COLOR_SCALE_ALGORITHMS.md`
- `docs/SCIENTIFIC_COLOR_POLICY.md`
- `docs/VISUAL_ATTRIBUTE_MODEL.md`
- `docs/VISUAL_DESIGN_SYSTEM.md`
- `docs/BLENDER_PREMIUM_ACCEPTANCE.md`

### Validation / showcases

- `docs/SHOWCASE_SCENARIOS.md`
- `docs/PREMIUM_SHOWCASE_ACCEPTANCE_DATA.md`
- `docs/MAXWELL_FLAGSHIP_VALIDATION_HANDOFF.md`
- `docs/ELECTROSTATIC_LAB_VALIDATION_HANDOFF.md`
- `docs/QUANTITATIVE_NATIVE_VALIDATION_HANDOFF.md`
- `docs/TEST_STRATEGY_AND_CHECKPOINTS.md`
- `docs/RELEASE_QUALIFICATION.md`

### Coordination

- `docs/MASTER_AGENT_HANDOFF.md`
- **this file:** `docs/CHAT_LIMIT_HANDOFF_2026-09-06.md`

---

## 14. Current work discipline

Use this checkpoint discipline from now on:

```text
foundational change
→ targeted tests
→ full pytest
→ Blender smoke if Scene/backend changed
→ record exact SHA + results
→ only then stack the next foundational block
```

Do not accumulate another large unvalidated architecture stack if it can be avoided.

For showcase work:

```text
reuse existing science
→ bounded canonical config
→ deterministic generic Scene
→ explicit presentation intent
→ Python acceptance tests
→ Blender smoke
→ dedicated validation handoff
→ promote only after local validation
```

For numerical provider work:

```text
stable role
→ provider implementation
→ selection requirements/policy
→ provenance
→ reference equivalence tests
→ full validation
```

---

## 15. Exact first action in the next chat

The next assistant/agent should **not** ask the user to restate the project history.

It should:

1. open this document;
2. inspect current `main` HEAD;
3. inspect `spectra/showcases/electrostatic_lab.py`, `tests/test_electrostatic_lab_showcase.py`, and `docs/ELECTROSTATIC_LAB_VALIDATION_HANDOFF.md` to confirm the electrostatic milestone files exist as expected;
4. inspect the current quantum foundation (`schrodinger2d.py`, complex PDE 2D, presentation/color-scale support);
5. if the user says validation is available, run the prescribed full validation first;
6. otherwise continue the Quantum 2D showcase in a bounded, renderer-neutral product layer without changing scientific solvers.

---

## 16. Status labels to use accurately

Use these exact mental labels:

- **VERIFIED GREEN:** only a commit for which compile/tests/native checks were actually run and reported.
- **IMPLEMENTED / PENDING VALIDATION:** code exists but promotion gate has not been completed.
- **SPECIFIED:** documentation/API direction exists but runtime implementation is incomplete.
- **AUDITED:** source paths/contracts were inspected and a safe implementation direction is known.
- **PLANNED:** idea/roadmap only.

At the time this handoff was written:

- old `acb9e056...` milestone — **VERIFIED GREEN**;
- large later numerical/experiments stack — **IMPLEMENTED / PENDING CURRENT-HEAD VALIDATION**;
- premium presentation architecture — mixture of **SPECIFIED** and partial runtime implementation in the later stack;
- Maxwell showcase — **IMPLEMENTED**, with dedicated validation path;
- Electrostatic showcase — **IMPLEMENTED / PENDING VALIDATION**;
- Quantum showcase — **AUDITED / NOT YET COMPLETED**.

---

## 17. User intent

The user wants Spectra to become a scalable, professional-grade scientific computation and visualization platform, not a pile of isolated demos. Architectural choices should favor reusable contracts, deterministic behavior, renderer independence, native performance paths, premium scientific visualization, and future extensibility rather than one-off shortcuts.

When enough context exists, proceed directly rather than repeatedly asking for confirmation.
