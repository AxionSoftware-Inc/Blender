from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec2
from spectra.domains.mathematics.fields2d import TimeDependentVectorField2D, VectorField2D
from spectra.domains.partial_differential_equations.domain2d import UniformGrid2D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class ExplicitStability2D:
    """Conservative explicit finite-difference transport stability diagnostics.

    This is intentionally solver-neutral. It is a conservative envelope useful
    for authoring/reference solvers, not a proof of RK4 or production-CFD
    stability. Faster/native solvers may publish their own stronger contracts.
    """

    dt: float
    max_abs_velocity_x: float
    max_abs_velocity_y: float
    cfl_x: float
    cfl_y: float
    cfl_sum: float
    diffusion_number: float
    conservative_load: float
    suggested_max_dt: float
    within_conservative_envelope: bool


def _validate_inputs(
    grid: UniformGrid2D,
    dt: float,
    diffusivity: float,
    safety: float,
) -> tuple[float, float, float]:
    step = float(dt)
    diffusion = float(diffusivity)
    safety_factor = float(safety)
    if not math.isfinite(step) or step <= 0.0:
        raise ValueError("stability dt must be finite and positive")
    if not math.isfinite(diffusion) or diffusion < 0.0:
        raise ValueError("stability diffusivity must be finite and non-negative")
    if not math.isfinite(safety_factor) or not 0.0 < safety_factor <= 1.0:
        raise ValueError("stability safety factor must lie in (0, 1]")
    if grid.x.spacing <= 0.0 or grid.y.spacing <= 0.0:
        raise ValueError("stability grid spacing must be positive")
    return step, diffusion, safety_factor


def explicit_stability_from_samples_2d(
    grid: UniformGrid2D,
    velocities: tuple[Vec2, ...],
    *,
    dt: float,
    diffusivity: float = 0.0,
    safety: float = 0.9,
) -> ExplicitStability2D:
    step, diffusion, safety_factor = _validate_inputs(grid, dt, diffusivity, safety)
    if len(velocities) != grid.count:
        raise ValueError("stability velocity sample count must match grid")
    if any(not isinstance(vector, Vec2) for vector in velocities):
        raise TypeError("stability velocity samples must be Vec2")

    max_x = max((abs(vector.x) for vector in velocities), default=0.0)
    max_y = max((abs(vector.y) for vector in velocities), default=0.0)
    advective_rate = max_x / grid.x.spacing + max_y / grid.y.spacing
    diffusion_rate = 2.0 * diffusion * (
        1.0 / (grid.x.spacing * grid.x.spacing)
        + 1.0 / (grid.y.spacing * grid.y.spacing)
    )
    total_rate = advective_rate + diffusion_rate
    suggested = math.inf if total_rate == 0.0 else safety_factor / total_rate

    cfl_x = step * max_x / grid.x.spacing
    cfl_y = step * max_y / grid.y.spacing
    cfl_sum = cfl_x + cfl_y
    diffusion_number = diffusion * step * (
        1.0 / (grid.x.spacing * grid.x.spacing)
        + 1.0 / (grid.y.spacing * grid.y.spacing)
    )
    load = cfl_sum + 2.0 * diffusion_number

    return ExplicitStability2D(
        dt=step,
        max_abs_velocity_x=max_x,
        max_abs_velocity_y=max_y,
        cfl_x=cfl_x,
        cfl_y=cfl_y,
        cfl_sum=cfl_sum,
        diffusion_number=diffusion_number,
        conservative_load=load,
        suggested_max_dt=suggested,
        within_conservative_envelope=load <= 1.0,
    )


def explicit_stability_for_field_2d(
    grid: UniformGrid2D,
    field: VectorField2D | TimeDependentVectorField2D,
    *,
    dt: float,
    diffusivity: float = 0.0,
    time: float | None = None,
    safety: float = 0.9,
) -> ExplicitStability2D:
    if isinstance(field, TimeDependentVectorField2D):
        if time is None:
            raise ValueError("time is required for a time-dependent velocity field")
        velocities = tuple(
            field.evaluate(Vec2(x, y), float(time)) for x, y in grid.coordinates
        )
    elif isinstance(field, VectorField2D):
        velocities = tuple(field.evaluate(Vec2(x, y)) for x, y in grid.coordinates)
    else:
        raise TypeError("stability field must be VectorField2D or TimeDependentVectorField2D")
    return explicit_stability_from_samples_2d(
        grid,
        velocities,
        dt=dt,
        diffusivity=diffusivity,
        safety=safety,
    )


class Stability2DDomain:
    name = "partial_differential_equations.stability2d"
    version = "1"
    dependencies = (
        DomainDependency("pde.uniform_grid2d"),
        DomainDependency("mathematics.vector_field2d"),
        DomainDependency("mathematics.time_vector_field2d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("pde.explicit_stability2d", ExplicitStability2D)
        registry.provide("pde.explicit_stability_from_samples_2d", explicit_stability_from_samples_2d)
        registry.provide("pde.explicit_stability_for_field_2d", explicit_stability_for_field_2d)
