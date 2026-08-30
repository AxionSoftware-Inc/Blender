from __future__ import annotations

from dataclasses import dataclass

from spectra.core.types import Vec3
from spectra.core.units import HERTZ, METER_PER_SECOND, PASCAL
from spectra.domains.mathematics.field_views import (
    TimeScalarFieldSurfaceAnimation2D,
    TimeVectorFieldAnimation3D,
)
from spectra.domains.mathematics.fields import (
    AxisSample,
    RegularGrid3D,
    TimeDependentScalarField3D,
    TimeDependentVectorField3D,
)
from spectra.domains.physics.incompressible_flow3d import IncompressibleFlowSolution3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class IncompressibleFlowFields3D:
    velocity: TimeDependentVectorField3D
    pressure: TimeDependentScalarField3D
    speed: TimeDependentScalarField3D
    vorticity: TimeDependentVectorField3D
    start_time: float
    end_time: float
    name: str = "incompressible_flow_fields3d"

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


def _regular_grid(solution: IncompressibleFlowSolution3D) -> RegularGrid3D:
    grid = solution.grid
    return RegularGrid3D(
        AxisSample(grid.x.start, grid.x.end, grid.x.count),
        AxisSample(grid.y.start, grid.y.end, grid.y.count),
        AxisSample(grid.z.start, grid.z.end, grid.z.count),
    )


class IncompressibleFlowViews3DDomain:
    """Reconstruct continuous field semantics and views from sampled 3D CFD history."""

    name = "physics.incompressible_flow.views3d"
    version = "1"
    dependencies = (
        DomainDependency("physics.incompressible_flow.solution3d"),
        DomainDependency("pde.time_scalar_field_from_grid_3d"),
        DomainDependency("pde.time_vector_field_from_grid_3d"),
        DomainDependency("pde.curl_grid_3d"),
        DomainDependency("field_dynamics.pathline_problem3d"),
        DomainDependency("mathematics.time_vector_field_animation3d"),
        DomainDependency("mathematics.time_scalar_field_surface_animation2d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        time_scalar = registry.require("pde.time_scalar_field_from_grid_3d")
        time_vector = registry.require("pde.time_vector_field_from_grid_3d")
        curl = registry.require("pde.curl_grid_3d")
        pathline_type = registry.require("field_dynamics.pathline_problem3d")

        def fields_from_solution(
            solution: IncompressibleFlowSolution3D,
        ) -> IncompressibleFlowFields3D:
            times = solution.times
            velocity_states = tuple(state.velocity for state in solution.states)
            pressure_states = tuple(state.pressure for state in solution.states)
            speed_states = tuple(
                tuple(vector.magnitude for vector in state.velocity)
                for state in solution.states
            )
            vorticity_states = tuple(
                curl(
                    state.velocity,
                    solution.grid,
                    boundary=solution.velocity_boundary,
                )
                for state in solution.states
            )
            return IncompressibleFlowFields3D(
                velocity=time_vector(
                    solution.grid,
                    times,
                    velocity_states,
                    name=f"{solution.name}.velocity",
                    output_unit=METER_PER_SECOND,
                    temporal_outside="clamp",
                ),
                pressure=time_scalar(
                    solution.grid,
                    times,
                    pressure_states,
                    name=f"{solution.name}.pressure",
                    output_unit=PASCAL,
                    temporal_outside="clamp",
                ),
                speed=time_scalar(
                    solution.grid,
                    times,
                    speed_states,
                    name=f"{solution.name}.speed",
                    output_unit=METER_PER_SECOND,
                    temporal_outside="clamp",
                ),
                vorticity=time_vector(
                    solution.grid,
                    times,
                    vorticity_states,
                    name=f"{solution.name}.vorticity",
                    output_unit=HERTZ,
                    temporal_outside="clamp",
                ),
                start_time=times[0],
                end_time=times[-1],
                name=f"{solution.name}.fields",
            )

        def velocity_animation(
            solution: IncompressibleFlowSolution3D,
            *,
            temporal_samples: int | None = None,
            vector_scale: float = 1.0,
        ) -> TimeVectorFieldAnimation3D:
            fields = fields_from_solution(solution)
            return TimeVectorFieldAnimation3D(
                field=fields.velocity,
                grid=_regular_grid(solution),
                start_time=fields.start_time,
                end_time=fields.end_time,
                temporal_samples=temporal_samples or max(2, len(solution.states)),
                vector_scale=vector_scale,
                name=f"{solution.name}.velocity_view",
            )

        def scalar_z_slice_animation(
            solution: IncompressibleFlowSolution3D,
            quantity: str,
            *,
            plane_z: float,
            temporal_samples: int | None = None,
            height_scale: float = 1.0,
        ) -> TimeScalarFieldSurfaceAnimation2D:
            fields = fields_from_solution(solution)
            selected = {
                "pressure": fields.pressure,
                "speed": fields.speed,
            }.get(quantity)
            if selected is None:
                raise ValueError("3D flow scalar view quantity must be pressure or speed")
            grid = solution.grid
            return TimeScalarFieldSurfaceAnimation2D(
                field=selected,
                x=AxisSample(grid.x.start, grid.x.end, grid.x.count),
                y=AxisSample(grid.y.start, grid.y.end, grid.y.count),
                start_time=fields.start_time,
                end_time=fields.end_time,
                temporal_samples=temporal_samples or max(2, len(solution.states)),
                plane_z=plane_z,
                height_scale=height_scale,
                name=f"{solution.name}.{quantity}_z_slice",
            )

        def pathline_problem(
            solution: IncompressibleFlowSolution3D,
            seed: Vec3,
            *,
            initial_time: float | None = None,
            name: str | None = None,
        ):
            fields = fields_from_solution(solution)
            start = fields.start_time if initial_time is None else float(initial_time)
            if start < fields.start_time or start > fields.end_time:
                raise ValueError("3D pathline initial_time must lie inside flow solution time range")
            return pathline_type(
                field=fields.velocity,
                initial_position=seed,
                initial_time=start,
                name=name or f"{solution.name}.pathline",
            )

        registry.register_semantic_type(
            "physics.incompressible_flow.fields3d",
            IncompressibleFlowFields3D,
        )
        registry.provide(
            "physics.incompressible_flow.fields_from_solution3d",
            fields_from_solution,
        )
        registry.provide(
            "physics.incompressible_flow.velocity_animation3d",
            velocity_animation,
        )
        registry.provide(
            "physics.incompressible_flow.scalar_z_slice_animation3d",
            scalar_z_slice_animation,
        )
        registry.provide(
            "physics.incompressible_flow.pathline_problem3d",
            pathline_problem,
        )
