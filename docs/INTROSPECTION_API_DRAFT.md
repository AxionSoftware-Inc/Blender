# Spectra Science — Semantic Introspection API Draft

Status: **design draft, not implemented runtime**.

This document defines a concrete first API for exposing domains, capabilities, semantic types, solver roles, views, and constraints to generic UI, CLI, AI authoring, documentation, and plugin inspection.

## Goal

Spectra should not require a giant product switch statement such as:

```text
if domain == quantum: ...
elif domain == cfd: ...
elif domain == chemistry: ...
```

A generic product surface should be able to inspect what the loaded engine provides and build many workflows from structured metadata.

## First-scope metadata

The initial introspection layer should expose only stable descriptive metadata:

```text
DomainInfo
CapabilityInfo
SemanticTypeInfo
ParameterInfo
ViewInfo
SolverRoleInfo
SolverImplementationInfo
```

Do not attempt a full automatic form/schema language in the first implementation.

## DomainInfo

```python
@dataclass(frozen=True)
class DomainInfo:
    name: str
    version: str
    display_name: str | None = None
    summary: str | None = None
    tags: tuple[str, ...] = ()
    provides: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
```

The runtime source of truth for `provides` remains actual registration ownership, not duplicated handwritten manifests.

## CapabilityInfo

```python
@dataclass(frozen=True)
class CapabilityInfo:
    name: str
    version: int
    provider_domain: str
    kind: str | None = None
    summary: str | None = None
    maturity: str | None = None
    tags: tuple[str, ...] = ()
```

`kind` may classify contracts such as:

```text
semantic_type
constructor
solver
adapter
view
diagnostic
experiment
presentation
```

Classification is descriptive only. Capability behavior remains defined by the actual public contract.

## ParameterInfo

```python
@dataclass(frozen=True)
class ParameterInfo:
    name: str
    value_type: str
    required: bool = True
    unit_dimension: str | None = None
    default: object | None = None
    minimum: float | None = None
    maximum: float | None = None
    choices: tuple[str, ...] = ()
    summary: str | None = None
```

Do not encode arbitrary executable validators in introspection metadata.

The semantic constructor remains authoritative for validation.

## SemanticTypeInfo

```python
@dataclass(frozen=True)
class SemanticTypeInfo:
    type_id: str
    python_qualified_name: str
    domain_name: str
    display_name: str
    summary: str | None = None
    parameters: tuple[ParameterInfo, ...] = ()
    canonical_view_id: str | None = None
    tags: tuple[str, ...] = ()
```

Stable `type_id` should be separate from Python file layout.

Example:

```text
physics.electromagnetism.point_charge3d
```

rather than:

```text
spectra.domains.physics.electromagnetism.PointCharge
```

The Python qualified name may still be exposed for developer tools.

## ViewInfo

```python
@dataclass(frozen=True)
class ViewInfo:
    view_id: str
    source_type_id: str
    display_name: str
    summary: str | None = None
    parameters: tuple[ParameterInfo, ...] = ()
    output_kind: str = "scene"
    tags: tuple[str, ...] = ()
```

Examples:

```text
physics.vector_field3d.arrows
physics.vector_field3d.integral_curves
physics.quantum.wavefunction3d.probability_slice
physics.quantum.wavefunction3d.phase_slice
experiments.pareto.scatter
```

A view ID describes semantic visualization intent, not a renderer implementation.

## Solver introspection

```python
@dataclass(frozen=True)
class SolverRoleInfo:
    role: str
    display_name: str
    summary: str | None = None

@dataclass(frozen=True)
class SolverImplementationInfo:
    role: str
    implementation_id: str
    method_id: str
    execution_kind: str
    precision: str | None
    order: int | None
    adaptive: bool
    reference: bool
    priority: int
    tags: tuple[str, ...] = ()
```

This metadata should be derived from `NumericalSolverRegistry` records where possible.

## EngineInspector

Suggested facade:

```python
class EngineInspector:
    def __init__(self, registry: DomainRegistry): ...

    def domains(self) -> tuple[DomainInfo, ...]: ...
    def capabilities(self) -> tuple[CapabilityInfo, ...]: ...
    def capability(self, name: str) -> CapabilityInfo: ...
    def semantic_types(self) -> tuple[SemanticTypeInfo, ...]: ...
    def views_for(self, type_id: str) -> tuple[ViewInfo, ...]: ...
    def solver_roles(self) -> tuple[SolverRoleInfo, ...]: ...
    def solver_implementations(self, role: str) -> tuple[SolverImplementationInfo, ...]: ...
```

