import pytest

from spectra.domains import DomainRegistry
from spectra.domains.differential_equations import DifferentialEquationsDomain
from spectra.domains.mathematics import MathematicsDomain
from spectra.domains.partial_differential_equations import (
    EllipticPDE2DDomain,
    PDEFieldAdapters2DDomain,
    PDEOperators2DDomain,
    PartialDifferentialEquations2DDomain,
    PartialDifferentialEquationsDomain,
    UniformGrid1D,
    UniformGrid2D,
)
from spectra.domains.physics.electrostatic_potential2d import (
    ElectrostaticPotential2DDomain,
    ElectrostaticPotentialProblem2D,
)


def test_charge_free_linear_potential_produces_uniform_electric_field() -> None:
    registry = DomainRegistry()
    registry.add_domains(
        (
            ElectrostaticPotential2DDomain(),
            EllipticPDE2DDomain(),
            PDEFieldAdapters2DDomain(),
            PDEOperators2DDomain(),
            PartialDifferentialEquations2DDomain(),
            PartialDifferentialEquationsDomain(),
            DifferentialEquationsDomain(),
            MathematicsDomain(),
        )
    )
    grid = UniformGrid2D(UniformGrid1D(-1.0, 1.0, 9), UniformGrid1D(-1.0, 1.0, 9))
    exact_potential = tuple(x for x, _y in grid.coordinates)
    problem = ElectrostaticPotentialProblem2D(
        grid=grid,
        charge_density=tuple(0.0 for _ in range(grid.count)),
        potential_initial_values=exact_potential,
        boundary="fixed",
    )
    solution = registry.require("physics.electrostatic_potential.solve2d")(
        problem,
        max_iterations=20,
        tolerance=1e-10,
    )

    assert solution.converged
    center = grid.flat_index(4, 4)
    assert solution.potential_volts[center] == pytest.approx(0.0, abs=1e-10)
    assert solution.electric_field_si[center].x == pytest.approx(-1.0, rel=1e-6)
    assert solution.electric_field_si[center].y == pytest.approx(0.0, abs=1e-8)
