import pytest

from spectra.core.types import Vec2
from spectra.core.units import KILOGRAM_PER_CUBIC_METER, SQUARE_METER_PER_SECOND, Quantity
from spectra.domains.differential_equations import DifferentialEquationsDomain
from spectra.domains.partial_differential_equations import PartialDifferentialEquationsDomain
from spectra.domains.partial_differential_equations.domain import UniformGrid1D
from spectra.domains.partial_differential_equations.domain2d import (
    PartialDifferentialEquations2DDomain,
    UniformGrid2D,
)
from spectra.domains.partial_differential_equations.elliptic2d import EllipticPDE2DDomain
from spectra.domains.partial_differential_equations.operators2d import PDEOperators2DDomain
from spectra.domains.physics.incompressible_flow import (
    IncompressibleFlow2DDomain,
    IncompressibleFlowProblem2D,
)
from spectra.domains.registry import DomainRegistry


def test_zero_incompressible_flow_remains_zero_and_compiles() -> None:
    registry = DomainRegistry()
    registry.add_domains(
        (
            IncompressibleFlow2DDomain(),
            EllipticPDE2DDomain(),
            PDEOperators2DDomain(),
            PartialDifferentialEquations2DDomain(),
            PartialDifferentialEquationsDomain(),
            DifferentialEquationsDomain(),
        )
    )
    grid = UniformGrid2D(UniformGrid1D(0.0, 1.0, 7), UniformGrid1D(0.0, 1.0, 7))
    problem = IncompressibleFlowProblem2D(
        grid=grid,
        initial_velocity=tuple(Vec2(0.0, 0.0) for _ in range(grid.count)),
        density=Quantity(1000.0, KILOGRAM_PER_CUBIC_METER),
        kinematic_viscosity=Quantity(1e-6, SQUARE_METER_PER_SECOND),
    )
    solution = registry.require("physics.incompressible_flow.simulate2d")(
        problem,
        end_time=0.05,
        steps=5,
        pressure_max_iterations=50,
    )

    assert all(vector == Vec2(0.0, 0.0) for vector in solution.states[-1].velocity)
    assert solution.states[-1].max_divergence == pytest.approx(0.0)
    assert all(state.pressure_converged for state in solution.states)

    scene = registry.compile_scene(solution)
    assert len(scene.primitives) == 1
    assert len(scene.primitives[0].origins) == grid.count
    assert scene.timeline.duration == pytest.approx(0.05)
