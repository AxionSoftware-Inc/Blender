# Numerical Provenance

Spectra separates scientific semantics from numerical implementation details, but scientific results still need to say how they were computed.

The provenance layer is deliberately additive and backward-compatible. Existing solver capabilities continue to return their existing solution types. A solver may additionally publish:

```text
<solver capability>
<solver capability>.method
<solver capability>.tracked
```

For example:

```text
ode.solve_rk4
ode.solve_rk4.method
ode.solve_rk4.tracked

pde.solve_method_of_lines_3d
pde.solve_method_of_lines_3d.method
pde.solve_method_of_lines_3d.tracked
```

## Contracts

`spectra.numerics` defines renderer- and domain-neutral records:

- `NumericalMethodDescriptor` — method identity, family, implementation, formal order when meaningful, adaptive/reference flags, and notes.
- `NumericalPipelineDescriptor` — ordered composition of method stages.
- `NumericalRunRecord` — start/end time, step count, state size, fixed step size, and lightweight tags.
- `TrackedNumericalResult[T]` — an ordinary result plus its run record.

## Current examples

The fixed-step RK4 reference solver publishes a fourth-order explicit Runge-Kutta descriptor.

The scalar 3D method-of-lines solver publishes a pipeline:

```text
method-of-lines.scalar3d
  -> rk4.fixed
```

The first stage deliberately states that the spatial derivative comes from the problem RHS. A specific physics domain may later publish a richer pipeline containing finite-difference, upwind, Poisson, projection, or other stages without changing the generic solution type.

## Design constraints

- Scientific domains do not need to wrap every result in provenance to remain usable.
- Existing solution dataclasses and serialization schemas are not changed merely to add provenance.
- Provenance is discoverable through versioned capabilities rather than hidden implementation comments.
- Production/native/GPU solvers can publish different descriptors behind the same scientific problem semantics.
- A reference implementation must not be presented as production CFD/FDTD/FEA merely because it has a provenance record.

This layer is intended to support future reproducibility reports, benchmark tooling, solver comparison, experiment tracking, and saved-study metadata without coupling those workflows to Blender or another renderer.
