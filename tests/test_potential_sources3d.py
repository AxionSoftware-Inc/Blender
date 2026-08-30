import pytest

from spectra.core.types import Vec3
from spectra.core.units import COULOMB, KILOGRAM, Quantity
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid3D
from spectra.domains.physics import PointChargeSource3D, PointMassSource3D


def _grid() -> UniformGrid3D:
    axis = UniformGrid1D(0.0, 1.0, 3)
    return UniformGrid3D(axis, axis, axis)


def test_typed_point_sources_share_generic_conservative_deposition() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["physics.potential_sources.3d"])
    grid = _grid()

    charge_problem = registry.require("physics.potential_sources.electrostatic_problem3d")(
        grid,
        (PointChargeSource3D(Vec3(0.25, 0.25, 0.25), Quantity(2.0, COULOMB)),),
    )
    mass_problem = registry.require("physics.potential_sources.gravitational_problem3d")(
        grid,
        (PointMassSource3D(Vec3(0.25, 0.25, 0.25), Quantity(3.0, KILOGRAM)),),
    )

    cell_volume = grid.x.spacing * grid.y.spacing * grid.z.spacing
    assert sum(charge_problem.charge_density) * cell_volume == pytest.approx(2.0)
    assert sum(mass_problem.mass_density) * cell_volume == pytest.approx(3.0)
    assert charge_problem.charge_density_unit.symbol == "C/m^3"
    assert mass_problem.mass_density_unit.symbol == "kg/m^3"

    assert "partial_differential_equations.deposition3d" in loaded
    assert "physics.electrostatic_potential.3d" in loaded
    assert "physics.gravitational_potential.3d" in loaded
    assert registry.has_capability("pde.deposit_point_density_3d")


def test_point_source_type_validation_is_dimension_safe() -> None:
    with pytest.raises(ValueError):
        PointChargeSource3D(Vec3(0.0, 0.0, 0.0), Quantity(1.0, KILOGRAM))
    with pytest.raises(ValueError):
        PointMassSource3D(Vec3(0.0, 0.0, 0.0), Quantity(1.0, COULOMB))
