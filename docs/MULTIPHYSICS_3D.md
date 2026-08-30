# Spectra Science — 3D Multiphysics Foundation

This document describes the current renderer-independent 3D simulation stack. It is an architecture and reference-numerics foundation, not a claim that every reference solver is production CFD/FDTD/FEA quality.

## Design rule

Scientific domains do not own numerical machinery that already exists elsewhere. A domain contributes semantics and composes versioned capabilities:

```text
scientific problem
  -> domain semantics
  -> reusable math / numerical capabilities
  -> solution semantics / continuous fields
  -> explicit visualization views
  -> Scene + Timeline
  -> Blender / future WebGPU / other backends
```

The renderer never decides scientific meaning. For example, a 3D complex wavefunction must be explicitly viewed as real, imaginary, magnitude, or magnitude-squared on an explicit slice.

## Generic numerical foundation

The 3D PDE stack currently includes:

- scalar first-order PDE method-of-lines
- complex first-order PDE method-of-lines
- scalar second-order-in-time PDE
- vector second-order-in-time PDE
- N-component coupled scalar PDE
- finite-difference gradient, divergence, curl, and Laplacian
- scalar and vector upwind advection
- Poisson / elliptic reference solve
- advection-diffusion transport
- grid integrals and L2 norms
- conservative explicit CFL/diffusion diagnostics
- continuity residual diagnostics
- CIC point-source deposition
- trilinear grid-to-field adapters, including time histories
- explicit scalar and complex slice views

All current method-of-lines domains ultimately reuse the generic ODE/RK4 capability rather than embedding separate time integrators.

## Fluids

```text
3D grid operators
  + Poisson3D
  + transport/stability
       -> incompressible-flow reference projection solver
       -> velocity / pressure / speed / vorticity history
       -> F(x,t) field reconstruction
       -> pathlines / vector animation
       -> kinetic-energy / enstrophy / divergence diagnostics
```

The current incompressible solver is a deterministic reference implementation. It is not a production CFD solver and should eventually be replaceable by native CPU/GPU implementations behind the same capability contract.

## Waves and acoustics

```text
ODE/RK4
  -> second-order scalar PDE 3D
  -> wave equation 3D
  -> linear acoustic pressure 3D
```

Acoustics adds pressure/sound semantics but does not implement another wave integrator.

## Quantum dynamics

```text
complex PDE 3D
  + grid integrals
  + typed hbar / mass
       -> Schrodinger 3D
       -> probability density and current
       -> generic continuity residual
       -> explicit complex/slice views
```

Probability current uses generic sampled-grid gradients. Probability conservation diagnostics reuse the generic continuity equation capability rather than embedding a quantum-specific residual formula.

## Solid dynamics

```text
vector second-order PDE 3D
  + grad/div/Laplacian
  + isotropic elasticity
       -> elastodynamics 3D
       -> displacement / velocity F(x,t)
       -> deformed-grid PointCloud animation
       -> stress / von Mises / kinetic / strain-energy diagnostics
```

For a homogeneous isotropic small-strain material the reference acceleration is

```text
u_tt = ((lambda + mu)/rho) grad(div u) + (mu/rho) Laplacian(u) + b
```

The deformed-grid view is deliberately a single animated PointCloud. This maps directly to the already native-validated incremental `PointCloud.positions` backend path instead of generating one Blender object per grid point.

## Heat and thermoelasticity

Typed thermal quantities include specific heat, thermal conductivity, thermal expansion coefficient, temperature rate, and volumetric power.

```text
scalar PDE 3D
  -> heat conduction: T_t = alpha Laplacian(T) + q/(rho cp)
  -> temperature F(x,t)
  -> explicit temperature slices

elasticity + temperature
  -> thermal strain alpha (T - T_ref) I
  -> mechanical strain = total - thermal
  -> thermoelastic stress

thermoelastic material + grad(T)
  -> equivalent thermal body acceleration
  -> existing elastodynamics solver
```

The thermoelastodynamic coupling is currently one-way temperature-to-solid coupling. Fully coupled thermoelastic feedback can be added later without changing Core.

## Electromagnetic dynamics

