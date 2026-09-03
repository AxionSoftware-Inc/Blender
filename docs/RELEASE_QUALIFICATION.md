# Spectra Science — Release Qualification Matrix

This document defines how a Spectra release or subsystem milestone should be qualified before being presented to users as dependable within a stated scope.

Release qualification is broader than "all tests passed." It combines scientific scope, software maturity, compatibility, lifecycle, documentation, and deployment behavior.

## Qualification dimensions

A release/subsystem should be evaluated across:

```text
scientific/model scope
API/schema compatibility
semantic/capability correctness
numerical correctness
renderer/backend correctness
project lifecycle
resource/memory safety
performance within target workload
security/trust behavior
documentation/maturity labeling
```

Not every subsystem needs every dimension, but missing dimensions should be explicit.

## Release types

Useful categories:

### Developer snapshot

- internal/advanced development;
- APIs may change;
- limited qualification;
- intended for continued engine work.

### Technical alpha

- major workflows function;
- reference/experimental maturity clearly labeled;
- compatibility still evolving;
- suitable for demos/technical users.

### Beta

- project lifecycle and compatibility substantially more stable;
- broader real-user validation;
- known limitations documented;
- upgrade/migration path expected.

### Production release within supported scope

- explicit supported models/backends/platforms;
- release qualification matrix green for that scope;
- robust failure/lifecycle behavior;
- compatibility policy active.

## Core engine gate

Required before a release depending on current semantic engine:

- compile/import checks;
- full plain-Python suite;
- DomainCatalog probe;
- capability version/dependency validation;
- transactional rollback tests;
- Scene serialization compatibility for supported versions;
- safe expression boundary tests;
- unit/coordinate regressions.

## Numerical platform gate

For solver-role/experiment platform:

- reference ODE solvers pass analytical cases;
- role selection/policy/fallback tests;
- fixed/adaptive provenance correct;
- high-level PDE/mechanics consumers use role dispatch;
- convergence framework behaves correctly;
- experiment sweeps/batching/failure recording;
- sensitivity/uncertainty/calibration/Pareto tests;
- artifact round-trip/integrity;
- reproducibility fingerprint/policy coverage.

## Scientific domain gate

Each promoted domain should document:

```text
model equations/scope
units/conventions
boundary/initial-condition assumptions
reference/analytical cases
known unsupported regimes
maturity level
```

A passing code suite does not justify broad claims beyond the implemented model.

## Blender backend gate

For a release claiming Blender support:

- supported Blender version range stated;
- embedded Python import works through supported packaging/launcher path;
- static primitive/material/light/camera smoke;
- timeline playback;
- incremental identity where promised;
- cleanup/ownership;
- dense batching;
- repeated-frame leak test;
- save/reload behavior when release claims it;
- presentation gates when premium presentation is included.

## Premium presentation gate

If release claims premium presentation:

- renderer-neutral presentation tests;
- quantitative color/legend integrity;
- deterministic resource IDs;
- canonical scenes;
- Blender premium acceptance gates;
- preset switching;
- accessibility/basic contrast review;
- display sampling does not alter solver resolution;
- publication/cinematic scope documented.

## Project format gate

If release claims project save/load:

- schema/version explicit;
- round-trip;
- historical fixtures for supported versions;
- unknown future version rejection;
- external resource handling;
- missing plugin/resource diagnostics;
- model/result/view/presentation invalidation behavior;
- stale result handling;
- no renderer-native file required as scientific truth.

## Plugin SDK gate

If external plugins are public:

- curated SDK facade documented;
- sample extension package works;
- compatibility range checked;
- plugin enable/disable;
- capability conflicts deterministic;
- registration rollback;
- broken/missing plugin does not break base engine;
- trust/security behavior documented;
- no automatic plugin install from project files.

## Native CPU/GPU provider gate

For each provider:

- provider/ABI compatibility;
- canonical reference parity;
- precision support tested;
- convergence/order where meaningful;
- problem compatibility;
- provenance/method/execution metadata;
- fallback policy;
- lifecycle/resource cleanup;
- performance crossover measured;
- unsupported workload diagnostics;
- no scientific-domain code forks required.

## Remote worker gate

If release claims remote/HPC execution:

