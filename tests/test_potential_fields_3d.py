import pytest

from spectra.core.types import Vec3
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid3D


def _grid() -> UniformGrid3D:
    axis = UniformGrid1D(-1.0, 1.0, 5)
    return UniformGrid3D(axis, axis, axis)


def test_electrostatic_3d_harmonic_linear_potential_recovers_uniform_field() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    catalog.load(registry, ["physics.electrostatic_potential.3d"])

    grid = _grid()
    problem_type = registry.require("physics.electrostatic_potential.problem3d")
    solve = registry.require("physics.electrostatic_potential.solve3d")
    as_field = registry.require("physics.electrostatic_potential.vector_field3d")

    potential = tuple(x for x, _y, _z in grid.coordinates)
    solution = solve(
        problem_type(
            grid=grid,
            charge_density=tuple(0.0 for _ in range(grid.count)),
            potential_initial_values=potential,
            boundary="fixed",
        ),
        max_iterations=10,
        tolerance=1e-10,
    )

    assert solution.converged
    field = as_field(solution)
    sample = field.evaluate(Vec3(0.0, 0.0, 0.0))
    assert sample.x == pytest.approx(-1.0, abs=1e-9)
    assert sample.y == pytest.approx(0.0, abs=1e-9)
    assert sample.z == pytest.approx(0.0, abs=1e-9)


def test_gravity_and_electrostatics_share_poisson3d_provider_chain() -> None:
    catalog = builtin_domain_catalog()

    electrostatic_registry = DomainRegistry()
    catalog.load(electrostatic_registry, ["physics.electrostatic_potential.3d"])

    gravity_registry = DomainRegistry()
    catalog.load(gravity_registry, ["physics.gravitational_potential.3d"])

    for registry in (electrostatic_registry, gravity_registry):
        assert registry.has_capability("pde.poisson_problem3d")
        assert registry.has_capability("pde.solve_poisson_3d")
        assert registry.has_capability("pde.gradient_grid_3d")
        assert registry.has_capability("pde.scalar_field_from_grid_3d")
        assert registry.has_capability("pde.vector_field_from_grid_3d")
