from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec3
from spectra.core.units import TEMPERATURE, THERMAL_EXPANSION, Quantity
from spectra.domains.mathematics.fields import ScalarField3D, VectorField3D
from spectra.domains.physics.elasticity import (
    IsotropicElasticMaterial,
    StrainTensor3D,
    StressTensor3D,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class ThermoelasticMaterial3D:
    elastic: IsotropicElasticMaterial
    thermal_expansion: Quantity
    reference_temperature: Quantity
    name: str = "thermoelastic_material"

    def __post_init__(self) -> None:
        if self.thermal_expansion.unit.dimension != THERMAL_EXPANSION:
            raise ValueError("thermal expansion coefficient must have inverse-temperature dimension")
        if self.thermal_expansion.si_value < 0.0:
            raise ValueError("thermal expansion coefficient must be non-negative")
        if self.reference_temperature.unit.dimension != TEMPERATURE:
            raise ValueError("reference temperature must have temperature dimension")
        if self.reference_temperature.si_value < 0.0:
            raise ValueError("reference temperature must be non-negative")
        if not self.name:
            raise ValueError("thermoelastic material name cannot be empty")


@dataclass(frozen=True, slots=True)
class ThermoelasticStressSample3D:
    total_strain: StrainTensor3D
    thermal_strain: StrainTensor3D
    mechanical_strain: StrainTensor3D
    stress: StressTensor3D
    temperature_si: float


def _temperature_si(field: ScalarField3D, position: Vec3) -> float:
    value = field.evaluate(position)
    if field.output_unit is None:
        return value
    if field.output_unit.dimension != TEMPERATURE:
        raise ValueError("thermoelastic temperature field must use temperature units")
    return field.output_unit.to_si(value)


class Thermoelasticity3DDomain:
    """Small-strain thermoelastic constitutive coupling over generic elasticity fields."""

    name = "physics.thermoelasticity.3d"
    version = "1"
    dependencies = (
        DomainDependency("tensor.tensor"),
        DomainDependency("physics.elasticity.strain_tensor3d", min_version=2),
        DomainDependency("physics.elasticity.small_strain_at"),
        DomainDependency("physics.elasticity.stress_from_strain"),
        DomainDependency("mathematics.scalar_field3d"),
        DomainDependency("mathematics.vector_field3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        tensor_type = registry.require("tensor.tensor")
        small_strain_at = registry.require("physics.elasticity.small_strain_at")
        stress_from_strain = registry.require("physics.elasticity.stress_from_strain")

        def thermal_strain(
            material: ThermoelasticMaterial3D,
            temperature_si: float,
        ) -> StrainTensor3D:
            temperature = float(temperature_si)
            if not math.isfinite(temperature) or temperature < 0.0:
                raise ValueError("thermoelastic temperature must be finite and non-negative")
            scalar = material.thermal_expansion.si_value * (
                temperature - material.reference_temperature.si_value
            )
            values = tuple(
                scalar if row == column else 0.0
                for row in range(3)
                for column in range(3)
            )
            return StrainTensor3D(
                tensor_type((3, 3), values, name=f"{material.name}.thermal_strain")
            )

        def mechanical_strain(
            total: StrainTensor3D,
            thermal: StrainTensor3D,
        ) -> StrainTensor3D:
            values = tuple(
                total.tensor.at(row, column) - thermal.tensor.at(row, column)
                for row in range(3)
                for column in range(3)
            )
            return StrainTensor3D(
                tensor_type((3, 3), values, name="thermoelastic_mechanical_strain")
            )

        def stress_from_total_strain(
            material: ThermoelasticMaterial3D,
            total: StrainTensor3D,
            temperature_si: float,
        ) -> ThermoelasticStressSample3D:
            thermal = thermal_strain(material, temperature_si)
            mechanical = mechanical_strain(total, thermal)
            stress = stress_from_strain(material.elastic, mechanical)
            return ThermoelasticStressSample3D(
                total_strain=total,
                thermal_strain=thermal,
                mechanical_strain=mechanical,
                stress=stress,
                temperature_si=float(temperature_si),
            )

        def stress_from_fields(
            material: ThermoelasticMaterial3D,
            displacement: VectorField3D,
            temperature: ScalarField3D,
            position: Vec3,
            *,
            step: float = 1e-5,
        ) -> ThermoelasticStressSample3D:
            total = small_strain_at(displacement, position, step=step)
            return stress_from_total_strain(
                material,
                total,
                _temperature_si(temperature, position),
            )

        registry.register_semantic_type(
            "physics.thermoelasticity.material3d",
            ThermoelasticMaterial3D,
        )
        registry.register_semantic_type(
            "physics.thermoelasticity.stress_sample3d",
            ThermoelasticStressSample3D,
        )
        registry.provide("physics.thermoelasticity.material3d", ThermoelasticMaterial3D)
        registry.provide("physics.thermoelasticity.thermal_strain", thermal_strain)
        registry.provide("physics.thermoelasticity.mechanical_strain", mechanical_strain)
        registry.provide(
            "physics.thermoelasticity.stress_from_total_strain",
            stress_from_total_strain,
        )
        registry.provide("physics.thermoelasticity.stress_from_fields", stress_from_fields)
