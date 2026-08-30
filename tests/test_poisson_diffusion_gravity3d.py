import pytest

from spectra.core.primitives import Surface
from spectra.core.types import Vec3
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import (
    PoissonProblem3D,
    ScalarPDESliceView3D,
    UniformGrid1D,
    UniformGrid3D,
)
from spectra.domains.physics import (
    DiffusionProblem3D,
    GravitationalPotentialProblem3D,
)


def _grid() -> UniformGrid3D:
    axis = UniformGrid1D(-1.0, 1.0, 5)
    return UniformGrid3D(axis, axis, axis)


def test_zero_source_poisson3d_converges_to_zero() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(
        registry,
        ["partial_differential_equations.elliptic3d"],
    )
    grid = _grid()
    zeros = tuple(0.0 for _ in range(grid.count))
    solution = registry.require("pde.solve_poisson_3d")(
        PoissonProblem3D(grid=grid, source=zeros, boundary="fixed"),
        max_iterations=20,
        tolerance=1e-12,
    )
    assert solution.converged
    assert solution.residual_inf == pytest.approx(0.0)
    assert solution.values == pytest.approx(zeros)


def test_3d_diffusion_spreads_center_pulse_and_can_be_sliced() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(
        registry,
        ["physics.diffusion.3d", "partial_differential_equations.slices3d"],
    )
    grid = _grid()
    center = grid.flat_index(2, 2, 2)
    initial = [0.0] * grid.count
    initial[center] = 1.0
    solution = registry.require("physics.diffusion.solve3d")(
        DiffusionProblem3D(
            grid=grid,
            initial_values=tuple(initial),
            diffusivity=0.05,
            boundary="fixed",
        ),
        end_time=0.02,
        steps=8,
    )
    final = solution.states[-1]
    assert final[center] < 1.0
    assert final[grid.flat_index(3, 2, 2)] > 0.0

    view = ScalarPDESliceView3D(
        solution=solution.pde_solution,
        axis="z",
        index=2,
    )
    scene = registry.compile_scene(view)
    assert isinstance(scene.primitives[0], Surface)


def test_zero_density_gravity3d_reuses_poisson_and_returns_zero_fields() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    loaded = catalog.load(registry, ["physics.gravitational_potential.3d"])
    grid = _grid()
    zeros = tuple(0.0 for _ in range(grid.count))
    solution = registry.require("physics.gravitational_potential.solve3d")(
        GravitationalPotentialProblem3D(
            grid=grid,
            mass_density=zeros,
            boundary="fixed",
        ),
        max_iterations=20,
        tolerance=1e-12,
    )
    assert solution.converged
    assert solution.potential_si == pytest.approx(zeros)
    assert all(value == Vec3(0.0, 0.0, 0.0) for value in solution.field_si)

    potential = registry.require(
        "physics.gravitational_potential.scalar_field3d"
    )(solution)
    gravity = registry.require(
        "physics.gravitational_potential.vector_field3d"
    )(solution)
    assert potential.evaluate(Vec3(0.1, 0.2, 0.3)) == pytest.approx(0.0)
    assert gravity.evaluate(Vec3(0.1, 0.2, 0.3)) == Vec3(0.0, 0.0, 0.0)
    assert "partial_differential_equations.elliptic3d" in loaded
    assert "partial_differential_equations.operators3d" in loaded
    assert "partial_differential_equations.field_adapters3d" in loaded
