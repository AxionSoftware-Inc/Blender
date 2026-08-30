from __future__ import annotations

from dataclasses import dataclass

from spectra.core.types import Vec3
from spectra.domains.field_dynamics import IntegralCurveBundleProblem3D
from spectra.domains.mathematics import (
    AxisSample,
    RegularGrid3D,
    ScalarField3D,
    ScalarFieldSliceSurface3D,
    VectorField3D,
    VectorFieldView3D,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class PotentialField3D:
    """A scalar potential paired with its associated physical vector field."""

    potential: ScalarField3D
    field: VectorField3D
    name: str = "potential_field3d"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("potential field name cannot be empty")


class PotentialFields3DDomain:
    """Common potential-field semantic layer shared by gravity and electrostatics."""

    name = "physics.potential_fields.3d"
    version = "1"
    dependencies = (
        DomainDependency("mathematics.scalar_field3d"),
        DomainDependency("mathematics.vector_field3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("physics.potential_field3d", PotentialField3D)
        registry.provide("physics.potential_field3d", PotentialField3D)


class PotentialFieldViews3DDomain:
    """Renderer-neutral view constructors for any PotentialField3D."""

    name = "physics.potential_fields.views3d"
    version = "1"
    dependencies = (
        DomainDependency("physics.potential_field3d"),
        DomainDependency("mathematics.scalar_field_slice_surface3d"),
        DomainDependency("mathematics.vector_field_view3d"),
        DomainDependency("field_dynamics.integral_curve_bundle_problem3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        slice_type = registry.require("mathematics.scalar_field_slice_surface3d")
        vector_view_type = registry.require("mathematics.vector_field_view3d")
        bundle_type = registry.require("field_dynamics.integral_curve_bundle_problem3d")

        def scalar_slice(
            potential_field: PotentialField3D,
            *,
            axis: str,
            coordinate: float,
            u: AxisSample,
            v: AxisSample,
            height_scale: float = 1.0,
            name: str | None = None,
        ) -> ScalarFieldSliceSurface3D:
            return slice_type(
                field=potential_field.potential,
                axis=axis,
                coordinate=coordinate,
                u=u,
                v=v,
                height_scale=height_scale,
                name=name or f"{potential_field.name}.potential_slice",
            )

        def vector_view(
            potential_field: PotentialField3D,
            grid: RegularGrid3D,
            *,
            vector_scale: float = 1.0,
            name: str | None = None,
        ) -> VectorFieldView3D:
            return vector_view_type(
                field=potential_field.field,
                grid=grid,
                vector_scale=vector_scale,
                name=name or f"{potential_field.name}.field_view",
            )

        def field_lines(
            potential_field: PotentialField3D,
            seeds: tuple[Vec3, ...],
            *,
            parameter_length: float,
            steps_per_direction: int = 128,
            mode: str = "normalized",
            bidirectional: bool = True,
            name: str | None = None,
        ) -> IntegralCurveBundleProblem3D:
            return bundle_type(
                field=potential_field.field,
                seeds=seeds,
                parameter_length=parameter_length,
                steps_per_direction=steps_per_direction,
                mode=mode,
                bidirectional=bidirectional,
                name=name or f"{potential_field.name}.field_lines",
            )

        registry.provide("physics.potential_fields.scalar_slice3d", scalar_slice)
        registry.provide("physics.potential_fields.vector_view3d", vector_view)
        registry.provide("physics.potential_fields.field_lines3d", field_lines)
