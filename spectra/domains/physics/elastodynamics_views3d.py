from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.animation import Keyframe, Timeline, Track
from spectra.core.primitives import PointCloud
from spectra.core.scene import Scene
from spectra.core.types import Vec3
from spectra.core.units import METER, METER_PER_SECOND
from spectra.domains.mathematics.field_views import TimeVectorFieldAnimation3D
from spectra.domains.mathematics.fields import AxisSample, RegularGrid3D, TimeDependentVectorField3D
from spectra.domains.physics.elastodynamics3d import ElastodynamicsSolution3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class ElastodynamicsFields3D:
    displacement: TimeDependentVectorField3D
    velocity: TimeDependentVectorField3D
    start_time: float
    end_time: float
    name: str = "elastodynamics_fields3d"

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


@dataclass(frozen=True, slots=True)
class ElastodynamicsDeformedGridView3D:
    solution: ElastodynamicsSolution3D
    displacement_scale: float = 1.0
    point_radius: float = 0.03
    name: str = "elastodynamics_deformed_grid3d"

    def __post_init__(self) -> None:
        if not math.isfinite(self.displacement_scale):
            raise ValueError("elastodynamics displacement scale must be finite")
        if not math.isfinite(self.point_radius) or self.point_radius < 0.0:
            raise ValueError("elastodynamics point radius must be finite and non-negative")
        if not self.name:
            raise ValueError("elastodynamics deformed-grid view name cannot be empty")


def _regular_grid(solution: ElastodynamicsSolution3D) -> RegularGrid3D:
    grid = solution.grid
    return RegularGrid3D(
        AxisSample(grid.x.start, grid.x.end, grid.x.count),
        AxisSample(grid.y.start, grid.y.end, grid.y.count),
        AxisSample(grid.z.start, grid.z.end, grid.z.count),
    )


def _compile_deformed_grid(view: ElastodynamicsDeformedGridView3D) -> Scene:
    solution = view.solution
    base_positions = tuple(Vec3(x, y, z) for x, y, z in solution.grid.coordinates)
    position_states = tuple(
        tuple(
            base + displacement * view.displacement_scale
            for base, displacement in zip(base_positions, state, strict=True)
        )
        for state in solution.displacements
    )
    if len(position_states) < 2:
        raise ValueError("elastodynamics animation requires at least two time samples")
    start_time = solution.times[0]
    relative_times = tuple(time - start_time for time in solution.times)
    cloud_id = f"{view.name}.points"
    cloud = PointCloud(
        id=cloud_id,
        positions=position_states[0],
        radius=view.point_radius,
    )
    track = Track(
        target_id=cloud_id,
        property_path="positions",
        keyframes=tuple(
            Keyframe(time, positions, "linear")
            for time, positions in zip(relative_times, position_states, strict=True)
        ),
    )
    return Scene(
        primitives=(cloud,),
        timeline=Timeline(duration=relative_times[-1], tracks=(track,)),
    )


class ElastodynamicsViews3DDomain:
    """Adapters from sampled solid motion back into generic fields and Scene views."""

    name = "physics.elastodynamics.views3d"
    version = "1"
    dependencies = (
        DomainDependency("physics.elastodynamics.solution3d"),
        DomainDependency("pde.time_vector_field_from_grid_3d", min_version=2),
        DomainDependency("mathematics.time_vector_field_animation3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        time_vector = registry.require("pde.time_vector_field_from_grid_3d", min_version=2)

        def fields_from_solution(solution: ElastodynamicsSolution3D) -> ElastodynamicsFields3D:
            return ElastodynamicsFields3D(
                displacement=time_vector(
                    solution.grid,
                    solution.times,
                    solution.displacements,
                    name=f"{solution.name}.displacement",
                    output_unit=METER,
                    temporal_outside="clamp",
                ),
                velocity=time_vector(
                    solution.grid,
                    solution.times,
                    solution.velocities,
                    name=f"{solution.name}.velocity",
                    output_unit=METER_PER_SECOND,
                    temporal_outside="clamp",
                ),
                start_time=solution.times[0],
                end_time=solution.times[-1],
                name=f"{solution.name}.fields",
            )

        def displacement_animation(
            solution: ElastodynamicsSolution3D,
            *,
            temporal_samples: int | None = None,
            vector_scale: float = 1.0,
        ) -> TimeVectorFieldAnimation3D:
            fields = fields_from_solution(solution)
            return TimeVectorFieldAnimation3D(
                field=fields.displacement,
                grid=_regular_grid(solution),
                start_time=fields.start_time,
                end_time=fields.end_time,
                temporal_samples=temporal_samples or max(2, len(solution.times)),
                vector_scale=vector_scale,
                name=f"{solution.name}.displacement_vectors",
            )

        def deformed_grid_view(
            solution: ElastodynamicsSolution3D,
            *,
            displacement_scale: float = 1.0,
            point_radius: float = 0.03,
        ) -> ElastodynamicsDeformedGridView3D:
            return ElastodynamicsDeformedGridView3D(
                solution=solution,
                displacement_scale=displacement_scale,
                point_radius=point_radius,
                name=f"{solution.name}.deformed_grid",
            )

        registry.register_semantic_type(
            "physics.elastodynamics.fields3d",
            ElastodynamicsFields3D,
        )
        registry.register_semantic_type(
            "physics.elastodynamics.deformed_grid_view3d",
            ElastodynamicsDeformedGridView3D,
        )
        registry.provide(
            "physics.elastodynamics.fields_from_solution3d",
            fields_from_solution,
        )
        registry.provide(
            "physics.elastodynamics.displacement_animation3d",
            displacement_animation,
        )
        registry.provide(
            "physics.elastodynamics.deformed_grid_view3d",
            deformed_grid_view,
        )
        registry.register_visualization(
            ElastodynamicsDeformedGridView3D,
            _compile_deformed_grid,
        )
