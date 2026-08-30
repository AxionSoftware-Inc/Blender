import pytest

from spectra.core.units import KILOGRAM, Quantity
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import UniformGrid1D
from spectra.domains.physics import SchrodingerProblem1D


def test_schrodinger_catalog_loads_complex_pde_solver_chain() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.quantum.schrodinger1d"])

    assert "physics.quantum.schrodinger1d" in registry.domains
    assert "partial_differential_equations.complex" in registry.domains
    assert "partial_differential_equations" in registry.domains
    assert "differential_equations" in registry.domains
    assert "mathematics" in registry.domains


def test_free_schrodinger_evolution_preserves_probability_approximately() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.quantum.schrodinger1d"])
    solve = registry.require("physics.quantum.schrodinger1d.solve")
    probability_mass = registry.require("physics.quantum.schrodinger1d.probability_mass")

    grid = UniformGrid1D(0.0, 1.0, 7)
    problem = SchrodingerProblem1D(
        grid=grid,
        initial_values=(0j, 0j, 0j, 1.0 + 0.0j, 0j, 0j, 0j),
        mass=Quantity(1e-34, KILOGRAM),
        boundary="fixed",
        name="free-packet",
    )
    solution = solve(problem, end_time=0.01, steps=100)

    initial_mass = probability_mass(solution.states[0], grid)
    final_mass = probability_mass(solution.states[-1], grid)
    assert initial_mass == pytest.approx(1.0, rel=1e-9)
    assert final_mass == pytest.approx(1.0, rel=2e-4)
    assert solution.states[-1][3] != solution.states[0][3]

    scene = registry.compile_scene(solution)
    assert scene.timeline.duration == pytest.approx(0.01)
    assert len(scene.primitives) == 3
