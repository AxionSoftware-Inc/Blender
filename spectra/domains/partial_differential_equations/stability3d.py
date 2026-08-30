from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec3
from spectra.domains.mathematics.fields import TimeDependentVectorField3D, VectorField3D
from spectra.domains.partial_differential_equations.domain3d import UniformGrid3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class ExplicitStability3D:
    """Conservative solver-neutral stability envelope for explicit 3D transport."""

    dt: float
    max_abs_velocity_x: float
    max_abs_velocity_y: float
    max_abs_velocity_z: float
    cfl_x: float
    cfl_y: float
    cfl_z: float
    cfl_sum: float
    diffusion_number: float
    conservative_load: float
    suggested_max_dt: float
    within_conservative_envelope: bool


def _validate_inputs(
    grid: UniformGrid3D,
    dt: float,
    diffusivity: float,
    safety: float,
) -> tuple[float, float, float]:
    step = float(dt)
    diffusion = float(diffusivity)
    safety_factor = float(safety)
    if not math.isfinite(step) or step <= 0.0:
        raise ValueError("3D stability dt must be finite and positive")
    if not math.isfinite(diffusion) or diffusion < 0.0:
        raise ValueError("3D stability diffusivity must be finite and non-negative")
    if not math.isfinite(safety_factor) or not 0.0 < safety_factor <= 1.0:
        raise ValueError("3D stability safety factor must lie in (0, 1]")
    return step, diffusion, safety_factor


def explicit_stability_from_samples_3d(
    grid: UniformGrid3D,
    velocities: tuple[Vec3, ...],
    *,
    dt: float,
    diffusivity: float = 0.0,
    safety: float = 0.9,
) -> ExplicitStability3D:
    step, diffusion, safety_factor = _validate_inputs(grid, dt, diffusivity, safety)
    if len(velocities) != grid.count:
        raise ValueError("3D stability velocity sample count must match grid")
    if any(not isinstance(vector, Vec3) for vector in velocities):
        raise TypeError("3D stability velocity samples must be Vec3")

    max_x = max((abs(vector.x) for vector in velocities), default=0.0)
    max_y = max((abs(vector.y) for vector in velocities), default=0.0)
    max_z = max((abs(vector.z) for vector in velocities), default=0.0)
    advective_rate = (
        max_x / grid.x.spacing
        + max_y / grid.y.spacing
        + max_z / grid.z.spacing
    )
    inverse_square_sum = (
        1.0 / (grid.x.spacing * grid.x.spacing)
        + 1.0 / (grid.y.spacing * grid.y.spacing)
        + 1.0 / (grid.z.spacing * grid.z.spacing)
    )
    diffusion_rate = 2.0 * diffusion * inverse_square_sum
    total_rate = advective_rate + diffusion_rate
    suggested = math.inf if total_rate == 0.0 else safety_factor / total_rate

    cfl_x = step * max_x / grid.x.spacing
    cfl_y = step * max_y / grid.y.spacing
    cfl_z = step * max_z / grid.z.spacing
    cfl_sum = cfl_x + cfl_y + cfl_z
    diffusion_number = diffusion * step * inverse_square_sum
    load = cfl_sum + 2.0 * diffusion_number

    return ExplicitStability3D(
        dt=step,
        max_abs_velocity_x=max_x,
        max_abs_velocity_y=max_y,
        max_abs_velocity_z=max_z,
        cfl_x=cfl_x,
        cfl_y=cfl_y,
        cfl_z=cfl_z,
        cfl_sum=cfl_sum,
        diffusion_number=diffusion_number,
        conservative_load=load,
        suggested_max_dt=suggested,
        within_conservative_envelope=load <= 1.0,
    )


def explicit_stability_for_field_3d(
    grid: UniformGrid3D,
    field: VectorField3D | TimeDependentVectorField3D,
    *,
    dt: float,
    diffusivity: float = 0.0,
    time: float | None = None,
    safety: float = 0.9,
) -> ExplicitStability3D:
    if isinstance(field, TimeDependentVectorField3D):
        if time is None:
            raise ValueError("time is required for a time-dependent 3D velocity field")
        velocities = tuple(
            field.evaluate(Vec3(x, y, z), float(time))
            for x, y, z in grid.coordinates
        )
    elif isinstance(field, VectorField3D):
        velocities = tuple(field.evaluate(Vec3(x, y, z)) for x, y, z in grid.coordinates)
    else:
        raise TypeError("3D stability field must be VectorField3D or TimeDependentVectorField3D")
    return explicit_stability_from_samples_3d(
        grid,
        velocities,
        dt=dt,
        diffusivity=diffusivity,
        safety=safety,
    )


class Stability3DDomain:
    name = "partial_differential_equations.stability3d"
    version = "1"
    dependencies = (
        DomainDependency("pde.uniform_grid3d"),
        DomainDependency("mathematics.vector_field3d"),
        DomainDependency("mathematics.time_vector_field3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("pde.explicit_stability3d", ExplicitStability3D)
        registry.provide("pde.explicit_stability_from_samples_3d", explicit_stability_from_samples_3d)
        registry.provide("pde.explicit_stability_for_field_3d", explicit_stability_for_field_3d)
