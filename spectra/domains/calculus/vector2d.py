from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec2
from spectra.domains.mathematics.fields2d import ScalarField2D, VectorField2D
from spectra.domains.registry import DomainDependency, DomainRegistry


def _step(value: float) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError("2D field derivative step must be finite and positive")
    return result


def gradient_at_2d(field: ScalarField2D, position: Vec2, *, step: float = 1e-5) -> Vec2:
    h = _step(step)
    dx = Vec2(h, 0.0)
    dy = Vec2(0.0, h)
    return Vec2(
        (field.evaluate(position + dx) - field.evaluate(position - dx)) / (2.0 * h),
        (field.evaluate(position + dy) - field.evaluate(position - dy)) / (2.0 * h),
    )


def divergence_at_2d(field: VectorField2D, position: Vec2, *, step: float = 1e-5) -> float:
    h = _step(step)
    dx = Vec2(h, 0.0)
    dy = Vec2(0.0, h)
    dfx_dx = (field.evaluate(position + dx).x - field.evaluate(position - dx).x) / (2.0 * h)
    dfy_dy = (field.evaluate(position + dy).y - field.evaluate(position - dy).y) / (2.0 * h)
    return dfx_dx + dfy_dy


def scalar_curl_at_2d(field: VectorField2D, position: Vec2, *, step: float = 1e-5) -> float:
    """Out-of-plane curl component: (curl F)_z = dv/dx - du/dy."""
    h = _step(step)
    dx = Vec2(h, 0.0)
    dy = Vec2(0.0, h)
    dv_dx = (field.evaluate(position + dx).y - field.evaluate(position - dx).y) / (2.0 * h)
    du_dy = (field.evaluate(position + dy).x - field.evaluate(position - dy).x) / (2.0 * h)
    return dv_dx - du_dy


@dataclass(frozen=True, slots=True)
class VectorCalculus2DDomain:
    name: str = "calculus.vector2d"
    version: str = "1"
    dependencies: tuple[DomainDependency, ...] = (
        DomainDependency("mathematics.scalar_field2d"),
        DomainDependency("mathematics.vector_field2d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.provide("calculus.gradient_at_2d", gradient_at_2d)
        registry.provide("calculus.divergence_at_2d", divergence_at_2d)
        registry.provide("calculus.scalar_curl_at_2d", scalar_curl_at_2d)
