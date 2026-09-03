# Spectra Science — Metadata Runtime API Draft

Status: **design draft grounded against current runtime; not implemented runtime**.

This document converts the semantic metadata field catalog into a minimal Python-facing runtime design that composes with current `DomainModule`, `DomainRegistry`, `DomainCatalog`, `VisualizationRegistry`, and unit contracts.

## Current runtime facts

Current source already provides authoritative runtime identity/state for:

```text
DomainModule.name/version/dependencies
DomainRegistry semantic types
DomainRegistry capabilities/provider/version
DomainCatalog probe-derived capability ownership
VisualizationRegistry semantic type -> Scene compiler
NumericalSolverRegistry implementation/method/execution metadata
Dimension / Unit / Quantity
```

The metadata layer must **supplement** these facts, not duplicate or override them.

## Non-goals

The first metadata runtime should not:

- replace `DomainRegistry`;
- replace `DomainCatalog`;
- replace `VisualizationRegistry`;
- maintain a second capability provider manifest;
- serialize Python callable validators;
- automatically generate every UI form;
- require annotating all 100+ domains immediately.

## Proposed module

```text
spectra/metadata.py
```

Start with one compact module. Split later only if the contract proves stable.

## Core descriptors

Conceptual API:

```python
@dataclass(frozen=True, slots=True)
class ParameterDescriptor:
    parameter_id: str
    label: str
    value_kind: str
    description: str = ""
    required: bool = True
    unit_dimension: Dimension | None = None
    preferred_units: tuple[Unit, ...] = ()
    choices: tuple[str, ...] = ()
    constraints: tuple[ConstraintDescriptor, ...] = ()
    group_id: str | None = None
    order: int = 0
    advanced: bool = False
    read_only: bool = False

@dataclass(frozen=True, slots=True)
class SemanticTypeDescriptor:
    type_id: str
    semantic_type: type[object]
    label: str
    description: str = ""
    category: str = "general"
    parameters: tuple[ParameterDescriptor, ...] = ()
    quantity_id: str | None = None
    serializer_id: str | None = None
    tags: tuple[str, ...] = ()

@dataclass(frozen=True, slots=True)
class ViewDescriptor:
    view_id: str
    source_type: type[object]
    label: str
    description: str = ""
    quantity_id: str | None = None
    unit_dimension: Dimension | None = None
    signed: bool | None = None
    cyclic: bool = False
    non_negative: bool = False
    preferred_color_kind: str | None = None
    tags: tuple[str, ...] = ()
```

The exact field vocabulary should follow `SEMANTIC_METADATA_FIELD_CATALOG.md`.

## MetadataRegistry

```python
@dataclass
class MetadataRegistry:
    semantic_types: dict[str, SemanticTypeDescriptor]
    semantic_type_ids: dict[type[object], str]
    views: dict[str, ViewDescriptor]

    def register_semantic_type(self, descriptor: SemanticTypeDescriptor) -> None: ...
    def register_view(self, descriptor: ViewDescriptor) -> None: ...
    def semantic_type(self, type_or_id: type[object] | str) -> SemanticTypeDescriptor: ...
    def views_for(self, value_or_type: object | type[object]) -> tuple[ViewDescriptor, ...]: ...
    def copy(self) -> "MetadataRegistry": ...
```

Duplicate stable IDs or duplicate Python-type bindings should fail.

A copy/snapshot operation is important because `DomainRegistry.add_domain()` is already transactional. Metadata registration should participate in the same rollback semantics once integrated.

## DomainRegistry integration

Preferred future extension:

```python
@dataclass
class DomainRegistry:
    ...
    metadata: MetadataRegistry = field(default_factory=MetadataRegistry)
```

The registry snapshot/restore path should copy/restore metadata alongside capabilities, numerical solvers, and visualization compilers.

This keeps one transaction boundary for a domain.

Conceptual helpers:

```python
def register_type_metadata(self, descriptor: SemanticTypeDescriptor) -> None: ...
def register_view_metadata(self, descriptor: ViewDescriptor) -> None: ...
```

A domain can then register:

```text
semantic Python type
capabilities
visualization compiler
metadata descriptor
```

within one atomic `register()` call.

## DomainModule contract

Do **not** expand the base `DomainModule` protocol with mandatory metadata properties in the first implementation.

Reason:

- 100+ current domains would need mechanical changes;
- metadata should be optional/additive initially;
- registration already offers a transactional hook.

Preferred pattern:

```python
class ExampleDomain:
    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type(...)
        registry.register_type_metadata(...)
        ...
```

