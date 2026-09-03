# Spectra Science — Semantic Metadata Field Catalog

Status: **design catalog, not implemented runtime**.

This document defines a concrete field vocabulary for future semantic introspection so UI, AI authoring, plugins, project tooling, and docs do not invent incompatible metadata shapes independently.

## Principle

Metadata is descriptive. Runtime constructors, domain registration, units, capability providers, and solver registries remain authoritative.

The metadata layer should expose stable machine IDs and human-oriented descriptions without duplicating scientific execution logic.

## SemanticTypeDescriptor

Recommended fields:

```text
type_id                 required stable machine ID
python_type             runtime type reference, not persisted directly
label                   human-facing default label
description             concise scientific meaning
category                broad subject/category
maturity                capability maturity classification
parameters              ordered ParameterDescriptor tuple
derived_fields          ordered DerivedFieldDescriptor tuple
canonical_unit_context  optional
serializable            bool
serializer_id           optional stable serializer key
capabilities             related capability keys
views                    compatible/default view IDs
tags                     stable machine tags
```

Example:

```text
type_id = physics.maxwell.problem3d
category = electromagnetism
```

## ParameterDescriptor

Recommended fields:

```text
parameter_id            stable machine field ID
label                   human-facing label
description             meaning/assumptions
value_kind              generic authoring kind
required                bool
default                  explicit default or sentinel
unit_dimension          optional Dimension
preferred_unit_ids      optional tuple
constraints             tuple of ConstraintDescriptor
choices                 tuple of ChoiceDescriptor
semantic_type_id        for nested semantic object
resource_kind           optional external-resource category
collection_item         optional nested descriptor
group_id                UI/docs grouping
order                   deterministic display order
advanced                bool
read_only               bool
deprecated              bool
deprecation_message     optional
```

Parameter identity is never the localized label.

## ValueKind vocabulary

Initial generic values:

```text
number
integer
quantity
boolean
string
enum
vec2
vec3
matrix
complex
expression
field
resource_ref
semantic_object
collection
mapping
callable_runtime_only
```

`callable_runtime_only` explicitly communicates that a value cannot be persistently reconstructed from ordinary metadata alone.

## ConstraintDescriptor

Common machine-readable constraints:

```text
finite
positive
non_negative
non_zero
minimum
maximum
exclusive_minimum
exclusive_maximum
integer_minimum
integer_maximum
length
min_length
max_length
unique_items
ordered_pair
unit_dimension
shape
```

Fields:

```text
constraint_id
kind
value/parameters
message
severity
```

Complex domain validation remains runtime code and may expose only a descriptive validation note rather than pretending to fit this vocabulary.

## ChoiceDescriptor

For enum-like authoring:

```text
value
label
description
maturity/availability optional
```

Persistent value is the stable machine value, not the label.

## DerivedFieldDescriptor

For read-only values such as Reynolds number, wave speed, energy drift, CFL, or duration:

```text
field_id
label
description
value_kind
unit_dimension
preferred_unit_ids
source_capability optional
expensive bool
```

`expensive=True` indicates inspection should not compute the value automatically.

## CapabilityDescriptor

Recommended fields:

```text
capability_key
version
provider_domain
label
description
input_type_ids
output_type_ids
maturity
pure bool
side_effect_kind        none | renderer | filesystem | remote | external
solver_role optional
related_views
tags
```

Provider/version fields must be generated or reconciled with actual `DomainRegistry` state rather than maintained as a second source of truth.

## DomainDescriptor metadata extension

Current `DomainCatalog.DomainDescriptor` already has:

```text
name
factory
provides
tags
```

Future metadata should supplement rather than replace actual probe-derived provider data.

Suggested descriptive fields conceptually:

```text
label
description
subject
maturity
package/plugin identity
public type IDs
default view IDs
```

Do not hand-maintain `provides` in metadata when the current catalog can derive it through probe registration.

## ViewDescriptor

Recommended fields:

```text
view_id
label
description
source_type_ids
result_quantity_id optional
result_unit_dimension optional
signed optional
cyclic bool
non_negative bool
parameters
preferred_color_kind optional
preferred_presentation_preset optional
display_cost_hint optional
```

