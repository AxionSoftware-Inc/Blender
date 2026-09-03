# Spectra Science — AI Authoring and Semantic Compilation Contract

This document defines how AI may assist users in authoring Spectra scientific projects without becoming the authoritative numerical/scientific runtime.

## Principle

AI proposes semantic intent and commands.

Spectra validates and executes deterministic scientific contracts.

Conceptual boundary:

```text
natural language / multimodal user intent
        ↓
AI planner/compiler
        ↓
semantic project commands / explicit model/view/presentation config
        ↓
Spectra validation + capability graph
        ↓
numerical execution
        ↓
verified semantic result
```

AI must not bypass the engine by inventing numerical results or directly manipulating renderer-native objects as the scientific source of truth.

## AI roles

Useful roles include:

```text
intent parser
project/model authoring assistant
capability discovery assistant
parameter/unit assistant
experiment designer
view/presentation assistant
diagnostic explainer
report/caption assistant
module-development assistant
```

These are authoring/interpretation roles, not replacements for solvers.

## Intent compilation

Example user request:

> Put a positive charge at the left, a negative charge at the right, solve the field, show field lines and potential, then make it cinematic.

AI should compile to explicit operations conceptually:

```text
CreateElectrostaticModel
AddPointCharge(+q, position=A)
AddPointCharge(-q, position=B)
SetGrid(...)
SolveStudy(...)
CreatePotentialSliceView(...)
CreateFieldLineView(...)
SetPresentationPreset(cinematic)
```

Each operation is validated normally.

## Units

AI should preserve/ask/infer units carefully.

If user says:

> radius 5

and no domain/default unit contract makes the meaning unambiguous, AI should not silently choose centimeters/meters and hide the choice.

Semantic metadata may expose preferred/default display units, but scientific constructors remain authoritative.

When AI makes a reasonable explicit assumption, the project command/value should contain the actual unit so it is inspectable.

## Capability discovery

AI should query/introspect available capabilities rather than assume every requested feature exists.

Useful questions:

```text
Which domain handles this subject?
Which semantic problem types are available?
Which views are available for this result?
Which solver roles/providers are compatible?
Which presentation presets exist?
Which plugin is required?
```

This motivates `SEMANTIC_METADATA_AND_INTROSPECTION.md`.

## Unsupported requests

If a user asks for an unsupported model, AI should distinguish:

```text
not implemented
requires plugin
implemented only as reference model
implemented but current provider unavailable
presentation effect unsupported by backend
```

Do not fabricate a result to maintain conversational flow.

## Scientific scope explanation

AI can explain maturity/model scope.

Example:

> This uses Spectra's reference incompressible-flow solver; it is suitable for architecture/examples and defined reference cases, not industrial turbulence-model CFD.

Use maturity metadata rather than vague confidence language.

## Diagnostics

AI should consume structured diagnostics.

Example engine diagnostic:

```text
UNIT_DIMENSION_MISMATCH
charge_density expected C/m^3, received kg/m^3
```

AI can explain and propose a correction, but should apply it only as an explicit new command/value.

Do not catch an error and secretly coerce data until the solver accepts it.

## AI and renderer

AI may request presentation changes semantically:

```text
use cinematic preset
make labels minimal
use orthographic analysis view
reduce displayed arrow density
```

It should not normally emit raw Blender node/socket/object mutations.

A renderer-expert mode may assist backend customization, but those edits are renderer-specific and should not become scientific project truth automatically.

## AI and experiments

AI can author experiment definitions:

```text
sweep temperature from 280 K to 360 K
measure max displacement
minimize energy error
compare RK4 and RK45
run sensitivity for conductivity
```

The experiment engine generates deterministic case IDs, metrics, traces, and artifacts.

AI should not manually aggregate case results from prose when structured metrics are available.

## AI and calibration

AI may help choose:

- candidate parameter ranges;
- observations;
- objective metrics;
- result interpretation.

The calibration engine computes objective/residual values.

AI must not claim an optimum not present in computed results.

## AI and reports

AI may generate narrative from structured:

```text
project metadata
model parameters
result metrics
provenance
maturity/model limitations
figures
experiment artifacts
```

Numerical values should be sourced from engine records.

A report can distinguish AI-authored narrative from deterministic engine-generated tables/metrics if necessary.

## AI-generated modules

A development agent may generate new domain/plugin code.

That code must follow normal acceptance:

- module SDK;
- capability contracts;
- units;
- renderer independence;
- tests;
- maturity labeling;
- security/plugin review.

Generated executable code is executable code and must not be auto-trusted merely because AI produced it.

## Safe project semantics vs trusted scripting

Future product may support two distinct modes:

### Semantic authoring

AI edits safe/validated project structures through commands.

Preferred for normal users.

### Trusted scripting/development

AI can help author arbitrary Python/plugin code.

Requires developer/trust boundary and is not safe project data.

Do not blur the two.

## Command output

AI actions should be inspectable.

A product may show:

```text
Planned changes:
- Add charge +1 nC at (...)
- Add charge -1 nC at (...)
- Use 3D electrostatic solve
- Show potential slice at z=0
- Show 24 field-line seeds
- Set presentation to Cinematic
```

This is more trustworthy than invisible renderer mutations.

## Ambiguity handling

AI should resolve harmless presentation ambiguity automatically when reasonable.

Example:

> Make it prettier.

May select a presentation preset without changing science.

Scientific ambiguity needs more caution.

Example:

> Simulate water flow.

Missing geometry/boundary/viscosity/model assumptions materially affect science. AI may choose a clearly labeled template/reference example, or ask/derive from project context, but should not pretend one arbitrary setup is the requested real-world simulation.

## Templates

AI can accelerate authoring by selecting explicit project templates:

```text
electrostatic dipole
heat diffusion slab
charged particle in magnetic field
quantum wavepacket
reference cavity flow
thermoelastic beam
```

Templates are semantic project definitions with documented assumptions, not hidden AI behavior.

## AI and caching/invalidation

AI commands participate in the normal project invalidation model.

Example:

> Make arrows fewer and switch to dark background.

Should invalidate view/presentation only, not numerical result.

> Double charge strength.

Invalidates result and downstream layers.

The command model determines this, not AI guesswork.

## Provenance of AI edits

Command metadata may optionally record:

```text
source = ai
assistant/model identifier if product policy wants it
user-approved transaction id
```

Scientific result provenance should still focus on the actual semantic model and numerical environment.

## Privacy and external AI

If AI is remote, the product must decide what project/resource data can be sent externally.

Do not automatically send large/private scientific datasets merely because AI needs a summary.

Prefer metadata/derived summaries when sufficient and follow deployment privacy policy.

## Offline/local AI

The architecture should allow AI authoring to be optional. Spectra scientific engine must remain fully usable without AI.

## AI failure behavior

If AI produces an invalid command:

```text
engine validation rejects it
structured diagnostic returned
AI may revise plan
```

Do not weaken semantic validation for AI-generated actions.

## Success criterion

AI should make Spectra easier to author and understand while every actual scientific result remains traceable to explicit semantic inputs, capability contracts, numerical providers, and validated project commands independent of the language model's prose.
