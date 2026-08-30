from __future__ import annotations

from dataclasses import dataclass

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


class CalculusDomain:
    name = "calculus"
    version = "2"
    dependencies = (
        DomainDependency("mathematics.function1d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("calculus.tangent_sample", TangentSample)
        registry.provide("calculus.derivative_at", derivative_at)
        registry.provide("calculus.tangent_at", tangent_at)
        registry.provide("calculus.integrate", integrate, version=2)