This is the bridge between scientific visualization semantics and presentation hints.

Example:

```text
view_id = quantum.wavefunction.phase_slice3d
cyclic = true
preferred_color_kind = cyclic
```

No Blender shader/node names belong here.

## QuantityDescriptor

For presentation/legend consistency:

```text
quantity_id
label
description
dimension
preferred_units
signed
non_negative
cyclic
canonical_reference optional
```

Examples:

```text
temperature
pressure
pressure_delta
velocity_magnitude
electric_potential
probability_density
phase
von_mises_stress
```

A `quantity_id` is semantic identity, not merely a display title.

## SolverRoleDescriptor

The runtime already owns numerical implementation metadata. Introspection should expose a safe descriptive view:

```text
role
label
description
problem_type_ids
solution_type_ids
recommended_policy optional
```

For each actual implementation, expose from runtime:

```text
implementation_id
method_id/family/order
adaptive
execution kind/backend/precision
provider domain
priority/tags
reference implementation flag
```

Do not persist Python predicates/callables.

## PresentationPresetDescriptor

When presentation presets become runtime:

```text
preset_id
label
description
maturity
intended_use
accessibility notes
supports_animation
```

Resolved policy data should remain separate from descriptive metadata.

## ResourceDescriptor

For imported datasets/resources:

```text
resource_kind
label
description
format_ids
unit expectations
coordinate expectations
lazy_supported
remote_supported
```

Actual URI/checksum/state belongs in project/resource runtime, not static metadata.

## Localization

All machine identity fields remain untranslated.

Human-facing strings may resolve through localization keys later:

```text
label_key
description_key
```

The first runtime may carry default English strings directly, but should not persist them as identity.

## Deterministic ordering

Metadata collections should have explicit stable ordering rules:

```text
parameters -> order then parameter_id
choices -> declared semantic order
capabilities -> capability key
views -> view_id
tags -> sorted
```

This helps generic UI, generated docs, snapshots, and plugin comparisons.

## Metadata IDs

Recommended patterns:

```text
type:       physics.maxwell.problem3d
parameter:  electric_field
quantity:   physics.temperature
view:       physics.temperature.slice3d
preset:     presentation.publication
resource:   data.structured_grid3d
```

Do not embed Python module paths unless they are intentionally the stable public identity.

## Runtime reconciliation

A future introspection registry should merge static descriptive metadata with live runtime facts.

Example:

```text
static description says capability X belongs to subject Y
live DomainRegistry says capability X provider/version = actual current provider
```

If these conflict, live registry facts win and a metadata diagnostic should surface the mismatch.

## Minimal first implementation scope

After validation, do not attempt the full catalog at once.

Recommended first slice:

1. `ParameterDescriptor`;
2. `SemanticTypeDescriptor`;
3. `ViewDescriptor`;
4. small `MetadataRegistry`;
5. register metadata for 2–3 showcase types;
6. generic inspection only;
7. no automatic UI generation yet.

This proves the contract before annotating 100+ domains.

## Initial showcase metadata targets

Use types from multiple scientific families:

```text
MaxwellProblem3D
HeatConductionProblem3D
ReactionKineticsProblem
```

and representative views:

```text
Maxwell E/B vector view
Temperature scalar slice
Experiment metric/convergence view
```

This tests vectors, scalar fields, units, enum/boundary choices, quantities, and experiment semantics.

## Tests after implementation gate

- duplicate type IDs rejected;
- duplicate parameter IDs rejected;
- deterministic parameter ordering;
- unit dimensions preserved;
- localized label does not affect identity;
- capability live provider/version reconciled correctly;
- inspection does not solve a problem;
- callable/runtime-only field marked non-persistable;
- view quantity metadata correctly drives color-policy hints;
- plugin metadata can be inspected without hardcoded core switch statements.

## Success criterion

A product surface should be able to inspect a previously unknown module and answer:

```text
What is this semantic type?
What inputs does it need?
Which units are valid?
Which capabilities solve/transform it?
Which views display it?
What quantity does the view represent?
Which solver implementations are available?
How mature/verified is each piece?
```

without embedding that module's private implementation logic into the UI or AI layer.
