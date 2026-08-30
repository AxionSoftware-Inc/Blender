from __future__ import annotations

from spectra.core.types import Vec3
from spectra.core.units import PASCAL
from spectra.domains.mathematics.fields import VectorField3D
from spectra.domains.physics.elasticity import (
    IsotropicElasticMaterial,
    StrainTensor3D,
    StressTensor3D,
)
from spectra.domains.registry import DomainDependency, DomainRegistry
from spectra.domains.tensor_fields import TensorField3D


class ElasticityFieldsDomain:
    """Continuous strain/stress fields composed from elasticity pointwise capabilities."""

    name = "physics.elasticity.fields"
    version = "1"
    dependencies = (
        DomainDependency("physics.elasticity.small_strain_at"),
        DomainDependency("physics.elasticity.stress_from_displacement"),
        DomainDependency("tensor.field3d"),
        DomainDependency("mathematics.vector_field3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        small_strain_at = registry.require("physics.elasticity.small_strain_at")
        stress_from_displacement = registry.require(
            "physics.elasticity.stress_from_displacement"
        )

        def strain_field_from_displacement(
            displacement: VectorField3D,
            *,
            step: float = 1e-5,
            name: str = "strain_field",
        ) -> TensorField3D:
            def evaluate(position: Vec3):
                strain: StrainTensor3D = small_strain_at(
                    displacement,
                    position,
                    step=step,
                )
                return strain.tensor

            return TensorField3D(
                evaluator=evaluate,
                shape=(3, 3),
                name=name,
                output_unit=None,
            )

        def stress_field_from_displacement(
            material: IsotropicElasticMaterial,
            displacement: VectorField3D,
            *,
            step: float = 1e-5,
            name: str = "stress_field",
        ) -> TensorField3D:
            def evaluate(position: Vec3):
                stress: StressTensor3D = stress_from_displacement(
                    material,
                    displacement,
                    position,
                    step=step,
                )
                return stress.tensor

            return TensorField3D(
                evaluator=evaluate,
                shape=(3, 3),
                name=name,
                output_unit=PASCAL,
            )

        registry.provide(
            "physics.elasticity.strain_field_from_displacement",
            strain_field_from_displacement,
        )
        registry.provide(
            "physics.elasticity.stress_field_from_displacement",
            stress_field_from_displacement,
        )
