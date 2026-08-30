from __future__ import annotations

from dataclasses import dataclass

from spectra.core.types import Vec2
from spectra.core.units import HERTZ, METER_PER_SECOND, PASCAL
from spectra.domains.field_dynamics.domain2d import PathlineProblem2D
from spectra.domains.mathematics.field_views2d import (
    TimeScalarFieldHeightAnimation2D,
    TimeVectorFieldAnimation2D,
)
from spectra.domains.mathematics.fields import AxisSample
from spectra.domains.mathematics.fields2d import (
    TimeDependentScalarField2D,
    TimeDependentVectorField2D,
)
from spectra.domains.physics.incompressible_flow import IncompressibleFlowSolution2D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class IncompressibleFlowFields2D:
    """Continuous semantic field history reconstructed from a sampled CFD solution."""

    velocity: TimeDependentVectorField2D
    pressure: TimeDependentScalarField2D
    speed: TimeDependentScalarField2D
    vorticity: TimeDependentScalarField2D
    start_time: float
    end_time: float
    name: str = "incompressible_flow_fields2d"

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


def _axes(solution: IncompressibleFlowSolution2D) -> tuple[AxisSample, AxisSample]:
    grid = solution.grid
    return (
        AxisSample(grid.x.start, grid.x.end, grid.x.count),
        AxisSample(grid.y.start, grid.y.end, grid.y.count),
    )


class IncompressibleFlowViews2DDomain:
    """Adapters from sampled CFD history back into generic field semantics."""

    name = "physics.incompressible_flow.views2d"
    version = "1"
    dependencies = (
        DomainDependency("physics.incompressible_flow.solution2d", min_version=2),
        DomainDependency("pde.time_scalar_field_from_grid_2d", min_version=2),
        DomainDependency("pde.time_vector_field_from_grid_2d", min_version=2),
        DomainDependency("pde.curl_grid_2d", min_version=2),
        DomainDependency("field_dynamics.pathline_problem2d"),
        DomainDependency("mathematics.time_vector_field_animation2d"),
        DomainDependency("mathematics.time_scalar_field_height_animation2d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        time_scalar = registry.require("pde.time_scalar_field_from_grid_2d", min_version=2)
        time_vector = registry.require("pde.time_vector_field_from_grid_2d", min_version=2)
        curl = registry.require("pde.curl_grid_2d", min_version=2)
        pathline_type = registry.require("field_dynamics.pathline_problem2d")

        def fields_from_solution(
            solution: IncompressibleFlowSolution2D,
        ) -> IncompressibleFlowFields2D:
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
            return IncompressibleFlowFields2D(
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
                vorticity=time_scalar(
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
            solution: IncompressibleFlowSolution2D,
            *,
            temporal_samples: int | None = None,
            vector_scale: float = 1.0,
            plane_z: float = 0.0,
        ) -> TimeVectorFieldAnimation2D:
            fields = fields_from_solution(solution)
            x, y = _axes(solution)
            return TimeVectorFieldAnimation2D(
                field=fields.velocity,
                x=x,
                y=y,
                start_time=fields.start_time,
                end_time=fields.end_time,
                temporal_samples=temporal_samples or max(2, len(solution.states)),
                vector_scale=vector_scale,
                plane_z=plane_z,
                name=f"{solution.name}.velocity_view",
            )

        def scalar_animation(
            solution: IncompressibleFlowSolution2D,
            quantity: str,
            *,
            temporal_samples: int | None = None,
            height_scale: float = 1.0,
            base_z: float = 0.0,
        ) -> TimeScalarFieldHeightAnimation2D:
            fields = fields_from_solution(solution)
            selected = {
                "pressure": fields.pressure,
                "speed": fields.speed,
                "vorticity": fields.vorticity,
            }.get(quantity)
            if selected is None:
                raise ValueError("flow scalar view quantity must be pressure, speed, or vorticity")
            x, y = _axes(solution)
            return TimeScalarFieldHeightAnimation2D(
                field=selected,
                x=x,
                y=y,
                start_time=fields.start_time,
                end_time=fields.end_time,
                temporal_samples=temporal_samples or max(2, len(solution.states)),
                height_scale=height_scale,
                base_z=base_z,
                name=f"{solution.name}.{quantity}_view",
            )

        def pathline_problem(
            solution: IncompressibleFlowSolution2D,
            seed: Vec2,
            *,
            initial_time: float | None = None,
            name: str | None = None,
        ) -> PathlineProblem2D:
            fields = fields_from_solution(solution)
            start = fields.start_time if initial_time is None else float(initial_time)
            if start < fields.start_time or start > fields.end_time:
                raise ValueError("pathline initial_time must lie inside flow solution time range")
            return pathline_type(
                field=fields.velocity,
                initial_position=seed,
                initial_time=start,
                name=name or f"{solution.name}.pathline",
            )

        registry.register_semantic_type(
            "physics.incompressible_flow.fields2d",
            IncompressibleFlowFields2D,
        )
        registry.provide(
            "physics.incompressible_flow.fields_from_solution2d",
            fields_from_solution,
        )
        registry.provide(
            "physics.incompressible_flow.velocity_animation2d",
            velocity_animation,
        )
        registry.provide(
            "physics.incompressible_flow.scalar_animation2d",
            scalar_animation,
        )
        registry.provide(
            "physics.incompressible_flow.pathline_problem2d",
            pathline_problem,
        )