The time-domain Maxwell reference domain evolves sampled electric and magnetic fields with

```text
dE/dt = c^2 curl(B) - J/epsilon0
dB/dt = -curl(E)
```

It reuses the generic 3D curl operator and ODE/RK4 capability. Typed vacuum permittivity/permeability and current-density units live in the physical-units/constants layer.

Maxwell solution history can be reconstructed as typed `E(x,t)` and `B(x,t)` fields, compiled into batched VectorGlyphSet animations, diagnosed for divergence/energy/Poynting magnitude, and passed to the existing Lorentz-force particle bridge.

Charge/current sources are a separate semantic layer. Source-aware diagnostics compose generic grid divergence and continuity capabilities:

```text
rho(x,t), J(x,t)
  -> Gauss residual: div(E) - rho/epsilon0
  -> magnetic constraint: div(B)
  -> charge continuity: d rho/dt + div(J)
```

The Maxwell time integrator therefore does not need to own source-conservation verification.

This is a reference time-domain Maxwell solver, **not Yee-FDTD**. Numerical dispersion, staggered grids, absorbing boundaries, CFL-specific FDTD schemes, and production electromagnetic stability are future solver implementations behind the same semantic contracts.

## Chemistry and reaction-diffusion

Chemistry introduces a local `ReactionNetwork` independent of spatial discretization.

```text
ReactionNetwork
  + generic ODE
       -> well-mixed chemical kinetics

ReactionNetwork
  + coupled N-component PDE 3D
  + Laplacian
       -> multi-species reaction-diffusion 3D
       -> species F(x,t)
       -> explicit species slice views
```

Mass-action helpers use SI-consistent concentrations (`mol/m^3`). A reaction-rate constant's dimension depends on reaction order, so it is intentionally represented as an SI scalar rather than assigned a misleading fixed unit.

## Cross-domain energy couplings

Thermal physics is now a shared meeting point for multiple scientific domains rather than an isolated solver.

### Thermochemical heating

Reaction enthalpies are energy-per-amount quantities. A reaction-diffusion history can be converted into a volumetric heat field using

```text
q_dot = - sum_r DeltaH_r * reaction_rate_r
```

so an exothermic reaction (`DeltaH < 0`) produces positive heating. The resulting `W/m^3` field is passed directly to the existing heat-conduction problem.

```text
ReactionNetwork + concentration F(x,t)
  -> reaction rates
  -> thermochemical q_dot(x,t)
  -> HeatConductionProblem3D
  -> temperature F(x,t)
  -> optional thermoelastic / solid-dynamic coupling
```

### Electrothermal/Joule heating

Time-dependent Maxwell fields and current density reuse the same thermal contract:

```text
E(x,t) + J(x,t)
  -> q_dot = J dot E
  -> W/m^3 field
  -> HeatConductionProblem3D
```

This creates a renderer-neutral path from electromagnetic simulation to temperature and then, if desired, to thermoelastic response without adding EM-specific logic to the heat solver.

## Domain discovery scalability

Built-in discovery no longer requires a hand-maintained central list of every provider capability or every domain factory.

A concrete built-in domain is discovered when it:

1. lives under `spectra.domains`,
2. is defined in its own module rather than merely re-exported,
3. has a class name ending in `Domain`,
4. supports zero-argument construction, and
5. satisfies the `DomainModule` protocol.

Discovery is deterministic by stable domain name. `DomainCatalog.from_factories()` then probe-loads the discovered domains and derives provider ownership from their real `registry.provide()` calls.

Therefore the scalable path is now:

```text
add new ...Domain class
  -> auto discovery
  -> transactional probe registration
  -> automatic capability-provider index
  -> dependency closure
```

The scientific engine still depends on explicit capability names and dependencies; auto-discovery removes duplicate bookkeeping, not architectural contracts.

## Renderer boundary

No volume primitive has been forced into Core yet. 3D scalar/complex simulation data uses explicit slices and existing Surface primitives. Vector fields use batched VectorGlyphSet primitives, and deformed solid grids use batched PointCloud primitives.

A future volume representation should be added only when its renderer-independent semantic requirements are clear. Existing solvers should not need modification when that happens.
