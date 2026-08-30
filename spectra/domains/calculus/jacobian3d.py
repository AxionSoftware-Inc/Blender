from __future__ import annotations

import math

from spectra.core.types import Vec3
from spectra.domains.linear_algebra import MatrixN
from spectra.domains.mathematics.fields import VectorField3D
from spectra.domains.registry import DomainDependency, DomainRegistry


def jacobian_at_3d(
    field: VectorField3D,
    position: Vec3,
    *,
    step: float = 1e-5,
) -> MatrixN:
    """Numerical Jacobian J_ij = partial F_i / partial x_j."""

    h = float(step)
    if not math.isfinite(h) or h <= 0.0:
        raise ValueError("Jacobian derivative step must be finite and positive")

    offsets = (
        Vec3(h, 0.0, 0.0),
        Vec3(0.0, h, 0.0),
        Vec3(0.0, 0.0, h),
    )
    columns = []
    for offset in offsets:
        plus = field.evaluate(position + offset)
        minus = field.evaluate(position - offset)
        columns.append(
            (
                (plus.x - minus.x) / (2.0 * h),
                (plus.y - minus.y) / (2.0 * h),
                (plus.z - minus.z) / (2.0 * h),
            )
        )
    return MatrixN.of(
        (
            (columns[0][0], columns[1][0], columns[2][0]),
            (columns[0][1], columns[1][1], columns[2][1]),
            (columns[0][2], columns[1][2], columns[2][2]),
        )
    )


class Jacobian3DDomain:
    name = "calculus.jacobian3d"
    version = "1"
    dependencies = (
        DomainDependency("mathematics.vector_field3d"),
        DomainDependency("linear_algebra.matrix"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.provide("calculus.jacobian_at_3d", jacobian_at_3d)
