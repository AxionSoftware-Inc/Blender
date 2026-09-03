# Spectra Science — Public API Stability and Deprecation Policy

This document defines how Spectra should evolve public Python APIs, capability names, solver roles, plugin contracts, presentation policies, and persistent schemas without freezing internal development too early.

Spectra is currently pre-alpha, so not every import path is stable. The goal is to establish the rules before third-party modules and saved projects depend on accidental internals.

## API classes

Spectra interfaces should be classified conceptually as:

```text
internal
public_experimental
public_stable
persistent_schema
```

### Internal

Repository implementation detail.

Characteristics:

- may change without compatibility guarantees;
- external modules should not import it;
- not re-exported from curated SDK facades;
- file path itself is not a contract.

### Public experimental

Documented for advanced use but still subject to change.

Characteristics:

- changes should be announced in changelog/release notes;
- compatibility aliases may be provided when inexpensive;
- third-party modules should pin compatible Spectra versions.

### Public stable

Intended for external modules/products.

Characteristics:

- stable semantic meaning;
- deliberate versioning;
- breaking changes require a migration/deprecation path unless a major version policy explicitly allows otherwise.

### Persistent schema

Serialized format read by future versions.

Examples:

- `spectra.scene`;
- experiment artifacts;
- future `spectra.project`.

Persistent schemas require stronger backward-read discipline than ordinary Python convenience APIs.

## Curated public facade

The future `spectra.sdk` facade should expose only interfaces deliberately promoted to public use.

External module documentation should prefer:

```python
from spectra.sdk import DomainDependency, DomainRegistry
```

rather than arbitrary internal file paths.

Subject packages may also expose stable subject-specific facades such as:

```python
from spectra.domains.physics.maxwell import ...
```

only when intentionally documented as public.

## Capability names are APIs

A capability key is a dependency contract and must be treated as public once other domains/plugins depend on it.

Example:

```text
ode.solve_first_order
physics.potential_field3d
pde.laplacian_3d
```

Do not casually rename capability keys to improve aesthetics.

If a capability contract changes incompatibly:

- bump its capability version;
- allow consumers to declare `min_version`;
- preserve older provider contract when feasible during migration;
- document the semantic change.

## Domain names are identities

Domain names participate in:

- discovery;
- environment fingerprints;
- project/plugin requirements;
- diagnostics.

Renaming a domain is therefore not equivalent to renaming a Python class.

A domain rename should be treated as a migration with alias/compatibility handling where persistent references may exist.

## Solver roles

Stable solver roles represent semantic numerical contracts.

Example:

```text
ode.first_order
```

Implementation IDs may evolve more freely than roles, but persisted provenance must preserve the exact implementation used.

Do not create a new role merely because execution technology changed.

Bad:

```text
ode.first_order_cuda
```

Better:

```text
role: ode.first_order
implementation: cuda.rk45
```

## Method IDs

Method IDs describe numerical method identity/provenance.

Examples:

```text
rk4.fixed
rk45.dormand_prince
method-of-lines.scalar3d
```

They should remain stable for a defined algorithm/contract so historical experiment artifacts remain interpretable.

If the algorithm changes materially, use a new method ID or versioned descriptor rather than silently reusing an old identity.

## Presentation policy identifiers

Preset/policy IDs may be persisted in project documents.

Examples:

```text
analysis
publication
cinematic
scientific_studio
orthographic_analysis
```

Once persisted publicly, changes to meaning should be deliberate.

A preset may improve visually while preserving its broad semantic intent. A fundamental semantic change should use a new identifier/version.

## Deprecation lifecycle

For a stable public API, recommended lifecycle:

```text
active
  -> deprecated
  -> compatibility alias/adapter
  -> removed at documented major/breaking boundary
```

A deprecation should state:

- what is deprecated;
- replacement;
- why;
- first deprecated version;
- earliest removal boundary if known.

## Compatibility aliases

Aliases are appropriate when:

- name changed but semantics remain equivalent;
- capability moved behind a new facade;
- temporary migration reduces ecosystem breakage.

Aliases are not appropriate when old/new semantics differ enough to cause misleading behavior.

## Warnings

Public API deprecation warnings should be:

- specific;
- actionable;
- suppressible through normal Python warning mechanisms where appropriate;
- not emitted excessively inside hot numerical loops.

## Pre-alpha policy

Before the first intentionally stable SDK release:

- internal APIs may change quickly;
- design docs should mark future contracts clearly;
- external experimental users should pin versions/commits;
- new APIs should not be labeled stable merely because tests pass.

The maturity model in `CAPABILITY_MATURITY_MODEL.md` remains separate from API stability.

A reference solver may have a stable API while the solver itself remains scientific-reference maturity.

## Plugin compatibility

A plugin descriptor should eventually declare a supported Spectra API/version range.

Conceptually:

```text
spectra_api >= X, < Y
```

The loader should reject clearly incompatible plugins before registration side effects.

Do not rely on import exceptions as the primary compatibility mechanism.

## Feature detection

Plugins/products should prefer capability/feature detection over exact implementation inspection.

Good:

```text
require capability physics.potential_field3d >= 2
```

Avoid:

```text
if Spectra version string == ... then import private file ...
```

Version ranges are useful for package/API compatibility; capability versions are the better boundary for scientific functionality.

## Removal discipline

Before removing a stable capability/type/schema field, ask:

1. Is it referenced by built-in domains?
2. Could external plugins depend on it?
3. Could saved Scene/project/artifact files contain it?
4. Is there a compatibility adapter?
5. Is the replacement semantically equivalent?
6. Is the removal tied to an explicit breaking-version boundary?

## Documentation discipline

Public docs/examples define user expectations even when an API was not formally marked stable.

Before changing a documented example API, update:

- docs;
- sample extensions;
- migration notes;
- tests for compatibility where applicable.

## Source compatibility vs data compatibility

These are different.

### Source compatibility

Old Python/plugin code still runs.

### Data compatibility

Old saved Scene/project/experiment files still load.

Persistent scientific data often deserves a longer compatibility window than Python convenience APIs.

## Backend APIs

Backend interfaces may evolve internally, but Scene/presentation semantics should remain the public renderer boundary.

Do not expose Blender datablock structures as a stable Spectra scientific API.

## Native ABI

A future native numerical ABI should be versioned independently from high-level scientific capabilities.

Native provider loading must validate ABI compatibility before passing memory/buffer handles across the boundary.

Do not assume Python package version equality guarantees binary ABI compatibility.

## Success criterion

External developers should know which Spectra interfaces they may safely depend on, while core contributors remain free to refactor private implementation details without turning every internal file move into an ecosystem-breaking event.
