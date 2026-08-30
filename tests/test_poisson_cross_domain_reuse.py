import pytest

from spectra.core.types import Vec2
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid2D
from spectra.domains.physics import (
    ElectrostaticPotentialProblem2D,
    VorticityStreamfunctionProblem2D,
)


def _grid() -> UniformGrid2D:
    return UniformGrid2D(
        UniformGrid1D(-1.0, 1.0, 5),
        UniformGrid1D(-1.0, 1.0, 5),
    )


def test_zero_source_poisson_is_reused_by_em_and_vorticity_flow() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(
        registry,
        ["physics.electrostatic_potential.2d", "physics.vorticity_streamfunction.2d"],
    )
    grid = _grid()
    zeros = tuple(0.0 for _ in range(grid.count))

    electrostatic = registry.require("physics.electrostatic_potential.solve2d")(
        ElectrostaticPotentialProblem2D(
            grid=grid,
            charge_density=zeros,
            boundary="fixed",
        ),
        max_iterations=50,
        tolerance=1e-12,
    )
    assert electrostatic.converged
    assert max(abs(value) for value in electrostatic.potential_volts) == pytest.approx(0.0)
    assert all(vector == Vec2(0.0, 0.0) for vector in electrostatic.electric_field_si)

    flow = registry.require("physics.vorticity_streamfunction.solve2d")(
        VorticityStreamfunctionProblem2D(
            grid=grid,
            vorticity=zeros,
            boundary="fixed",
        ),
        max_iterations=50,
        tolerance=1e-12,
    )
    assert flow.converged
    assert max(abs(value) for value in flow.streamfunction) == pytest.approx(0.0)
    assert all(vector == Vec2(0.0, 0.0) for vector in flow.velocity)

    assert registry.has_capability("pde.solve_poisson_2d")
