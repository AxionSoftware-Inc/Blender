# Premium Showcase Suite — Status and Promotion Boundary

## Purpose

This file keeps the product-visible flagship suite separate from the engine's verified runtime baseline.

A showcase being present in `main` does not automatically mean it is part of the latest verified checkpoint.

## Verified baseline

The current authoritative verified baseline recorded in `docs/CURRENT_STATUS.md` is:

```text
b24c31c6e48cb88a9efc541ca8632ba8d08f600d
```

At that checkpoint the following four flagship scenes are recorded as locally/native validated:

```text
1. Maxwell electromagnetic wave
2. Electrostatic field laboratory
3. Quantum probability + phase
4. Thermoelastic heated bar
```

That verification boundary must remain unchanged until a later full validation explicitly promotes a newer commit.

## Current development addition

The fifth recommended flagship is now implemented in the development stack:

```text
5. Schwarzschild black-hole null geodesics
```

It composes existing capabilities:

```text
SchwarzschildSpacetime
    -> MetricTensorField
    -> Christoffel symbols
    -> geometry.solve_geodesic
    -> ode.solve_first_order
    -> GeodesicSolution
    -> explicit equatorial r/r_s projection
    -> generic Scene
    -> presentation
    -> Blender
```

Promotion gate:

```text
docs/BLACK_HOLE_GEODESICS_VALIDATION_HANDOFF.md
```

Until that gate passes on the current development HEAD, Black-Hole Geodesics is **implemented, validation pending**.

## Canonical five-scene coverage

| Showcase | Scientific feature | Scene/presentation feature | Current status |
|---|---|---|---|
| Maxwell | time-dependent EM fields | batched E/B animation, science/playback time separation | verified at `b24c31c...` |
| Electrostatic | Poisson + potential + E field + integral curves | signed quantitative potential + vectors + field lines | verified at `b24c31c...` |
| Quantum | complex Schrödinger state | explicit probability + cyclic phase views, SI/display separation | verified at `b24c31c...` |
| Thermoelastic | heat conduction -> thermal strain/free expansion | quantitative temperature + explicitly exaggerated deformation | verified at `b24c31c...` |
| Black hole | Schwarzschild metric + generic geodesic ODE | explicit higher-dimensional coordinate projection + trajectories | implemented after baseline; pending validation |

## Suite invariants

All five scenes must preserve the same platform rules.

### Science before renderer

Every scientific result must exist before Blender is invoked.

```text
no bpy in science/showcase construction
no renderer-side physical formula
no renderer-generated trajectory/field solution
```

### Explicit display transformations

Display transforms may improve readability, but they must be declared and must not mutate the scientific state.

Examples:

```text
Maxwell: c*B display normalization only
Quantum: meters -> display nanometer-scale units; probability height normalization
Thermoelastic: deformation exaggeration explicitly labeled
Black hole: meters -> r/r_s equatorial projection
```

### Quantitative truth

Where scalar color represents a physical quantity:

- the source scalar attribute remains present;
- units remain attached when defined;
- the color scale is presentation metadata;
- Blender receives native display colors rather than recomputing scientific quantities.

### Dense data stays batched

Examples:

- Maxwell E/B -> `VectorGlyphSet`;
- electrostatic E -> `VectorGlyphSet`;
- scalar surfaces -> one `Surface` mesh per semantic view;
- geodesic sample sequences -> one `Polyline`/native curve per trajectory, not per-point objects.

### Scientific time is not presentation time

Time-dependent scientific Timelines retain their physical units/ranges.

A renderer/client may map that interval to human playback seconds. It must not overwrite the scientific duration.

Static-final result showcases are allowed when explicitly described as such; they must not pretend that the solve itself was static.

### Solver interchangeability

Showcase tests must not rely on a fixed solver's sample count unless the public contract guarantees it.

Do not encode assumptions such as:

```text
requested steps N => exactly N + 1 returned samples
```

when a stable role may select adaptive or alternative implementations.

## Suite promotion sequence

For the next promotion:

1. validate the Black-Hole targeted plain-Python tests;
2. run its Blender 5.2 smoke;
3. run full `pytest -q`;
4. ensure the four already-verified flagship paths did not regress;
5. record current HEAD, test count, DomainCatalog counts, and native smoke outcomes;
6. only then update `docs/CURRENT_STATUS.md` and the verified baseline SHA.

Do not silently advance the verified baseline from documentation-only inspection.

## After the five-scene suite is green

The next product-visible showcase wave can expand to:

```text
6. incompressible flow / CFD reference scene
7. reaction-diffusion pattern formation
8. solver laboratory / experiment dashboard
9. coupled electrothermal charged-particle scene
10. parameter-design exploration
```

These should reuse the same Scene/presentation contracts rather than introducing showcase-specific rendering systems.

## Deeper future upgrades to the existing five

Once the five-scene suite is green, useful upgrades can proceed independently:

- animate Quantum probability/phase across the actual Schrödinger solution while keeping femtosecond scientific time separate from playback time;
- animate Thermoelastic temperature/deformation through the heat history;
- add richer diagnostic panels without renderer-side recomputation;
- improve high-cardinality VectorGlyphSet native realization/Geometry Nodes;
- add independent presentation intro/hold/outro timing without contaminating scientific Timeline duration.

Those are enhancements, not prerequisites for recognizing the current canonical scientific compositions.
