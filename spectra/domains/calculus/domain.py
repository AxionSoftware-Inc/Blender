from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec3
from spectra.domains.mathematics.fields import ScalarField3D, VectorField3D
from spectra.domains.mathematics.functions import Function1D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True)
class TangentSample:
    x: float
    y: float
    slope: float


def derivative_at(function: Function1D, x: float, *, step: float | None = None) -> float:
    if not function.domain.contains(x):
        raise ValueError("derivative point lies outside function domain")

    h = step
    if h is None:
        h = max(function.domain.length * 1e-5, 1e-7)
    if h <= 0:
        raise ValueError("derivative step must be positive")

    left = x - h
    right = x + h
    if function.domain.contains(left) and function.domain.contains(right):
        return (function.evaluate(right) - function.evaluate(left)) / (2.0 * h)
    if function.domain.contains(right):
        return (function.evaluate(right) - function.evaluate(x)) / h
    if function.domain.contains(left):
        return (function.evaluate(x) - function.evaluate(left)) / h
    raise ValueError("function domain is too narrow for derivative sampling")


def tangent_at(function: Function1D, x: float) -> TangentSample:
    return TangentSample(x=x, y=function.evaluate(x), slope=derivative_at(function, x))


def integrate(
    function: Function1D,
    *,
    start: float | None = None,
    end: float | None = None,
    steps: int = 512,
) -> float:
    """Numerically integrate a Function1D using composite Simpson's rule.

    This is a deterministic reference implementation behind a capability
    boundary. A future NumPy/SciPy/native/GPU integrator can replace it without
    changing probability/physics domains that consume `calculus.integrate`.
    """
    lower = function.domain.start if start is None else float(start)
    upper = function.domain.end if end is None else float(end)
    if upper <= lower:
        raise ValueError("integration end must be greater than start")
    if not function.domain.contains(lower) or not function.domain.contains(upper):
        raise ValueError("integration bounds must lie inside function domain")
    if steps < 2:
        raise ValueError("integration steps must be >= 2")
    if steps % 2:
        steps += 1

    width = (upper - lower) / steps
    total = function.evaluate(lower) + function.evaluate(upper)
    for index in range(1, steps):
        x = lower + index * width
        total += (4.0 if index % 2 else 2.0) * function.evaluate(x)
    return total * width / 3.0


def _field_step(step: float) -> float:
    value = float(step)
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError("field derivative step must be finite and positive")
    return value


def gradient_at(
    field: ScalarField3D,
    position: Vec3,
    *,
    step: float = 1e-5,
) -> Vec3:
    """Numerical gradient of a scalar field using central differences."""
    h = _field_step(step)
    dx = Vec3(h, 0.0, 0.0)
    dy = Vec3(0.0, h, 0.0)
    dz = Vec3(0.0, 0.0, h)
    return Vec3(
        (field.evaluate(position + dx) - field.evaluate(position - dx)) / (2.0 * h),
        (field.evaluate(position + dy) - field.evaluate(position - dy)) / (2.0 * h),
        (field.evaluate(position + dz) - field.evaluate(position - dz)) / (2.0 * h),
    )


def divergence_at(
    field: VectorField3D,
    position: Vec3,
    *,
    step: float = 1e-5,
) -> float:
    """Numerical divergence of a vector field using central differences."""
    h = _field_step(step)
    dx = Vec3(h, 0.0, 0.0)
    dy = Vec3(0.0, h, 0.0)
    dz = Vec3(0.0, 0.0, h)
    dfx_dx = (field.evaluate(position + dx).x - field.evaluate(position - dx).x) / (2.0 * h)
    dfy_dy = (field.evaluate(position + dy).y - field.evaluate(position - dy).y) / (2.0 * h)
    dfz_dz = (field.evaluate(position + dz).z - field.evaluate(position - dz).z) / (2.0 * h)
    return dfx_dx + dfy_dy + dfz_dz


def curl_at(
    field: VectorField3D,
    position: Vec3,
    *,
    step: float = 1e-5,
) -> Vec3:
    """Numerical curl of a vector field using central differences."""
    h = _field_step(step)
    dx = Vec3(h, 0.0, 0.0)
    dy = Vec3(0.0, h, 0.0)
    dz = Vec3(0.0, 0.0, h)

    fx_plus_x = field.evaluate(position + dx)
    fx_minus_x = field.evaluate(position - dx)
    fy_plus_y = field.evaluate(position + dy)
    fy_minus_y = field.evaluate(position - dy)
    fz_plus_z = field.evaluate(position + dz)
    fz_minus_z = field.evaluate(position - dz)

    dfz_dy = (fy_plus_y.z - fy_minus_y.z) / (2.0 * h)
    dfy_dz = (fz_plus_z.y - fz_minus_z.y) / (2.0 * h)
    dfx_dz = (fz_plus_z.x - fz_minus_z.x) / (2.0 * h)
    dfz_dx = (fx_plus_x.z - fx_minus_x.z) / (2.0 * h)
    dfy_dx = (fx_plus_x.y - fx_minus_x.y) / (2.0 * h)
    dfx_dy = (fy_plus_y.x - fy_minus_y.x) / (2.0 * h)

    return Vec3(
        dfz_dy - dfy_dz,
        dfx_dz - dfz_dx,
        dfy_dx - dfx_dy,
    )


class CalculusDomain:
    name = "calculus"
    version = "3"
    dependencies = (
        DomainDependency("mathematics.function1d"),
        DomainDependency("mathematics.scalar_field3d"),
        DomainDependency("mathematics.vector_field3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("calculus.tangent_sample", TangentSample)
        registry.provide("calculus.derivative_at", derivative_at)
        registry.provide("calculus.tangent_at", tangent_at)
        registry.provide("calculus.integrate", integrate, version=2)
        registry.provide("calculus.gradient_at", gradient_at, version=1)
        registry.provide("calculus.divergence_at", divergence_at, version=1)
        registry.provide("calculus.curl_at", curl_at, version=1)
