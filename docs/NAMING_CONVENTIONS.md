# Spectra Science — Naming Conventions

This document defines stable naming rules for domains, capabilities, semantic types, numerical solver roles/implementations, views, presentation policies, and backend identifiers.

Consistent names are infrastructure. With hundreds of modules/providers, naming must support discovery, dependency reasoning, debugging, and third-party extensions.

## General principles

Names should be:

- stable across implementation refactors;
- semantic rather than renderer/device-specific;
- deterministic;
- lowercase for registry keys;
- explicit about dimensionality only when the contract is dimension-specific;
- explicit about representation only when representation is part of the public contract;
- free from release/project-management words such as `new`, `v2_new`, `final`, `temp`.

## Domain names

Use lowercase dotted namespaces.

Examples:

```text
mathematics
mathematics.field_slices3d
partial_differential_equations.3d
physics.elastodynamics.3d
physics.electromagnetism.maxwell3d
chemistry.reaction_diffusion.3d
experiments.sensitivity
```

### Rules

- A domain name identifies a capability-owning module, not a Python file name.
- Prefer scientific subject hierarchy.
- Do not include renderer names in scientific domains.
- Do not include solver backend technology in scientific domains unless the domain is intentionally a numerical provider.

Good:

```text
physics.optics.geometric
```

Bad:

```text
blender_optics
optics_cuda
```

A numerical provider domain may intentionally be implementation-oriented, for example conceptually:

```text
numerics.native_cpu.ode
numerics.cuda.ode
```

because implementation technology is the purpose of that provider.

## Capability keys

Capability keys are public dependency contracts.

Preferred structure:

```text
<subject>.<concept>[.<operation>][.<dimension>]
```

Examples:

```text
mathematics.vector_field3d
pde.laplacian_3d
pde.solve_method_of_lines_3d
physics.mechanics.trajectory
physics.potential_fields.field_lines3d
experiments.run_sweep
experiments.local_sensitivity
```

### Operation verbs

Use stable verbs where meaningful:

```text
solve
compute
evaluate
integrate
compile
sample
create
convert
rank
trace
```

Avoid vague verbs such as:

```text
do
process
handle
run_stuff
```

`run_*` is acceptable for experiment/study orchestration where running a study is the semantic operation.

## Capability nouns vs functions

A capability may expose a semantic type or a callable.

Semantic type:

```text
physics.potential_field3d
experiments.result
pde.scalar_problem3d
```

Operation:

```text
physics.potential_energy.compute_history
experiments.run_sweep
pde.solve_method_of_lines_3d
```

If downstream domains depend on a semantic type contract, publish it explicitly as a capability.

## Dimensional suffixes

Existing code uses both forms such as:

```text
vector_field3d
solve3d
problem3d
```

Keep existing public keys stable.

For new keys, choose one locally consistent structure and avoid redundant dimensions when the parent namespace already makes them unambiguous.

Examples:

```text
physics.elastodynamics.problem3d
physics.elastodynamics.solve3d
```

are reasonable because the domain may later have 2D variants.

Do not rename stable public keys merely for stylistic consistency without a migration strategy.

## Versioning is not naming

Do not encode capability version in the key:

Bad:

```text
pde.solve3d_v2
physics.field_new
```

Use registry capability versions:

```text
registry.provide("pde.solve3d", solve, version=2)
```

Only create a new key when the semantic contract is genuinely different, not merely newer.

## Semantic Python class names

Use descriptive PascalCase names.

Examples:

```text
PotentialField3D
ScalarPDEProblem3D
ParticleEnergyHistory
ReactionNetwork
NumericalSolverPolicy
```

Avoid renderer/backend names in scientific semantic classes.

A Blender-specific class belongs in the Blender backend package.

## Domain class names

Built-in auto-discovery expects discoverable zero-argument classes ending in `Domain`.

Examples:

```text
MechanicsDomain
PotentialFields3DDomain
ExperimentViewsDomain
```

Do not use `Domain` suffix on unrelated helper classes because it may accidentally enter discovery if it otherwise matches the contract.

## Numerical solver role names

A numerical solver role describes a stable computational job.

Examples:

```text
ode.first_order
```

Future examples might include:

```text
linear.solve_sparse
poisson.3d
optimization.continuous
```

The role should not encode implementation technology.

Good:

```text
ode.first_order
```

Bad:

```text
ode.cuda
ode.rk4
```

RK4 is a method/implementation choice, not the stable job.

## Numerical implementation IDs

Implementation IDs distinguish loaded implementations of one role.

Recommended structure:

```text
<method-or-family>.<provider-or-execution-qualifier>
```

Current examples:

```text
rk4.reference
heun.reference
rk45.reference
```

Future examples:

```text
rk4.native_cpu
rk45.native_cpu
rk4.cuda
rk45.webgpu
```

Implementation IDs must be unique within their role.

