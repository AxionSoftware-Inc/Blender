import pytest

from spectra.core.types import Vec3
from spectra.core.units import KILOGRAM, METER_PER_SECOND, Quantity
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid3D
from spectra.domains.physics import AcousticPressureProblem3D, SchrodingerProblem3D


def _grid() -> UniformGrid3D:
    axis = UniformGrid1D(0.0, 1.0, 3)
    return UniformGrid3D(axis, axis, axis)


def test_acoustics_3d_reuses_wave_equation_and_zero_state_remains_zero() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["physics.acoustics.3d"])
    grid = _grid()
    solve = registry.require("physics.acoustics.solve3d")

    solution = solve(
        AcousticPressureProblem3D(
            grid=grid,
            initial_pressure=(0.0,) * grid.count,
            initial_pressure_rate=(0.0,) * grid.count,
            sound_speed=Quantity(343.0, METER_PER_SECOND),
        ),
        end_time=0.01,
        steps=2,
    )

    assert "physics.wave_equation.3d" in loaded
    assert solution.pressure_states[-1] == pytest.approx((0.0,) * grid.count)
    assert solution.pressure_rate_states[-1] == pytest.approx((0.0,) * grid.count)


def test_quantum_probability_current_3d_constant_free_state_is_zero() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    loaded = catalog.load(registry, ["physics.quantum.probability_current3d"])
    grid = _grid()
    solve = registry.require("physics.quantum.schrodinger3d.solve")
    schrodinger = solve(
        SchrodingerProblem3D(
            grid=grid,
            initial_values=(1.0 + 0.0j,) * grid.count,
            mass=Quantity(1.0, KILOGRAM),
        ),
        end_time=0.1,
        steps=2,
        normalize_initial=True,
    )

    flow = registry.require("physics.quantum.compute_probability_flow3d")(schrodinger)
    fields = registry.require("physics.quantum.probability_fields_from_flow3d")(flow)

    assert "physics.quantum.schrodinger3d" in loaded
    assert all(
        current == Vec3(0.0, 0.0, 0.0)
        for state in flow.current_states
        for current in state
    )
    assert fields.density.evaluate(Vec3(0.5, 0.5, 0.5), 0.05) == pytest.approx(1.0)
    assert fields.current.evaluate(Vec3(0.5, 0.5, 0.5), 0.05) == Vec3(0.0, 0.0, 0.0)
