import pytest

from spectra.core.types import Vec3
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import (
    ScalarPDESolution3D,
    UniformGrid1D,
    UniformGrid3D,
)


def test_scalar_pde_history_returns_to_continuous_time_field_semantics() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(
        registry,
        ["partial_differential_equations.solution_fields3d"],
    )

    axis = UniformGrid1D(0.0, 1.0, 3)
    grid = UniformGrid3D(axis, axis, axis)
    solution = ScalarPDESolution3D(
        grid=grid,
        times=(0.0, 1.0),
        states=(
            tuple(0.0 for _ in range(grid.count)),
            tuple(2.0 for _ in range(grid.count)),
        ),
        name="ramp",
    )

    field = registry.require("pde.time_scalar_field_from_solution_3d")(solution)
    assert field.evaluate(Vec3(0.37, 0.42, 0.81), 0.0) == pytest.approx(0.0)
    assert field.evaluate(Vec3(0.37, 0.42, 0.81), 0.5) == pytest.approx(1.0)
    assert field.evaluate(Vec3(0.37, 0.42, 0.81), 1.0) == pytest.approx(2.0)
