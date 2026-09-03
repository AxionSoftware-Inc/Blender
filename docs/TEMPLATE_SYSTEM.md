# Spectra Science — Project and Study Template System

This document defines how reusable scientific templates should accelerate project authoring without hiding assumptions inside UI or AI behavior.

## Goal

A template is a versioned semantic starting point:

```text
template
  -> project/model parameters
  -> documented assumptions
  -> optional default view
  -> optional presentation preset
  -> optional experiment definition
```

A template is not a pre-rendered Blender scene and not an opaque script.

## Template categories

Useful categories:

```text
scientific model templates
teaching/demo templates
experiment templates
presentation templates
workflow templates
```

## Scientific model template

Examples:

```text
electrostatic dipole
uniform magnetic particle orbit
heat diffusion slab
reference cavity flow
quantum Gaussian wavepacket
thermoelastic beam
Schwarzschild geodesic bundle
A -> B reaction diffusion
```

The template should specify explicit scientific assumptions.

Example metadata:

```text
template_id
title
subject
description
maturity
required capabilities
model scope
parameters exposed to user
default units
default solver policy
reference diagnostics
```

## Template parameterization

A template should expose user-facing parameters rather than require editing raw internal objects.

Example electrostatic dipole template:

```text
charge magnitude
separation
grid bounds
grid resolution
field-line seed density
```

Template expansion constructs normal semantic objects.

After expansion, the project should remain editable through standard commands/APIs.

## Assumptions

Every scientific template must disclose assumptions.

Example:

```text
Reference incompressible flow template
- incompressible model
- reference finite-difference solver
- simple boundary conditions
- no turbulence model
```

Templates must not make reference implementations appear industrial merely by wrapping them in polished UI.

## Default solver policy

A template may recommend a solver policy, but it should not hardcode one implementation unless scientifically required.

Good:

```text
recommended: accurate_reference
```

Avoid:

```text
always import rk4.reference directly
```

The numerical role remains stable.

## Default views

Templates may include meaningful initial views:

```text
electrostatic dipole
  -> potential slice
  -> electric field vectors
  -> field lines
```

Views remain explicit semantic view definitions.

## Default presentation

A template may suggest presentation:

```text
teaching demo -> presentation
paper figure -> publication
marketing showcase -> cinematic
```

Presentation choice is replaceable without recomputing the scientific model.

## Teaching templates

Teaching templates may add staged explanation metadata:

```text
1. show geometry/source
2. explain boundary/parameters
3. reveal field
4. animate time
5. display diagnostic
```

This is presentation/workflow guidance, not new physics.

## Experiment templates

Reusable experiment definitions may include:

```text
solver convergence study
parameter sensitivity study
material calibration
Pareto tradeoff exploration
uncertainty propagation
```

They should bind to semantic parameter/metric IDs rather than arbitrary UI widget names.

## Workflow templates

A workflow template can chain ordinary operations:

```text
load model
validate
solve
compute derived diagnostic
compile view
apply publication presentation
export figure + metadata
```

This can power CLI, UI, AI, and tutorials through the same command model.

## Template identity/version

Templates should have stable IDs and versions.

Conceptually:

```text
physics.electrostatics.dipole@1
physics.quantum.gaussian_wavepacket@2
```

A template version changes when default structure/assumptions change materially.

Do not silently change an old saved project's meaning because the current template was updated.

Once expanded into a project, the project stores explicit semantic state. It should not require the original template to remain installed merely to solve/view the project, unless plugin semantics themselves are required.

## Built-in vs plugin templates

Built-in domains may provide templates.

Third-party plugins may also provide templates through explicit metadata/registration.

Template discovery should be separate from domain capability ownership so one domain can expose multiple templates.

## Template metadata/introspection

Template metadata can feed:

- project creation UI;
- search/filter;
- AI authoring;
- tutorials;
- documentation.

Useful filters:

```text
subject
maturity
2D/3D
static/time-dependent
requires GPU? no/optional
teaching/reference/showcase
```

## Safe template loading

Templates should be data/factories using approved installed code.

A project should not download/execute arbitrary template scripts from the internet merely from a template ID.

External template packages follow plugin trust policy.

## Template preview

Product UI may show:

- description;
- expected output image/video;
- parameters;
- scientific assumptions;
- maturity;
- required plugin/provider.

Preview assets are not scientific source of truth.

## AI template selection

AI can map vague requests to explicit templates.

Example:

> Show me a simple black-hole geodesic demo.

AI may select a documented Schwarzschild/geodesic reference template and state its assumptions.

This is preferable to silently inventing arbitrary parameters.

## Template customization

After creation, user can modify semantic parameters normally.

The UI should distinguish:

```text
reset to template default
current project value
```

Do not lock projects into one template-specific editor forever.

## Canonical showcase templates

The first premium showcase scenes may be implemented as template + view + presentation combinations:

```text
electrostatic laboratory
Maxwell plane wave
quantum wavepacket
thermoelastic solid
Schwarzschild geodesics
```

This makes them reusable as demos, tests, tutorials, and product examples.

## Success criterion

A user should be able to create a serious, explicit starting scientific project from a template in seconds, while every assumption, parameter, capability, view, and presentation choice remains inspectable and editable through normal Spectra semantics.