Results must be deterministically sorted.

Inspection must not mutate runtime state or trigger expensive solves.

## Metadata registration

Do not overload `DomainRegistry.register_semantic_type(...)` with dozens of unrelated arguments immediately.

A clean additive path is a metadata registry owned alongside domain runtime state.

Conceptual:

```python
registry.register_semantic_metadata(
    SemanticTypeInfo(...)
)
registry.register_view_metadata(
    ViewInfo(...)
)
```

Registration must participate in the same transaction/rollback semantics as domain capability/visualization registration.

A failed domain must not leave orphan metadata.

## Generic UI usage

A UI can use introspection to build:

- subject browser;
- searchable capability palette;
- parameter editor scaffolding;
- solver selector;
- available-view picker;
- plugin/domain inspector;
- maturity/status badges;
- unit hints;
- documentation links.

But generic UI metadata must never bypass semantic constructor validation.

## AI authoring usage

An AI authoring surface can request structured inventory:

```text
What semantic constructors exist?
Which parameters and units do they accept?
What capabilities are loaded?
Which views are valid for this result?
Which solver implementations support this role?
```

AI then emits explicit semantic/project commands.

The engine validates those commands normally.

Do not expose private function source or arbitrary executable plugin internals as authoring metadata.

## CLI usage

Potential commands:

```text
spectra inspect domains
spectra inspect capabilities
spectra inspect type physics.electromagnetism.point_charge3d
spectra inspect views physics.quantum.wavefunction3d
spectra inspect solvers ode.first_order
```

The CLI should consume `EngineInspector`, not duplicate discovery logic.

## Documentation generation

The same metadata can later generate reference pages:

```text
domain → capabilities → semantic types → parameters → views → solver roles
```

This avoids hand-maintaining large feature inventories as domain count grows.

## Maturity metadata

Use `CAPABILITY_MATURITY_MODEL.md` vocabulary.

Examples:

```text
reference
experimental
beta
production
```

Do not infer maturity from test count or provider name.

The owner/domain must declare status deliberately, and qualification tooling may validate the claim.

## Constraints

Introspection metadata must not become a second scientific schema that disagrees with runtime semantics.

Rules:

1. semantic constructors remain authoritative;
2. units/constraints in metadata are descriptive scaffolding and should be testable against the real API;
3. actual capability ownership comes from `provide()` registration;
4. actual solver inventory comes from `NumericalSolverRegistry`;
5. actual visualization compiler support comes from `VisualizationRegistry`;
6. metadata may enrich those records but not replace them.

## Transactionality

Domain registration transaction should include metadata state.

If a domain registers:

```text
capability A
semantic metadata B
view metadata C
```

and then fails, A/B/C must all roll back.

## Plugin interaction

Plugin metadata is visible only when the plugin/domain is active in the inspected environment.

A disabled plugin may appear in `PluginRegistry` inspection but its scientific semantic/capability metadata should not appear as active engine functionality.

## First implementation strategy

After the main runtime validation gate:

1. add minimal metadata records;
2. add a transaction-aware metadata registry;
3. derive `DomainInfo`/`CapabilityInfo` automatically from existing registry/catalog state;
4. manually annotate only a small set of semantic types/views as proof;
5. add `EngineInspector`;
6. use it in a small CLI/dev example before attempting automatic UI generation.

Recommended proof domains:

```text
mathematics function1d
physics mechanics particle problem
physics electromagnetism field
experiments sweep
```

## Tests

- deterministic ordering;
- capability info matches actual provider/version;
- failed domain metadata registration rolls back;
- disabled plugin metadata absent from active inspector;
- semantic type ID uniqueness;
- view source type must exist;
- solver inventory mirrors numerical registry;
- inspection performs no solve;
- metadata survives catalog load order differences;
- generic metadata never makes an invalid semantic constructor call valid.

## Success criterion

Adding a 500th domain should not require adding another hand-written UI branch merely to make the product aware that the domain, its capabilities, views, parameters, and solver choices exist.