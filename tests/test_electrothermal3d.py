import pytest

from spectra.core.types import Vec3
from spectra.core.units import (
    AMPERE_PER_SQUARE_METER,
    JOULE_PER_KILOGRAM_KELVIN,
    KILOGRAM_PER_CUBIC_METER,
    NEWTON_PER_COULOMB,
    Quantity,
    WATT_PER_METER_KELVIN,
)
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.mathematics.fields import TimeDependentVectorField3D
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid3D
from spectra.domains.physics import ThermalMaterial3D
from spectra.domains.physics.maxwell import MaxwellSolution3D, MaxwellSourceFields3D


def _grid() -> UniformGrid3D:
    axis = UniformGrid1D(0.0, 1.0, 3)
    return UniformGrid3D(axis, axis, axis)


def _maxwell_solution() -> MaxwellSolution3D:
    grid = _grid()
    electric = (Vec3(2.0, 0.0, 0.0),) * grid.count
    magnetic = (Vec3(0.0, 0.0, 0.0),) * grid.count
    return MaxwellSolution3D(
        grid=grid,
        times=(0.0, 1.0),
        electric_states=(electric, electric),
        magnetic_states=(magnetic, magnetic),
        boundary="periodic",
        source_free=False,
        name="uniform_electric",
    )


def _sources() -> MaxwellSourceFields3D:
    return MaxwellSourceFields3D(
        current_density=TimeDependentVectorField3D(
            evaluator=lambda _position, _time: Vec3(3.0, 0.0, 0.0),
            name="uniform_current",
            output_unit=AMPERE_PER_SQUARE_METER,
        ),
        name="uniform_current_sources",
    )


def _material() -> ThermalMaterial3D:
    return ThermalMaterial3D(
        density=Quantity(1.0, KILOGRAM_PER_CUBIC_METER),
        specific_heat=Quantity(1.0, JOULE_PER_KILOGRAM_KELVIN),
        thermal_conductivity=Quantity(1.0, WATT_PER_METER_KELVIN),
    )


def test_joule_heat_field_is_current_dot_electric_field() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["physics.electrothermal.3d"])
    source = registry.require("physics.electrothermal.source_from_maxwell3d")(
        _maxwell_solution(),
        _sources(),
    )
    heat_field = registry.require("physics.electrothermal.joule_heat_field3d")(source)

    assert "physics.electromagnetism.maxwell_views3d" in loaded
    assert "physics.heat_conduction.3d" in loaded
    assert heat_field.evaluate(Vec3(0.5, 0.5, 0.5), 0.5) == pytest.approx(6.0)


def test_electrothermal_problem_reuses_heat_conduction_solver() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.electrothermal.3d"])
    solution = _maxwell_solution()
    problem = registry.require("physics.electrothermal.heat_problem_from_maxwell3d")(
        solution,
        _sources(),
        initial_temperature=(300.0,) * solution.grid.count,
        material=_material(),
        boundary="periodic",
    )

    solve_heat = registry.require("physics.heat_conduction.solve3d")
    heat = solve_heat(problem, end_time=0.5, steps=2)
    assert heat.temperature_states[-1] == pytest.approx((303.0,) * solution.grid.count)
