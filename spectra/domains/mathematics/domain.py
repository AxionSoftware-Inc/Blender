from __future__ import annotations

from spectra.core.expressions import compile_expression
from spectra.domains.mathematics.functions import Function1D, Interval
from spectra.domains.registry import DomainRegistry


class MathematicsDomain:
    name = "mathematics"
    version = "1"

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("mathematics.interval", Interval)
        registry.register_semantic_type("mathematics.function1d", Function1D)
        registry.provide("mathematics.compile_expression", compile_expression)
        registry.provide("mathematics.interval", Interval)
        registry.provide("mathematics.function1d", Function1D)
