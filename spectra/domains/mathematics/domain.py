from __future__ import annotations

from spectra.core.expressions import compile_expression
from spectra.domains.mathematics.field_views import (
    ScalarFieldSurfaceView2D,
    TimeScalarFieldSurfaceAnimation2D,
    TimeVectorFieldAnimation3D,
    VectorFieldView3D,
)
from spectra.domains.mathematics.fields import (
    RegularGrid3D,
    ScalarField3D,
    TimeDependentScalarField3D,
    TimeDependentVectorField3D,
    VectorField3D,
)
from spectra.domains.mathematics.fields2d import (
    ScalarField2D,
    TimeDependentScalarField2D,
    TimeDependentVectorField2D,
    VectorField2D,
)
from spectra.domains.mathematics.functions import (
    CallableFunction1D,
    ComplexFunction1D,
    Function1D,
    Function2D,
    Interval,
    RealFunction1D,
    RectDomain2D,
)
from spectra.domains.mathematics.parametric import ParametricCurve3D, ParametricSurface3D
from spectra.domains.registry import DomainRegistry


class MathematicsDomain:
    name = "mathematics"
    version = "3"
    dependencies = ()

    def register(self, registry: DomainRegistry) -> None:
        # Import lazily so generic compilers can depend on mathematics semantic
        # types without making the domain module cyclic at import time.
        from spectra.compiler import compile_function1d, compile_function2d
        from spectra.domains.mathematics.field_visualization import (
            compile_scalar_field_surface_scene,
            compile_time_scalar_field_surface_animation_scene,
            compile_time_vector_field_animation_scene,
            compile_vector_field_view_scene,
        )
        from spectra.domains.mathematics.visualization import (
            compile_parametric_curve_scene,
            compile_parametric_surface_scene,
        )

        registry.register_semantic_type("mathematics.interval", Interval)
        registry.register_semantic_type("mathematics.rect_domain2d", RectDomain2D)
        registry.register_semantic_type("mathematics.function1d", Function1D)
        registry.register_semantic_type("mathematics.callable_function1d", CallableFunction1D)
        registry.register_semantic_type("mathematics.complex_function1d", ComplexFunction1D)
        registry.register_semantic_type("mathematics.function2d", Function2D)
        registry.register_semantic_type("mathematics.parametric_curve3d", ParametricCurve3D)
        registry.register_semantic_type("mathematics.parametric_surface3d", ParametricSurface3D)
        registry.register_semantic_type("mathematics.scalar_field2d", ScalarField2D)
        registry.register_semantic_type("mathematics.vector_field2d", VectorField2D)
        registry.register_semantic_type(
            "mathematics.time_scalar_field2d",
            TimeDependentScalarField2D,
        )
        registry.register_semantic_type(
            "mathematics.time_vector_field2d",
            TimeDependentVectorField2D,
        )
        registry.register_semantic_type("mathematics.scalar_field3d", ScalarField3D)
        registry.register_semantic_type("mathematics.vector_field3d", VectorField3D)
        registry.register_semantic_type(
            "mathematics.time_scalar_field3d",
            TimeDependentScalarField3D,
        )
        registry.register_semantic_type(
            "mathematics.time_vector_field3d",
            TimeDependentVectorField3D,
        )
        registry.register_semantic_type("mathematics.regular_grid3d", RegularGrid3D)
        registry.register_semantic_type("mathematics.vector_field_view3d", VectorFieldView3D)
        registry.register_semantic_type(
            "mathematics.time_vector_field_animation3d",
            TimeVectorFieldAnimation3D,
        )
        registry.register_semantic_type(
            "mathematics.scalar_field_surface_view2d",
            ScalarFieldSurfaceView2D,
        )
        registry.register_semantic_type(
            "mathematics.time_scalar_field_surface_animation2d",
            TimeScalarFieldSurfaceAnimation2D,
        )

        registry.provide("mathematics.compile_expression", compile_expression)
        registry.provide("mathematics.interval", Interval)
        registry.provide("mathematics.rect_domain2d", RectDomain2D)
        registry.provide("mathematics.real_function1d", RealFunction1D, version=1)
        registry.provide("mathematics.function1d", Function1D)
        registry.provide("mathematics.callable_function1d", CallableFunction1D)
        registry.provide("mathematics.complex_function1d", ComplexFunction1D)
        registry.provide("mathematics.function2d", Function2D)
        registry.provide("mathematics.parametric_curve3d", ParametricCurve3D)
        registry.provide("mathematics.parametric_surface3d", ParametricSurface3D)
        registry.provide("mathematics.scalar_field2d", ScalarField2D, version=1)
        registry.provide("mathematics.vector_field2d", VectorField2D, version=1)
        registry.provide("mathematics.time_scalar_field2d", TimeDependentScalarField2D, version=1)
        registry.provide("mathematics.time_vector_field2d", TimeDependentVectorField2D, version=1)
        registry.provide("mathematics.scalar_field3d", ScalarField3D)
        registry.provide("mathematics.vector_field3d", VectorField3D)
        registry.provide("mathematics.time_scalar_field3d", TimeDependentScalarField3D)
        registry.provide("mathematics.time_vector_field3d", TimeDependentVectorField3D)
        registry.provide("mathematics.regular_grid3d", RegularGrid3D)
        registry.provide("mathematics.vector_field_view3d", VectorFieldView3D)
        registry.provide(
            "mathematics.time_vector_field_animation3d",
            TimeVectorFieldAnimation3D,
        )
        registry.provide(
            "mathematics.scalar_field_surface_view2d",
            ScalarFieldSurfaceView2D,
        )
        registry.provide(
            "mathematics.time_scalar_field_surface_animation2d",
            TimeScalarFieldSurfaceAnimation2D,
        )

        registry.register_visualization(Function1D, compile_function1d)
        registry.register_visualization(CallableFunction1D, compile_function1d)
        registry.register_visualization(Function2D, compile_function2d)
        registry.register_visualization(ParametricCurve3D, compile_parametric_curve_scene)
        registry.register_visualization(ParametricSurface3D, compile_parametric_surface_scene)
        registry.register_visualization(VectorFieldView3D, compile_vector_field_view_scene)
        registry.register_visualization(
            TimeVectorFieldAnimation3D,
            compile_time_vector_field_animation_scene,
        )
        registry.register_visualization(
            ScalarFieldSurfaceView2D,
            compile_scalar_field_surface_scene,
        )
        registry.register_visualization(
            TimeScalarFieldSurfaceAnimation2D,
            compile_time_scalar_field_surface_animation_scene,
        )