- authenticated/authorized worker path;
- capability negotiation;
- resource staging;
- stale result revision protection;
- cancellation/failure semantics;
- result/provenance integrity;
- local/remote semantic parity;
- no secrets in project/provenance;
- approved plugin/provider policy.

## Data import gate

For each supported import family:

- malformed input rejection;
- unit/frame handling;
- missing-value policy;
- large resource behavior;
- safe parsing/trust boundary;
- semantic adapter tests;
- no arbitrary code execution from data.

## CLI/headless gate

If CLI/API is public:

- documented stable commands/APIs;
- structured diagnostics/output;
- deterministic exit behavior;
- plain scientific operations require no Blender;
- provenance emitted where promised;
- project/plugin security policies respected.

## Export gate

For claimed export targets:

- scientific data units/coordinates preserved;
- Scene export schema valid;
- image/video color/legend consistency;
- renderer/native export ownership metadata where applicable;
- overwrite/path behavior safe;
- report metadata/provenance correct;
- generated files not written into source repo by default.

## Security/trust gate

Minimum for broader distribution:

- project files treated as data;
- no silent plugin/native installation;
- no arbitrary code eval from project data;
- resource/path traversal protections where archives/resources exist;
- secrets excluded from project/provenance;
- remote fetch policy explicit;
- plugin/native trust model documented;
- structured diagnostics for blocked operations.

## Performance gate

A release should state target workload classes rather than universal performance claims.

Record representative:

```text
reference workloads
machine/device
setup/solve/transfer/materialization
Scene/renderer update
memory/VRAM where relevant
numerical error/parity
```

Performance regressions outside claimed workload scope need not block release, but should be visible.

## Documentation gate

Before release:

- README status current;
- docs index current;
- verified commit/test environment recorded;
- maturity labels accurate;
- reference solvers not described as industrial production solvers;
- design-only features not described as implemented;
- upgrade/migration notes for breaking changes;
- known limitations explicit.

## Platform matrix

A release should list what was actually qualified.

Conceptual table:

```text
Platform       Engine   Blender   Native CPU   GPU   CLI   Project
Windows        yes      5.2 LTS   ...          ...   ...   ...
Linux          ...      ...       ...          ...   ...   ...
macOS          ...      ...       ...          ...   ...   ...
```

Do not imply untested platforms from Python portability alone.

## Scientific reference matrix

Qualification can list canonical cases actually run:

```text
ODE exponential
harmonic oscillator
Poisson manufactured
Maxwell constant/current-driven
heat source
elastodynamic translation
quantum continuity
reaction kinetics
```

This is more informative than only reporting test count.

## Release report

Recommended release qualification record:

```text
release/version
commit
maturity
supported scope
platforms/environments
compile/test counts
native backend/provider results
schema compatibility range
canonical reference cases
performance reference measurements
known limitations
security/plugin policy
open blockers
```

## Blocking vs non-blocking issues

### Blocking examples

- scientific contract wrong;
- data corruption;
- unit conversion bug;
- provider silently changes precision/semantics;
- persistent schema cannot read documented supported files;
- resource leak severe enough to break normal supported workflow;
- untrusted project executes code unexpectedly.

### Potentially non-blocking with documentation

- unsupported advanced presentation effect;
- performance below target on out-of-scope XL workload;
- optional plugin unavailable;
- experimental feature known limitation outside supported scope.

## No false inheritance

A new commit/release does not automatically inherit a previous release's native qualification if relevant code changed.

Likewise, documentation-only commits need not invalidate runtime qualification when no executable behavior changed.

Qualification should consider the runtime delta.

## Current project status interpretation

The recorded `acb9e056...` baseline provides evidence for:

- plain engine suite at that milestone;
- DomainCatalog;
- Blender 5.2 native smoke/incremental behavior.

The current post-baseline numerical/experiment runtime batch still requires its next full local validation before a new green runtime qualification claim.

Subsequent documentation/spec commits are architecture preparation and do not by themselves create new runtime features.

## Success criterion

A Spectra release should make a precise statement of what is implemented, what was actually verified, on which platforms/backends/providers, and within what scientific/model scope—so users do not have to infer reliability from feature lists or test counts alone.
