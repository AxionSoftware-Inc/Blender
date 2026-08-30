import pytest

from spectra.core.types import Vec2
from spectra.domains.differential_equations import DifferentialEquationsDomain
from spectra.domains.mathematics import MathematicsDomain
from spectra.domains.mathematics.fields2d import TimeDependentVectorField2D
from spectra.domains.partial_differential_equations import PartialDifferentialEquationsDomain
from spectra.domains.partial_differential_equations.domain2d import (
    PartialDifferentialEquations2DDomain,
    UniformGrid2D,
)
from spectra.domains.partial_differential_equations.elliptic2d import (
    EllipticPDE2DDomain,
    PoissonProblem2D,
)
from spectra.domains.partial_differential_equations.transport2d import (
    AdvectionDiffusionProblem2D,
    Transport2DDomain,
    upwind_advection_2d,
)
from spectra.domains.registry import DomainRegistry


def _grid() -> UniformGrid2D:
    grid1d = __import__(
        "spectra.domains.partial_differential_equations.domain",
        fromlist=["UniformGrid1D"],
    ).UniformGrid1D
    return UniformGrid2D(grid1d(-1.0, 1.0, 9), grid1d(-1.0, 1.0, 9))


def test_upwind_advection_of_linear_ramp() -> None:
    grid = _grid()
    values = tuple(x for x, _y in grid.coordinates)
    velocity = TimeDependentVectorField2D(lambda _position, _time: Vec2(1.0, 0.0))
    advection = upwind_advection_2d(values, grid, velocity, time=0.0, boundary="fixed")
    center = grid.flat_index(4, 4)
    assert advection[center] == pytest.approx(1.0)


def test_uniform_passive_scalar_remains_uniform() -> None:
    registry = DomainRegistry()
    registry.add_domains(
        (
            Transport2DDomain(),
            PartialDifferentialEquations2DDomain(),
            PartialDifferentialEquationsDomain(),
            DifferentialEquationsDomain(),
            MathematicsDomain(),
        )
    )
    grid = _grid()
    problem = AdvectionDiffusionProblem2D(
        grid=grid,
        initial_values=tuple(3.0 for _ in range(grid.count)),
        velocity=TimeDependentVectorField2D(lambda _position, _time: Vec2(2.0, -1.0)),
        diffusivity=0.2,
        boundary="fixed",
    )
    solution = registry.require("pde.transport2d.solve")(
        problem,
        end_time=0.1,
        steps=8,
    )
    assert solution.states[-1] == pytest.approx(tuple(3.0 for _ in range(grid.count)))


def test_poisson_solver_preserves_exact_harmonic_linear_solution() -> None:
    registry = DomainRegistry()
    registry.add_domains(
        (
            EllipticPDE2DDomain(),
            PartialDifferentialEquations2DDomain(),
            PartialDifferentialEquationsDomain(),
            DifferentialEquationsDomain(),
        )
    )
    grid = _grid()
    exact = tuple(x + 2.0 * y for x, y in grid.coordinates)
    solution = registry.require("pde.solve_poisson_2d")(
        PoissonProblem2D(
            grid=grid,
            source=tuple(0.0 for _ in range(grid.count)),
            boundary="fixed",
            initial_values=exact,
        ),
        max_iterations=20,
        tolerance=1e-10,
    )
    assert solution.converged
    assert solution.values == pytest.approx(exact, abs=1e-10)
