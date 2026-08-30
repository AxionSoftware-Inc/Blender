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


class CalculusDomain:
    name = "calculus"
    version = "1"
    dependencies = (
        DomainDependency("mathematics.function1d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("calculus.tangent_sample", TangentSample)
        registry.provide("calculus.derivative_at", derivative_at)
        registry.provide("calculus.tangent_at", tangent_at)
