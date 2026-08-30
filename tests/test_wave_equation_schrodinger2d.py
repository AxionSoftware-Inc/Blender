import pytest

from spectra.core.primitives import Surface
from spectra.core.units import KILOGRAM, METER_PER_SECOND, Quantity
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid2D
from spectra.domains.physics import SchrodingerProblem2D, WaveEquationProblem2D


def _grid() -> UniformGrid2D:
    return UniformGrid2D(
        UniformGrid1D(0.0, 1.0, 3),
        UniformGrid1D(0.0, 1.0, 3),
    )


def test_zero_2d_wave_stays_zero_and_visualizes_as_surface() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.wave_equation.2d"])
    grid = _grid()
    zero = tuple(0.0 for _ in range(grid.count))
    problem = WaveEquationProblem2D(
        grid=grid,
        initial_displacement=zero,
        initial_velocity=zero,
        wave_speed=Quantity(2.0, METER_PER_SECOND),
        boundary="fixed",
    )
    solution = registry.require("physics.wave_equation.solve2d")(
        problem,
        end_time=0.1,
        steps=8,
    )
    assert all(value == pytest.approx(0.0) for value in solution.displacements[-1])
    scene = registry.compile_scene(solution)
    assert isinstance(scene.primitives[0], Surface)
    assert scene.timeline.duration == pytest.approx(0.1)


def test_constant_free_schrodinger2d_preserves_probability_mass() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.quantum.schrodinger2d"])
    grid = _grid()
    initial = tuple(1.0 + 0.0j for _ in range(grid.count))
    problem = SchrodingerProblem2D(
        grid=grid,
        initial_values=initial,
        mass=Quantity(1.0, KILOGRAM),
        boundary="zero_gradient",
    )
    solve = registry.require("physics.quantum.schrodinger2d.solve")
    probability_mass = registry.require(
        "physics.quantum.schrodinger2d.probability_mass"
    )
    solution = solve(problem, end_time=0.01, steps=4)
    assert probability_mass(solution.states[0], grid) == pytest.approx(1.0)
    assert probability_mass(solution.states[-1], grid) == pytest.approx(1.0, rel=1e-9)
    scene = registry.compile_scene(solution)
    assert isinstance(scene.primitives[0], Surface)
