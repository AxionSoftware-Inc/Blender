import pytest

from spectra.core.types import Vec2
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid2D
from spectra.domains.physics import (
    IncompressibleFlowSolution2D,
    IncompressibleFlowState2D,
)


def _solution() -> IncompressibleFlowSolution2D:
    grid = UniformGrid2D(
        UniformGrid1D(-10.0, 10.0, 3),
        UniformGrid1D(-10.0, 10.0, 3),
    )
    first_velocity = tuple(Vec2(1.0, 0.0) for _ in range(grid.count))
    second_velocity = tuple(Vec2(2.0, 0.0) for _ in range(grid.count))
    return IncompressibleFlowSolution2D(
        grid=grid,
        states=(
            IncompressibleFlowState2D(
                time=0.0,
                velocity=first_velocity,
                pressure=tuple(0.0 for _ in range(grid.count)),
                max_divergence=0.0,
                pressure_residual=0.0,
                pressure_converged=True,
            ),
            IncompressibleFlowState2D(
                time=1.0,
                velocity=second_velocity,
                pressure=tuple(2.0 for _ in range(grid.count)),
                max_divergence=0.0,
                pressure_residual=1e-10,
                pressure_converged=True,
            ),
        ),
        density_si=1.0,
        kinematic_viscosity_si=0.1,
        name="uniform_flow",
        velocity_boundary="fixed",
        pressure_boundary="fixed",
    )


def test_flow_solution_reenters_generic_field_and_pathline_pipeline() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    catalog.load(registry, ["physics.incompressible_flow.views2d"])

    solution = _solution()
    fields_from_solution = registry.require(
        "physics.incompressible_flow.fields_from_solution2d"
    )
    fields = fields_from_solution(solution)

    center = Vec2(0.0, 0.0)
    velocity = fields.velocity.evaluate(center, 0.5)
    assert velocity.x == pytest.approx(1.5)
    assert velocity.y == pytest.approx(0.0)
    assert fields.speed.evaluate(center, 0.5) == pytest.approx(1.5)
    assert fields.pressure.evaluate(center, 0.5) == pytest.approx(1.0)
    assert fields.vorticity.evaluate(center, 0.5) == pytest.approx(0.0)

    make_pathline = registry.require(
        "physics.incompressible_flow.pathline_problem2d"
    )
    solve_pathline = registry.require("field_dynamics.solve_pathline_2d")
    problem = make_pathline(solution, Vec2(0.0, 0.0))
    curve = solve_pathline(problem, end_time=1.0, steps=64)
    assert curve.positions[-1].x == pytest.approx(1.5, rel=1e-5, abs=1e-5)
    assert curve.positions[-1].y == pytest.approx(0.0, abs=1e-9)


def test_flow_diagnostics_and_integral_invariants() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    catalog.load(
        registry,
        ["physics.fluid_diagnostics.2d", "physics.fluid_invariants.2d"],
    )
    solution = _solution()

    diagnose = registry.require("physics.fluid.diagnose_solution2d")
    diagnostics = diagnose(solution)
    assert diagnostics.max_speed == pytest.approx(2.0)
    assert diagnostics.worst_divergence == pytest.approx(0.0)
    assert diagnostics.all_pressure_solves_converged
    assert diagnostics.all_steps_within_conservative_envelope

    invariant_history = registry.require("physics.fluid.invariant_history2d")
    history = invariant_history(solution)
    assert history.snapshots[0].kinetic_energy_per_unit_mass == pytest.approx(200.0)
    assert history.snapshots[1].kinetic_energy_per_unit_mass == pytest.approx(800.0)
    assert history.snapshots[0].enstrophy == pytest.approx(0.0)
    assert history.snapshots[0].circulation == pytest.approx(0.0)
