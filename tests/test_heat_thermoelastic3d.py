import pytest

from spectra.core.types import Vec3
from spectra.core.units import (
    JOULE_PER_KILOGRAM_KELVIN,
    KELVIN,
    KILOGRAM_PER_CUBIC_METER,
    PASCAL,
    PER_KELVIN,
    WATT_PER_CUBIC_METER,
    WATT_PER_METER_KELVIN,
    Quantity,
)
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.mathematics.fields import TimeDependentScalarField3D
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid3D
from spectra.domains.physics.elasticity import IsotropicElasticMaterial, StrainTensor3D
from spectra.domains.physics.heat_conduction3d import HeatConductionProblem3D, ThermalMaterial3D
from spectra.domains.physics.thermoelasticity3d import ThermoelasticMaterial3D
from spectra.domains.physics.thermoelastodynamics3d import ThermoelastodynamicsProblem3D
from spectra.domains.tensor_algebra import Tensor


def _grid() -> UniformGrid3D:
    axis = UniformGrid1D(0.0, 1.0, 3)
    return UniformGrid3D(axis, axis, axis)


def _thermal_material() -> ThermalMaterial3D:
    return ThermalMaterial3D(
        density=Quantity(1000.0, KILOGRAM_PER_CUBIC_METER),
        specific_heat=Quantity(1000.0, JOULE_PER_KILOGRAM_KELVIN),
        thermal_conductivity=Quantity(10.0, WATT_PER_METER_KELVIN),
    )


def _elastic_material() -> IsotropicElasticMaterial:
    return IsotropicElasticMaterial(
        young_modulus=Quantity(2.0e6, PASCAL),
        poisson_ratio=0.25,
    )


def _thermoelastic_material() -> ThermoelasticMaterial3D:
    return ThermoelasticMaterial3D(
        elastic=_elastic_material(),
        thermal_expansion=Quantity(1.0e-5, PER_KELVIN),
        reference_temperature=Quantity(300.0, KELVIN),
    )


def test_heat_conduction_constant_source_matches_energy_balance() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(
        registry,
        ["physics.heat_conduction.views3d"],
    )
    grid = _grid()
    source = TimeDependentScalarField3D(
        evaluator=lambda _position, _time: 1000.0,
        name="uniform_heat",
        output_unit=WATT_PER_CUBIC_METER,
    )
    solve = registry.require("physics.heat_conduction.solve3d")
    solution = solve(
        HeatConductionProblem3D(
            grid=grid,
            initial_temperature=(300.0,) * grid.count,
            material=_thermal_material(),
            boundary="periodic",
            volumetric_heat_source=source,
        ),
        end_time=2.0,
        steps=4,
    )

    assert "partial_differential_equations.3d" in loaded
    assert solution.material.thermal_diffusivity_si == pytest.approx(1.0e-5)
    assert solution.temperature_states[-1] == pytest.approx((300.002,) * grid.count)

    fields = registry.require("physics.heat_conduction.fields_from_solution3d")(solution)
    assert fields.temperature.evaluate(Vec3(0.5, 0.5, 0.5), 2.0) == pytest.approx(300.002)
    view = registry.require("physics.heat_conduction.temperature_slice3d")(
        solution,
        axis="z",
        index=1,
    )
    scene = registry.compile_scene(view)
    assert scene.timeline is not None


def test_thermoelastic_uniform_heating_creates_isotropic_compressive_stress_if_constrained() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.thermoelasticity.3d"])
    zero_total = StrainTensor3D(
        Tensor((3, 3), (0.0,) * 9, name="zero_total_strain")
    )
    sample = registry.require("physics.thermoelasticity.stress_from_total_strain")(
        _thermoelastic_material(),
        zero_total,
        310.0,
    )

    expected_thermal = 1.0e-4
    assert sample.thermal_strain.tensor.at(0, 0) == pytest.approx(expected_thermal)
    assert sample.thermal_strain.tensor.at(1, 1) == pytest.approx(expected_thermal)
    assert sample.thermal_strain.tensor.at(2, 2) == pytest.approx(expected_thermal)
    assert sample.stress.tensor.at(0, 0) < 0.0
    assert sample.stress.tensor.at(0, 0) == pytest.approx(sample.stress.tensor.at(1, 1))
    assert sample.stress.tensor.at(1, 1) == pytest.approx(sample.stress.tensor.at(2, 2))


def test_uniform_temperature_has_zero_thermoelastic_body_acceleration() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["physics.thermoelastodynamics.3d"])
    grid = _grid()
    temperature = TimeDependentScalarField3D(
        evaluator=lambda _position, _time: 310.0,
        output_unit=KELVIN,
        name="uniform_temperature",
    )
    zero = (Vec3(0.0, 0.0, 0.0),) * grid.count
    problem = ThermoelastodynamicsProblem3D(
        grid=grid,
        initial_displacement=zero,
        initial_velocity=zero,
        material=_thermoelastic_material(),
        density=Quantity(1000.0, KILOGRAM_PER_CUBIC_METER),
        temperature=temperature,
        boundary="fixed",
    )

    body = registry.require("physics.thermoelastodynamics.thermal_body_acceleration3d")(problem)
    assert body.evaluate(Vec3(0.5, 0.5, 0.5), 0.0) == Vec3(0.0, 0.0, 0.0)
    solution = registry.require("physics.thermoelastodynamics.solve3d")(
        problem,
        end_time=0.1,
        steps=2,
    )
    assert all(value == Vec3(0.0, 0.0, 0.0) for value in solution.displacements[-1])
    assert "physics.elastodynamics.3d" in loaded


def test_linear_temperature_gradient_drives_expected_thermal_acceleration_direction() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.thermoelastodynamics.3d"])
    grid = _grid()
    temperature = TimeDependentScalarField3D(
        evaluator=lambda position, _time: 300.0 + position.x,
        output_unit=KELVIN,
        name="linear_temperature",
    )
    zero = (Vec3(0.0, 0.0, 0.0),) * grid.count
    problem = ThermoelastodynamicsProblem3D(
        grid=grid,
        initial_displacement=zero,
        initial_velocity=zero,
        material=_thermoelastic_material(),
        density=Quantity(1000.0, KILOGRAM_PER_CUBIC_METER),
        temperature=temperature,
        boundary="fixed",
    )

    acceleration = registry.require(
        "physics.thermoelastodynamics.thermal_body_acceleration3d"
    )(problem).evaluate(Vec3(0.5, 0.5, 0.5), 0.0)
    assert acceleration.x < 0.0
    assert acceleration.y == pytest.approx(0.0, abs=1e-10)
    assert acceleration.z == pytest.approx(0.0, abs=1e-10)
