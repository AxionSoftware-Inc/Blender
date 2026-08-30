import math

import pytest

from spectra.core.types import Vec3
from spectra.core.units import KILOGRAM_PER_CUBIC_METER, SQUARE_METER_PER_SECOND, Quantity
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid3D
from spectra.domains.physics import IncompressibleFlowProblem3D


def _grid() -> UniformGrid3D:
    axis = UniformGrid1D(0.0, 1.0, 3)
    return UniformGrid3D(axis, axis, axis)


def _zero_solution(registry: DomainRegistry):
    grid = _grid()
    solve = registry.require("physics.incompressible_flow.simulate3d")
    return solve(
        IncompressibleFlowProblem3D(
            grid=grid,
            initial_velocity=(Vec3(0.0, 0.0, 0.0),) * grid.count,
            density=Quantity(1.0, KILOGRAM_PER_CUBIC_METER),
            kinematic_viscosity=Quantity(0.0, SQUARE_METER_PER_SECOND),
        ),
        end_time=0.1,
        steps=2,
        pressure_max_iterations=20,
        pressure_tolerance=1e-10,
    )


def test_zero_flow_3d_invariants_are_zero() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.fluid_invariants.3d"])
    solution = _zero_solution(registry)

    history = registry.require("physics.fluid.compute_invariant_history3d")(solution)

    assert len(history.snapshots) == len(solution.states)
    for snapshot in history.snapshots:
        assert snapshot.kinetic_energy_per_unit_mass == pytest.approx(0.0)
        assert snapshot.enstrophy == pytest.approx(0.0)
        assert snapshot.max_divergence == pytest.approx(0.0)


def test_zero_flow_3d_diagnostics_report_healthy_reference_step() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["physics.fluid_diagnostics.3d"])
    solution = _zero_solution(registry)

    diagnostic = registry.require("physics.fluid.diagnose_solution3d")(solution)

    assert "partial_differential_equations.stability3d" in loaded
    assert diagnostic.max_speed == pytest.approx(0.0)
    assert diagnostic.worst_divergence == pytest.approx(0.0)
    assert diagnostic.worst_pressure_residual == pytest.approx(0.0)
    assert diagnostic.all_pressure_solves_converged
    assert diagnostic.max_conservative_load == pytest.approx(0.0)
    assert diagnostic.all_steps_within_conservative_envelope
    assert math.isinf(diagnostic.minimum_suggested_dt)
