# Geometry, Relativity, and 2D PDE Foundation

This document records the current contracts added after the first plain-Python validation milestone (124 tests passed at that milestone). The code described here must be revalidated locally before it is treated as a new green baseline.

## Differential geometry

`differential_geometry` owns metric and curvature mathematics. It is not a physics domain.

Current semantics/capabilities include:

- `MetricTensorField`;
- metric matrix and inverse metric;
- metric inner product;
- lowering and raising one vector/covector index;
- numerical Levi-Civita Christoffel symbols;
- numerical Riemann curvature;
- Ricci tensor;
- scalar curvature.

The stored Riemann convention is:

```text
R^rho_(sigma mu nu)
  = d_mu Gamma^rho_(nu sigma)
  - d_nu Gamma^rho_(mu sigma)
  + Gamma^rho_(mu lambda) Gamma^lambda_(nu sigma)
  - Gamma^rho_(nu lambda) Gamma^lambda_(mu sigma)
```

Ricci contraction is:

```text
R_(sigma nu) = R^rho_(sigma rho nu)
```

Metrics may be positive-definite or indefinite. This is deliberate: Euclidean/Riemannian geometry and pseudo-Riemannian spacetime metrics share the same generic contract.

The current derivatives are deterministic finite-difference reference implementations. Analytic derivatives, autodiff, symbolic differentiation, native kernels, or GPU methods may replace them behind the same capabilities later.

## Geodesics

Geodesic time/affine-parameter integration is separated into `differential_geometry.geodesics`.

```text
MetricTensorField
    -> geometry.christoffel_symbols
    + ode.first_order_system
    + ode.solve_rk4
    -> GeodesicSolution
```

This keeps differential geometry independent of a particular ODE implementation.

`GeodesicView3D` makes projection explicit. Higher-dimensional geometry is never silently projected by a renderer. An axis may map to a source coordinate or `None` (zero) before compiling to a generic `Polyline` Scene.

## Special relativity

`physics.relativity` is a physics adapter over generic metric geometry.

Current foundation:

- `SpacetimeEvent` in SI time/position;
- Minkowski metric with signature `(-,+,+,+)` on coordinates `(ct,x,y,z)`;
- invariant interval squared;
- timelike/lightlike/spacelike classification;
- proper time for timelike-separated events;
- Lorentz factor;
- four-velocity.

The metric calculation is reused through `geometry.metric_inner_product` rather than reimplemented in the physics domain.

## General relativity adapter

`physics.relativity.general` consumes generic curvature capabilities.

```text
Tensor algebra
    + Linear algebra inverse
    -> Differential geometry
       Riemann / Ricci / scalar curvature
    -> General relativity
       Einstein tensor
```

Current semantics include `SchwarzschildSpacetime`, whose mass is a typed `Quantity`. Its exterior reference metric uses coordinates `(ct, r, theta, phi)` and requires `r > r_s`.

The typed gravitational constant now lives in `spectra.core.constants` alongside the other physical constants.

The GR domain currently provides:

- Schwarzschild spacetime/metric construction;
- Einstein tensor `G_mu_nu = R_mu_nu - 1/2 R g_mu_nu`;
- a numerical vacuum residual norm.

These are foundations, not a claim of a complete relativity package.

## Two-dimensional PDE foundation

`partial_differential_equations.2d` extends the existing method-of-lines architecture rather than introducing a second solver stack.

Current semantics:

- `UniformGrid2D`, composed from two `UniformGrid1D` axes;
- fixed, periodic, and zero-gradient boundary modes;
- five-point `laplacian_2d`;
- scalar 2D PDE problem/solution;
- method-of-lines time evolution through the existing RK4 ODE capability.

Visualization compiles a solution into one topology-stable `Surface`. The Timeline changes only `Surface.vertices`, so incremental backends can update the native vertex buffer instead of rebuilding topology.

## 2D diffusion proof

`physics.diffusion.2d` contains only physical meaning and composition:

```text
pde.laplacian_2d
    + pde.solve_method_of_lines_2d
    -> physics.diffusion.solve2d
    -> DiffusionSolution2D
    -> animated Surface
```

The diffusion domain does not implement its own Laplacian or time integrator.

## Validation boundary

The previous local baseline was:

```text
pytest: 124 passed
compileall: PASS
catalog/import/serialization: PASS
```

That baseline predates the code in this document. Before declaring a new stable milestone, run the complete suite after pulling latest `main`, plus targeted checks for:

- flat metric Riemann/Ricci/scalar curvature approximately zero;
- unit-sphere scalar curvature approximately 2;
- Euclidean geodesic remains a straight line;
- `GeodesicView3D` compiles to `Polyline`;
- Minkowski timelike/lightlike/spacelike classification;
- four-velocity invariant norm;
- flat-spacetime Einstein tensor approximately zero;
- Schwarzschild radius/metric components;
- 2D quadratic Laplacian interior value;
- 2D diffusion spreading a central pulse;
- animated 2D PDE Surface vertex updates;
- automatic DomainCatalog dependency closure for geodesics, GR, and 2D diffusion.

GitHub Actions remains intentionally absent. Native Blender validation remains a separate pending milestone until Blender is available locally.
