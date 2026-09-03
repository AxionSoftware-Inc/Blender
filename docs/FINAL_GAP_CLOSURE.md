# Spectra Science — Final Gap Closure Before Consolidated Agent Patch

Status: **design/source-audit closure; no new executable runtime behavior**.

This document answers one question before the next consolidated agent task:

> Are there unresolved architecture/design gaps that should be settled before asking the local agent to implement/test the large patch?

The answer for the planned milestone is **no material unresolved architecture blocker remains**. Remaining unknowns are implementation/test findings, not missing system-level decisions.

## 1. Runtime truth — resolved

Verified baseline and pending executable batch are separated:

```text
verified: acb9e056...
224 passed
Blender 5.2 native smoke PASS

implemented/pending validation runtime ends at:
00b5403...

post-00b5403 block:
README/docs/source-audit only
```

No later design document should be reported as implemented runtime until the consolidated patch lands and validates.

## 2. Scientific engine boundary — resolved

Fixed:

```text
scientific semantics/capabilities
-> numerical roles
-> semantic results
-> base Scene
-> presentation
-> backend
```

Renderer backends do not own science.

Scientific domains do not name concrete execution implementations when a stable numerical role exists.

No additional central-engine abstraction is required before the next patch.

## 3. Domain/plugin scalability — resolved

Built-ins remain auto-discovered through real domain registration/probe behavior.

External plugins contribute normal domain factories and reuse:

```text
DomainCatalog.from_factories(...)
DomainRegistry
```

No second plugin scientific registry is needed.

First plugin runtime intentionally does not require hot-unload from a mutated live registry.

## 4. Solver interchangeability — resolved

Current runtime already owns:

```text
NumericalSolverRegistry
ode.first_order
requirements
problem predicates
policies/fallback
execution metadata
provenance
```

Native CPU will be a provider, not a new solver architecture.

Real GPU execution remains a later provider implementation, not an architecture prerequisite for the next milestone.

## 5. Premium presentation boundary — resolved

Premium presentation is a renderer-neutral enrichment pass over a base Scene.

Fixed decisions:

- `VisualizationRegistry` remains semantic -> base Scene;
- presentation uses deterministic `presentation.*` resources;
- input Scene remains immutable;
- scientific primitive IDs remain stable;
- camera fitting uses `scene_local_bounds()`;
- presentation resources do not contaminate scientific bounds;
- existing scientific animation track ownership wins;
- no generic track blending in first version;
- existing `BackendCapabilities` is the only backend capability source of truth;
- `BackendSession` is the generic product-facing backend lifecycle.

No additional presentation architecture decision is required before implementation.

## 6. Presets/design language — resolved for first milestone

The initial deterministic presets are fixed in:

```text
analysis
publication
presentation
cinematic
dark_lab
```

Exact defaults are documented in `PRESENTATION_PRESET_DEFAULTS.md`.

They are first implementation values, not eternal visual-brand constants. Future visual tuning can change intentionally with versioned preset behavior where persistence requires it.

## 7. Camera math — resolved

Perspective/orthographic fitting, padding, clipping, deterministic view/up fallback, empty/degenerate Scene behavior, and non-default Scene-frame handling are documented.

Implementation should not improvise backend-specific focal-length math in generic presentation code.

## 8. Quantitative color semantics — resolved

Engine/presentation owns:

```text
quantity
unit conversion
data range
scale mode
palette identity
normalization
legend semantics
```

Backend owns only native realization.

Initial normalization policy supports explicit/data/symmetric/robust-percentile use cases and sequential/diverging/cyclic/categorical semantics as documented.

No Blender-side re-derivation of scientific scalar meaning is permitted.

## 9. Dense visual attributes — resolved at contract level

The major current Scene limitation was identified:

```text
Surface has one primitive color and no generic named scalar/vertex attribute path
```

The chosen solution is a generic immutable visual-attribute contract with initial associations:

```text
vertex
instance
primitive
```

and kinds:

```text
scalar
vec2
vec3
color
```

This is intentionally generic rather than `temperature_values`, `stress_values`, etc.

Actual runtime shape may be adjusted while implementing if tests reveal a simpler equivalent contract, but renderer-neutral named attributes remain the architectural requirement.

## 10. Scene persistence — resolved

Current Scene writer is v4 with historical v1-v4 read compatibility.

Visual attributes justify deliberate Scene v5.

