from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec3
from spectra.core.units import LENGTH, PASCAL, PRESSURE, Quantity, Unit
from spectra.domains.mathematics.fields import VectorField3D
from spectra.domains.registry import DomainDependency, DomainRegistry
from spectra.domains.tensor_algebra import Tensor


@dataclass(frozen=True, slots=True)
class StrainTensor3D:
    tensor: Tensor

    def __post_init__(self) -> None:
        if self.tensor.shape != (3, 3):
            raise ValueError("strain tensor must have shape (3, 3)")
        for row in range(3):
            for column in range(row + 1, 3):
                if not math.isclose(
                    self.tensor.at(row, column),
                    self.tensor.at(column, row),
                    rel_tol=1e-9,
                    abs_tol=1e-12,
                ):
                    raise ValueError("small-strain tensor must be symmetric")

    @property
    def trace(self) -> float:
        return sum(self.tensor.at(index, index) for index in range(3))


@dataclass(frozen=True, slots=True)
class StressTensor3D:
    tensor: Tensor
    unit: Unit = PASCAL

    def __post_init__(self) -> None:
        if self.tensor.shape != (3, 3):
            raise ValueError("stress tensor must have shape (3, 3)")
        if self.unit.dimension != PRESSURE:
            raise ValueError("stress tensor unit must have pressure dimension")
        for row in range(3):
            for column in range(row + 1, 3):
                if not math.isclose(
                    self.tensor.at(row, column),
                    self.tensor.at(column, row),
                    rel_tol=1e-9,
                    abs_tol=1e-12,
                ):
                    raise ValueError("Cauchy stress tensor must be symmetric")


@dataclass(frozen=True, slots=True)
class IsotropicElasticMaterial:
    young_modulus: Quantity
    poisson_ratio: float
    name: str = "isotropic_elastic_material"

    def __post_init__(self) -> None:
        if self.young_modulus.unit.dimension != PRESSURE or self.young_modulus.si_value <= 0.0:
            raise ValueError("Young modulus must be a positive pressure quantity")
        if not math.isfinite(self.poisson_ratio) or not (-1.0 < self.poisson_ratio < 0.5):
            raise ValueError("Poisson ratio must lie strictly between -1 and 0.5")
        if not self.name:
            raise ValueError("elastic material name cannot be empty")

    @property
    def lame_lambda_si(self) -> float:
        modulus = self.young_modulus.si_value
        nu = self.poisson_ratio
        return modulus * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))

    @property
    def shear_modulus_si(self) -> float:
        return self.young_modulus.si_value / (2.0 * (1.0 + self.poisson_ratio))


def stress_from_strain(
    material: IsotropicElasticMaterial,
    strain: StrainTensor3D,
) -> StressTensor3D:
    lam = material.lame_lambda_si
    mu = material.shear_modulus_si
    trace = strain.trace
    values = []
    for row in range(3):
        for column in range(3):
            isotropic = lam * trace if row == column else 0.0
            values.append(isotropic + 2.0 * mu * strain.tensor.at(row, column))
    return StressTensor3D(
        Tensor((3, 3), tuple(values), name=f"{material.name}.stress"),
        PASCAL,
    )


def traction_at(stress: StressTensor3D, normal: Vec3) -> Vec3:
    magnitude = normal.magnitude
    if magnitude == 0.0:
        raise ValueError("traction normal cannot be zero")
    unit_normal = normal * (1.0 / magnitude)
    components = (unit_normal.x, unit_normal.y, unit_normal.z)
    result = tuple(
        sum(stress.tensor.at(row, column) * components[column] for column in range(3))
        for row in range(3)
    )
    return Vec3(*result)


def von_mises_stress(stress: StressTensor3D) -> Quantity:
    sxx = stress.tensor.at(0, 0)
    syy = stress.tensor.at(1, 1)
    szz = stress.tensor.at(2, 2)
    sxy = stress.tensor.at(0, 1)
    syz = stress.tensor.at(1, 2)
    szx = stress.tensor.at(2, 0)
    equivalent = math.sqrt(
        0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2)
        + 3.0 * (sxy * sxy + syz * syz + szx * szx)
    )
    return Quantity(equivalent, stress.unit)


class ElasticityDomain:
    """Small-strain isotropic elasticity composed from vector calculus and tensors."""

    name = "physics.elasticity"
    version = "1"
    dependencies = (
        DomainDependency("calculus.jacobian_at_3d"),
        DomainDependency("tensor.tensor"),
    )

    def register(self, registry: DomainRegistry) -> None:
        jacobian = registry.require("calculus.jacobian_at_3d")

        def small_strain_at(
            displacement: VectorField3D,
            position: Vec3,
            *,
            step: float = 1e-5,
        ) -> StrainTensor3D:
            if displacement.output_unit is not None and displacement.output_unit.dimension != LENGTH:
                raise ValueError("displacement field must use a length unit")
            gradient = jacobian(displacement, position, step=step)
            values = tuple(
                0.5 * (gradient.values[row][column] + gradient.values[column][row])
                for row in range(3)
                for column in range(3)
            )
            return StrainTensor3D(Tensor((3, 3), values, name="small_strain"))

        def stress_from_displacement(
            material: IsotropicElasticMaterial,
            displacement: VectorField3D,
            position: Vec3,
            *,
            step: float = 1e-5,
        ) -> StressTensor3D:
            return stress_from_strain(
                material,
                small_strain_at(displacement, position, step=step),
            )

        registry.register_semantic_type("physics.elasticity.strain_tensor3d", StrainTensor3D)
        registry.register_semantic_type("physics.elasticity.stress_tensor3d", StressTensor3D)
        registry.register_semantic_type("physics.elasticity.material", IsotropicElasticMaterial)
        registry.provide("physics.elasticity.material", IsotropicElasticMaterial)
        registry.provide("physics.elasticity.small_strain_at", small_strain_at)
        registry.provide("physics.elasticity.stress_from_strain", stress_from_strain)
        registry.provide("physics.elasticity.stress_from_displacement", stress_from_displacement)
        registry.provide("physics.elasticity.traction_at", traction_at)
        registry.provide("physics.elasticity.von_mises_stress", von_mises_stress)