Later a helper/base mixin may reduce repetition.

## Runtime facts vs descriptive metadata

Capability provider/version must always come from live registry state.

Do not store authoritative fields like:

```text
provider_domain
capability_version
```

in static metadata as independently maintained truth.

An inspection DTO may combine them at read time:

```python
@dataclass(frozen=True)
class CapabilityInspection:
    key: str
    version: int
    provider_domain: str | None
    description: str | None
    maturity: str | None
```

where provider/version come from `DomainRegistry`.

## Unit integration

Use real existing `Dimension` and `Unit` objects in in-process descriptors.

`Dimension` already represents SI base exponents and is immutable.

`Unit` already stores:

```text
name
symbol
dimension
scale_to_si
offset_to_si
```

Therefore metadata should not invent a second dimension-string parser for runtime use.

Persistent/project metadata later may encode a stable dimension/unit reference, but in-process validation can compare `Dimension` objects directly.

## Quantity metadata

A simple independent `QuantityDescriptor` may later map semantic `quantity_id` to:

```text
label
description
dimension
preferred units
signed/non-negative/cyclic semantics
```

This is useful for presentation.

The first implementation can avoid a global quantity registry until two or more views actually need shared quantity identity.

## View integration

`VisualizationRegistry` currently resolves by Python type/MRO and compiles a semantic object into `Scene`.

Do not modify that compiler dispatch just to add metadata.

Metadata query should be parallel inspection:

```python
scene = registry.compile_scene(value)
view_info = registry.metadata.views_for(value)
```

Later, explicit view semantic objects can carry their own `ViewDescriptor` registration.

## Presentation bridge

`ViewDescriptor` is the correct place for semantic presentation hints such as:

```text
quantity_id
signed
cyclic
non_negative
preferred_color_kind
```

The presentation layer may consume these facts through `PresentationContext`.

It must not inspect private field names or guess from class names.

Example:

```text
quantum phase view -> cyclic=True -> cyclic color policy
probability density -> non_negative=True -> sequential color policy
pressure delta -> signed=True -> diverging policy
```

## Introspection service

Avoid exposing mutable registries directly to product code.

Conceptual read-only service:

```python
class SpectraIntrospection:
    def __init__(self, registry: DomainRegistry): ...

    def domains(self) -> tuple[DomainInspection, ...]: ...
    def capabilities(self) -> tuple[CapabilityInspection, ...]: ...
    def semantic_types(self) -> tuple[SemanticTypeDescriptor, ...]: ...
    def views_for(self, value_or_type: object | type[object]) -> tuple[ViewDescriptor, ...]: ...
    def solver_roles(self) -> tuple[SolverRoleInspection, ...]: ...
```

This service joins live facts and descriptive metadata deterministically.

## Plugin interaction

Plugin domains use the same metadata registration path.

If plugin activation/probe fails, its metadata must roll back with the domain transaction.

A plugin manager may inspect the static plugin descriptor before activation, but scientific type/view metadata becomes authoritative only after successful domain registration.

## Auto-generated metadata caution

Python dataclass reflection can be used as a convenience for initial parameter names/defaults, but must not be authoritative for:

- units;
- scientific meaning;
- constraints;
- quantity identity;
- persistence IDs.

Explicit metadata wins over reflection.

## Minimal first showcase registration

After the pending runtime validation, annotate only a small cross-domain sample:

```text
MaxwellProblem3D
HeatConductionProblem3D
ReactionKineticsProblem
```

Then add view descriptors for representative existing view semantic objects.

This is enough to validate generic UI/AI inspection without touching every domain.

## Transactional requirements

When a domain registration fails after metadata registration:

```text
semantic types
capabilities
numerical solvers
visualization compilers
metadata
```

must all return to the pre-domain snapshot.

No orphan metadata entries may remain.

## Tests after implementation gate

- duplicate type ID fails;
- duplicate Python type binding fails;
- metadata participates in DomainRegistry rollback;
- `Dimension` constraints compare correctly;
- metadata query does not execute a solve;
- live capability provider/version overrides stale descriptive hints;
- VisualizationRegistry still compiles without metadata present;
- plugin metadata disappears on failed activation rollback;
- quantum cyclic view metadata drives cyclic presentation hint;
- generic inspection order deterministic.

## Success criterion

Metadata becomes a thin, optional, transactional descriptive layer around the existing engine—not a second engine. Current domain/capability/visualization/solver registries remain the source of operational truth while generic UI, AI, docs, and presentation gain enough machine-readable scientific context to scale to hundreds of modules.
