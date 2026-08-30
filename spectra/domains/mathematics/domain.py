from __future__ import annotations

from spectra.core.expressions import compile_expression
from spectra.domains.mathematics.fields import RegularGrid3D, ScalarField3D, VectorField3D
from spectra.domains.mathematics.functions import Function1D, Function2D, Interval, RectDomain2D
from spectra.domains.registry import DomainRegistry


class MathematicsDomain:
    name = "mathematics"
    version = "1"
    dependencies = ()

    def register(self, registry: DomainRegistry) -> None:
        # Import lazily so the generic compiler can depend on mathematics
        # semantic types without making the domain module cyclic at import time.
        from spectra.compiler import compile_function1d, compile_function2d

        registry.register_semantic_type("mathematics.interval", Interval)
        registry.register_semantic_type("mathematics.rect_domain2d", RectDomain2D)
        registry.register_semantic_type("mathematics.function1d", Function1D)
        registry.register_semantic_type("mathematics.function2d", Function2D)
        registry.register_semantic_type("mathematics.scalar_field3d", ScalarField3D)
        registry.register_semantic_type("mathematics.vector_field3d", VectorField3D)
        registry.register_semantic_type("mathematics.regular_grid3d", RegularGrid3D)

        registry.provide("mathematics.compile_expression", compile_expression)
        registry.provide("mathematics.interval", Interval)
        registry.provide("mathematics.rect_domain2d", RectDomain2D)
        registry.provide("mathematics.function1d", Function1D)
        registry.provide("mathematics.function2d", Function2D)
        registry.provide("mathematics.scalar_field3d", ScalarField3D)
        registry.provide("mathematics.vector_field3d", VectorField3D)
        registry.provide("mathematics.regular_grid3d", RegularGrid3D)

        registry.register_visualization(Function1D, compile_function1d)
        registry.register_visualization(Function2D, compile_function2d)
