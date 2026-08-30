import pytest

from spectra.core.units import KILOGRAM, METER_PER_SECOND, Quantity
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import (
    ComplexPDESliceView3D,
    UniformGrid1D,
    UniformGrid3D,
)
from spectra.domains.physics import SchrodingerProblem3D, WaveEquationProblem3D


def _grid() -> UniformGrid3D:
    axis = UniformGrid1D(0.0, 1.0, 3)
    return UniformGrid3D(axis, axis, axis)


def test_wave_equation_3d_zero_state_remains_zero() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["physics.wave_equation.3d"])
    solve = registry.require("physics.wave_equation.solve3d")
    grid = _grid()

    solution = solve(
        WaveEquationProblem3D(
            grid=grid,
            initial_displacement=(0.0,) * grid.count,
            initial_velocity=(0.0,) * grid.count,
            wave_speed=Quantity(1.0, METER_PER_SECOND),
        ),
        end_time=0.25,
        steps=2,
    )

    assert "partial_differential_equations.second_order3d" in loaded
    assert solution.displacements[-1] == pytest.approx((0.0,) * grid.count)
    assert solution.velocities[-1] == pytest.approx((0.0,) * grid.count)


def test_schrodinger_3d_normalizes_and_conserves_constant_free_state() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    loaded = catalog.load(registry, ["physics.quantum.schrodinger3d"])
    solve = registry.require("physics.quantum.schrodinger3d.solve")
    probability_mass = registry.require("physics.quantum.schrodinger3d.probability_mass")
    grid = _grid()

    solution = solve(
        SchrodingerProblem3D(
            grid=grid,
            initial_values=(1.0 + 0.0j,) * grid.count,
            mass=Quantity(1.0, KILOGRAM),
        ),
        end_time=0.1,
        steps=2,
        normalize_initial=True,
    )

    assert "partial_differential_equations.complex3d" in loaded
    assert "partial_differential_equations.integrals3d" in loaded
    assert probability_mass(solution.states[0], grid) == pytest.approx(1.0)
    assert probability_mass(solution.states[-1], grid) == pytest.approx(1.0, abs=1e-10)


def test_schrodinger_3d_uses_generic_complex_slice_view() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    catalog.load(registry, ["physics.quantum.schrodinger3d"])
    solve = registry.require("physics.quantum.schrodinger3d.solve")
    grid = _grid()
    solution = solve(
        SchrodingerProblem3D(
            grid=grid,
            initial_values=(1.0 + 0.0j,) * grid.count,
            mass=Quantity(1.0, KILOGRAM),
        ),
        end_time=0.1,
        steps=2,
    )

    catalog.load(registry, ["partial_differential_equations.complex_views3d"])
    scene = registry.compile_scene(
        ComplexPDESliceView3D(
            solution=solution.pde_solution,
            axis="z",
            index=1,
            component="magnitude_squared",
        )
    )

    assert len(scene.primitives) == 1
    assert scene.timeline is not None