Do not encode device instance names such as `rtx_3060` in the implementation ID. Device belongs in execution metadata.

## Numerical method IDs

Method IDs identify the actual algorithm/pipeline, independent of selected hardware.

Examples:

```text
rk4.fixed
heun.fixed
rk45.dormand_prince
method-of-lines.scalar3d
```

Execution metadata identifies Python/native/GPU realization.

A native CPU RK4 may use the same mathematical method family/order while having a different implementation ID and execution backend.

## Execution backend IDs

Use stable software/runtime identifiers, not human marketing strings.

Examples conceptually:

```text
spectra.reference
spectra.native_cpu
spectra.cuda
spectra.webgpu
```

Device details such as GPU model belong in runtime/device metadata.

## View semantic names

Explicit view semantics should say what scientific representation is being displayed.

Examples:

```text
ScalarFieldSliceSurface3D
ComplexFieldSliceView3D
MetricSeriesView2D
ConvergenceView2D
```

Capability keys may follow:

```text
mathematics.scalar_field_slice_surface3d
experiments.metric_series_view2d
```

Avoid naming views after renderer techniques unless the view contract itself is renderer-specific.

Bad scientific view name:

```text
BlenderQuantumGlow
```

Good:

```text
QuantumProbabilityDensitySlice3D
```

## Presentation preset IDs

Presentation preset IDs describe communication intent rather than renderer settings.

Recommended built-ins:

```text
analysis
publication
presentation
cinematic
dark_lab
```

Do not name generic presets:

```text
cycles_premium
blender_dark
```

Renderer-specific profile names may exist separately inside backend configuration.

## Presentation resource IDs

Presentation-added Scene primitive IDs should use deterministic namespaces conceptually like:

```text
presentation.camera.primary
presentation.legend.temperature
presentation.axes.world
presentation.annotation.time
presentation.light.key
```

Scientific primitive IDs should remain stable when presentation styling changes.

## Backend IDs

Backend IDs should name renderer/execution adapters cleanly:

```text
memory
blender
webgpu
```

Implementation variants may be separate configuration/profile metadata rather than contaminating scientific keys.

## Experiment metric names

Metric names should state the measured quantity/diagnostic clearly:

```text
absolute_error
relative_error
peak_temperature
max_divergence
kinetic_energy
runtime_seconds
```

Units belong in `MetricSpec`/`MetricValue`, not the metric string.

Avoid:

```text
peak_temperature_celsius
runtime_ms_gpu
```

unless the unit/execution qualifier is genuinely part of the semantic metric contract. Normally it should be metadata.

## Parameter names

Experiment parameters should match scientific model terminology.

Good:

```text
diffusivity
young_modulus
source_strength
reynolds_number
```

Use units/Quantity values rather than encoding units in parameter names when possible.

## Plugin IDs

Third-party plugin IDs should be globally collision-resistant and distribution/vendor-oriented:

```text
org.example.spectra_optics
com.company.materials
```

Plugin ID and domain name serve different purposes.

A vendor package may expose standard scientific domain names if it implements an agreed capability contract and does not conflict with another provider.

## File/module names

Python module file names should be descriptive snake_case and need not duplicate the full registry namespace.

Examples:

```text
potential_energy.py
field_adapters3d.py
reaction_diffusion3d.py
```

Registry names are public contracts; Python file names are implementation organization.

Do not make downstream domain dependencies depend on file paths.

## Reserved conceptual prefixes

Use these categories consistently:

```text
mathematics.*
calculus.*
linear_algebra.*
tensor.* / tensor_fields.* where existing
pde.*
field_dynamics.*
physics.*
chemistry.*
experiments.*
```

Existing stable names remain authoritative even if some historical namespaces are imperfect.

Future cleanup should favor compatibility over aesthetic renaming.

## Avoid abbreviation ambiguity

Common scientific abbreviations may be acceptable where industry-standard and unambiguous:

```text
pde
ode
cfd
em
```

But public names should prefer descriptive terms where abbreviation could be unclear.

For example, capability names already use `physics.maxwell.*` rather than only `em.*` for time-domain Maxwell behavior.

## Naming review checklist

Before publishing a new public key, ask:

1. Is it semantic rather than implementation-specific?
2. Will the name still make sense if Python becomes GPU/native?
3. Will it still make sense if Blender is removed?
4. Is dimensionality explicit where needed?
5. Is version encoded in metadata rather than the string?
6. Could a third-party developer understand the contract from the name?
7. Does it collide with an existing concept?
8. Is it stable enough to become a dependency key?

## Compatibility rule

Once a capability/domain/role key is used by other modules, treat it as public API.

Do not rename it casually to improve style.

A migration should use deliberate compatibility aliases/deprecation only when the benefit justifies the ecosystem cost.

## Success criterion

At hundreds of domains/providers, a developer should be able to infer ownership and purpose from registry names without knowing repository file layout or renderer implementation details.