Requirements are fixed:

- preserve v1-v4 reads;
- v4 without attributes maps naturally to empty/default attributes;
- v5 round-trips attributes;
- validation catches kind/association/length errors;
- no silent destructive downgrade;
- do not bundle unrelated world/background schema changes merely because version is being bumped.

## 11. Blender premium path — resolved

Existing backend remains authoritative:

```text
backend.py
incremental.py
timeline.py
```

No parallel premium Blender backend.

Implementation order is fixed:

```text
presented Scene native smoke
-> camera/light/text incremental paths
-> material lifecycle/ownership
-> generic visual attributes
-> Geometry Nodes/dense instancing where justified
-> optional compositor/polish later
```

Current high-cardinality material-slot color behavior is not considered the final continuous scientific colormap solution.

## 12. Project model/provenance — resolved

Project v1 stores scientific/product intent and references, not Blender pointers or huge solver histories.

Project selection intent is distinct from captured execution provenance.

Reuse existing:

```text
ScientificEnvironmentSnapshot
SolverPolicyRecord
NumericalRunArtifact
ExperimentArtifact
```

Do not invent duplicate project provenance classes for the same meaning.

## 13. SDK/public API — resolved

Do not turn root `spectra` into a giant namespace.

Use curated `spectra.sdk.*` facade modules that re-export existing authoritative runtime objects.

The facade stabilizes extension imports without cloning implementation types.

## 14. Semantic metadata/introspection — resolved

Metadata is additive/optional initially.

It does not replace:

- constructor validation;
- DomainRegistry provider/version truth;
- numerical method/execution descriptors;
- VisualizationRegistry compiler registrations.

No giant central hand-written metadata manifest for 500 domains.

## 15. Diagnostics — resolved for first implementation

Structured categories/codes are documented.

The next patch should add subsystem-aware diagnostics where useful, but it should not derail into a repository-wide exception hierarchy rewrite.

Scientific/backend/plugin/serialization failures remain distinguishable.

## 16. Security/trust — resolved for milestone

Fixed rules:

- Scene/project/artifact JSON parsing does not execute arbitrary code;
- project requirements do not install/enable plugins;
- plugin/native provider is executable trust boundary;
- restricted expression safety remains intact;
- scientific data files are data, not plugin code.

Marketplace/signing/sandboxing are later product concerns.

## 17. Native CPU provider — resolved at implementation level

First provider target:

```text
role: ode.first_order
implementation: rk4.native_cpu
semantic input/output: FirstOrderSystem -> ODESolution
precision: float64
execution kind: cpu
```

It exists to prove execution replacement and provider packaging, not to claim maximum speed.

The exact low-level bridge may be CPython C extension or clean C ABI/ctypes depending on local tooling. This choice is an implementation detail, not an unresolved engine architecture decision.

## 18. Deliberately deferred — not defects in this milestone

The following are explicitly outside the consolidated patch and must not be treated as missing architecture work that blocks it:

```text
real CUDA/GPU solver implementation
industrial CFD/FEA/FDTD production solvers
full volumetric rendering
standalone/WebGPU UI product
remote/HPC runtime
collaboration server
plugin marketplace/installer
advanced screen-space layout engine
full reporting designer
production cloud services
```

Their architectural boundaries are documented sufficiently to avoid contaminating current work.

## 19. Remaining uncertainty — implementation/test only

The remaining unknowns can only be resolved by executing the consolidated patch:

- whether the pending numerical/experiments batch is fully green on the local machine;
- exact new pytest/domain/provider counts;
- any import/circular dependency exposed by real runtime implementation;
- exact Scene v5 API ergonomics after concrete tests;
- Blender native attribute/Geometry Nodes details under Blender 5.2;
- local native compiler/toolchain availability;
- measured native CPU parity/performance.

These are not reasons for more architecture documents before implementation.

## 20. Single source for next agent

The next agent should use:

```text
docs/MASTER_AGENT_HANDOFF.md
```

as the primary execution brief.

Supporting subsystem docs should be opened only as referenced by that handoff.

## Final conclusion

The preparation phase is complete enough for the planned milestone.

Further docs-only design work before local execution has sharply diminishing value. The next useful evidence must come from:

```text
validation
implementation
plain-Python tests
Scene/schema tests
Blender native smoke
native CPU parity
```

not from introducing more parallel concepts.
