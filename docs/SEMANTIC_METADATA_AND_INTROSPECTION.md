# Spectra Science — Semantic Metadata and Introspection

This document defines how Spectra should expose semantic metadata so generic UI, AI authoring, project serialization, documentation, diagnostics, and plugin tooling can understand scientific types/capabilities without hardcoding every domain.

## Goal

A scalable engine with hundreds of domains needs machine-readable descriptions of public semantic contracts.

Conceptual flow:

```text
semantic type / capability
        ↓
metadata/introspection
        ↓
UI forms / command palette / AI / docs / validation / plugin inspector
```

Metadata describes the contract; it does not replace the actual Python/semantic validation logic.

## Metadata categories

Useful metadata families:

```text
semantic type metadata
field/parameter metadata
capability metadata
domain metadata
view metadata
presentation metadata
solver-role metadata
diagnostic metadata
```

## Semantic type metadata

A public semantic type may expose conceptually:

```text
type_id
human label
description
category
maturity
fields/parameters
unit/frame semantics
serializable? yes/no
canonical/default view if any
related capabilities
```

Example:

```text
type_id: physics.maxwell.problem3d
label: Maxwell 3D Problem
category: electromagnetism
```

Do not use Python class `__name__` as the only stable identity for persistent/plugin/UI contracts.

## Parameter metadata

A field/parameter descriptor may contain:

```text
name
label
description
value kind
required/default
unit dimension
preferred display unit
range/constraints
choices
group/order
advanced flag
read-only/derived flag
```

Examples:

```text
mass
  dimension = MASS
  preferred display unit = kg
  min > 0

boundary
  choices = fixed, periodic, zero_gradient
```

Runtime constructors remain authoritative; metadata assists authoring and validation UX.

## Value kinds

Generic UI/AI may need broad kinds:

```text
number
quantity
boolean
string
enum
vector
matrix
field
resource reference
semantic object
collection
mapping
expression
```

Do not force every scientific object into primitive JSON form merely for UI convenience.

## Units

Metadata should specify expected dimension rather than one fixed unit when multiple units are valid.

Example:

```text
expected dimension: length
suggested units: m, cm, mm
```

The UI may accept `2 cm`; the semantic constructor can convert/validate.

## Constraints

Metadata can describe common constraints:

```text
positive
non-negative
finite
integer >= N
ordered interval
unique names
compatible shape
```

Complex scientific constraints still belong in semantic validation code.

Metadata must not pretend every validation rule is expressible as a simple range.

## Capability metadata

A capability descriptor may expose:

```text
capability key
version
provider domain
human description
input/output semantic contracts
maturity
side effects? none/renderer/external
```

This helps plugin inspectors and advanced tooling explain dependency chains.

Provider ownership remains derived from real registry registration.

## Domain metadata

A domain may expose:

```text
name
version
subject/category
description
maturity
dependencies
provided capabilities
public semantic types
views
optional plugin/package identity
```

Built-in auto-discovery should remain based on the domain contract, while metadata improves inspection/documentation.

## View metadata

Explicit scientific views should describe:

```text
view id
source semantic type
output meaning
required parameters
sampling/display controls
quantity/unit semantics
presentation hints
```

Example:

```text
quantum.probability_density.slice3d
  source = SchrodingerSolution3D
  component = probability density
  output quantity non-negative
  preferred color scale = sequential
```

Presentation hint is not a renderer shader configuration.

## Solver metadata

NumericalSolverRegistry already carries method/execution metadata.

Introspection should expose safely:

```text
role
implementation id
method id/family/order
adaptive
execution kind/backend/precision
priority/tags
problem compatibility description where representable
maturity/verification
```

Do not serialize callable compatibility predicates themselves into project files.

## Generic UI generation

With metadata, simple domains may get automatic editors:

```text
semantic constructor metadata
    -> form fields
    -> unit-aware inputs
    -> validation diagnostics
    -> construct immutable semantic object
```

Complex domains can still provide specialized UI components.

Generic UI should be an acceleration path, not a constraint that simplifies scientific semantics unnaturally.

## AI authoring

AI can use introspection to answer:

```text
What parameters does this problem require?
Which units are valid?
Which capabilities are available?
Which views can show this result?
Which solver implementations are compatible?
```

AI should call normal semantic/project APIs after choosing a command; metadata does not authorize bypassing validation.

## Command palette

Metadata can power discoverable actions:

```text
Create Maxwell problem
Add point charge source
Solve with recommended policy
Show electric field vectors
Run parameter sweep
Switch to publication presentation
```

Commands can be generated/composed from capability/view metadata where safe.

## Documentation generation

Public API docs may use metadata to generate consistent tables of:

- parameters;
- units;
- capability keys;
- maturity;
- views;
- dependencies.

Generated docs should supplement hand-written scientific explanations, not replace them.

## Plugin inspection

A plugin manager should be able to list installed plugin metadata without needing to understand its private implementation layout.

Potential inspection:

```text
plugin
  -> domains
  -> capabilities
  -> semantic types
  -> solver providers
  -> presentation presets/views
```

## Serialization

Persistent project formats should store stable semantic IDs and actual values, not entire introspection descriptors duplicated in every project.

The runtime resolves the current descriptor for editing/validation.

Where historical interpretation requires it, project/result metadata can preserve relevant contract version identifiers.

## Metadata versioning

Metadata schema itself should be versioned once it becomes a public/plugin contract.

Changing a label does not necessarily change scientific capability version.

Changing a semantic parameter meaning does.

## Localization

Stable machine IDs should be separate from human labels.

Example:

```text
parameter id: charge_density
label_en: Charge density
label_uz: ...
```

Do not use localized text as persistent semantic identity.

Localization can be added at product/metadata-resource layer later.

## Derived/read-only properties

Metadata may expose useful computed values:

```text
wave speed
Reynolds number
energy drift
result duration
```

These are not necessarily constructor inputs.

UI should distinguish editable parameters from derived diagnostics.

## Metadata ownership

Subject-specific metadata belongs near the semantic/domain contract.

Generic metadata infrastructure may live in a reusable engine/SDK layer.

Do not create one giant central catalog file containing hand-maintained descriptions of every scientific module.

## Introspection safety

Inspection should not execute expensive solves or arbitrary plugin code unnecessarily.

A plugin descriptor/domain may need loading to expose capabilities, but simply inspecting project metadata should not trigger scientific execution.

## Current vs future status

Some pieces already exist implicitly:

- DomainRegistry semantic types;
- capability/provider versions;
- numerical method/execution descriptors;
- domain names/versions;
- VisualizationRegistry registrations.

A unified semantic metadata layer is a design target, not current fully implemented runtime functionality.

## Success criterion

When Spectra has 500 modules, a generic product surface should be able to discover what a module provides, what inputs/units it expects, which views/solvers are available, and how mature the capability is without hardcoding 500 module-specific switch statements.
