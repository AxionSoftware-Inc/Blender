from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec3
from spectra.core.units import Quantity, Unit
from spectra.domains.linear_algebra import MatrixN
from spectra.domains.physics.elasticity import StressTensor3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class PrincipalStressState3D:
    values: tuple[float, float, float]
    directions: tuple[Vec3, Vec3, Vec3]
    unit: Unit
    converged: bool

    def __post_init__(self) -> None:
        if not all(math.isfinite(value) for value in self.values):
            raise ValueError("principal stresses must be finite")
        if any(direction.magnitude == 0.0 for direction in self.directions):
            raise ValueError("principal stress direction cannot be zero")

    @property
    def maximum(self) -> Quantity:
        return Quantity(self.values[0], self.unit)

    @property
    def minimum(self) -> Quantity:
        return Quantity(self.values[-1], self.unit)

    @property
    def maximum_shear(self) -> Quantity:
        return Quantity(0.5 * (self.values[0] - self.values[-1]), self.unit)


class PrincipalStressDomain:
    name = "physics.elasticity.principal"
    version = "1"
    dependencies = (
        DomainDependency("physics.elasticity.stress_tensor3d"),
        DomainDependency("linear_algebra.symmetric_eigendecomposition"),
    )

    def register(self, registry: DomainRegistry) -> None:
        eigensystem = registry.require("linear_algebra.symmetric_eigendecomposition")

        def principal_stresses(
            stress: StressTensor3D,
            *,
            tolerance: float = 1e-12,
            max_sweeps: int = 64,
        ) -> PrincipalStressState3D:
            matrix = MatrixN.of(
                tuple(
                    tuple(stress.tensor.at(row, column) for column in range(3))
                    for row in range(3)
                )
            )
            result = eigensystem(
                matrix,
                tolerance=tolerance,
                max_sweeps=max_sweeps,
            )
            directions = tuple(
                Vec3(*vector.values).normalized()
                for vector in result.eigenvectors
            )
            return PrincipalStressState3D(
                values=(
                    result.eigenvalues[0],
                    result.eigenvalues[1],
                    result.eigenvalues[2],
                ),
                directions=(directions[0], directions[1], directions[2]),
                unit=stress.unit,
                converged=result.converged,
            )

        registry.register_semantic_type(
            "physics.elasticity.principal_stress3d",
            PrincipalStressState3D,
        )
        registry.provide("physics.elasticity.principal_stresses", principal_stresses)
