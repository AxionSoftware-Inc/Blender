from __future__ import annotations

from dataclasses import dataclass

from spectra.core.units import NEWTON_PER_COULOMB, TESLA
from spectra.domains.mathematics.field_views import TimeVectorFieldAnimation3D
from spectra.domains.mathematics.fields import (
    AxisSample,
    RegularGrid3D,
    TimeDependentVectorField3D,
)
from spectra.domains.physics.maxwell3d import MaxwellSolution3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class MaxwellFields3D:
    electric: TimeDependentVectorField3D
    magnetic: TimeDependentVectorField3D
    start_time: float
    end_time: float
    name: str = "maxwell_fields3d"

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


def _regular_grid(solution: MaxwellSolution3D) -> RegularGrid3D:
    grid = solution.grid
    return RegularGrid3D(
        AxisSample(grid.x.start, grid.x.end, grid.x.count),
        AxisSample(grid.y.start, grid.y.end, grid.y.count),
        AxisSample(grid.z.start, grid.z.end, grid.z.count),
    )


class MaxwellViews3DDomain:
    """Adapters from sampled Maxwell histories back into generic vector fields/views."""

    name = "physics.electromagnetism.maxwell_views3d"
    version = "1"
    dependencies = (
        DomainDependency("physics.maxwell.solution3d"),
        DomainDependency("pde.time_vector_field_from_grid_3d", min_version=2),
        DomainDependency("mathematics.time_vector_field_animation3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        time_vector = registry.require("pde.time_vector_field_from_grid_3d", min_version=2)

        def fields_from_solution(solution: MaxwellSolution3D) -> MaxwellFields3D:
            return MaxwellFields3D(
                electric=time_vector(
                    solution.grid,
                    solution.times,
                    solution.electric_states,
                    name=f"{solution.name}.electric",
                    output_unit=NEWTON_PER_COULOMB,
                    temporal_outside="clamp",
                ),
                magnetic=time_vector(
                    solution.grid,
                    solution.times,
                    solution.magnetic_states,
                    name=f"{solution.name}.magnetic",
                    output_unit=TESLA,
                    temporal_outside="clamp",
                ),
                start_time=solution.times[0],
                end_time=solution.times[-1],
                name=f"{solution.name}.fields",
            )

        def electric_animation(
            solution: MaxwellSolution3D,
            *,
            temporal_samples: int | None = None,
            vector_scale: float = 1.0,
        ) -> TimeVectorFieldAnimation3D:
            fields = fields_from_solution(solution)
            return TimeVectorFieldAnimation3D(
                field=fields.electric,
                grid=_regular_grid(solution),
                start_time=fields.start_time,
                end_time=fields.end_time,
                temporal_samples=temporal_samples or max(2, len(solution.times)),
                vector_scale=vector_scale,
                name=f"{solution.name}.electric_vectors",
            )

        def magnetic_animation(
            solution: MaxwellSolution3D,
            *,
            temporal_samples: int | None = None,
            vector_scale: float = 1.0,
        ) -> TimeVectorFieldAnimation3D:
            fields = fields_from_solution(solution)
            return TimeVectorFieldAnimation3D(
                field=fields.magnetic,
                grid=_regular_grid(solution),
                start_time=fields.start_time,
                end_time=fields.end_time,
                temporal_samples=temporal_samples or max(2, len(solution.times)),
                vector_scale=vector_scale,
                name=f"{solution.name}.magnetic_vectors",
            )

        registry.register_semantic_type("physics.maxwell.fields3d", MaxwellFields3D)
        registry.provide("physics.maxwell.fields_from_solution3d", fields_from_solution)
        registry.provide("physics.maxwell.electric_animation3d", electric_animation)
        registry.provide("physics.maxwell.magnetic_animation3d", magnetic_animation)
