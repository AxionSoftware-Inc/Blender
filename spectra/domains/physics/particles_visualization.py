from __future__ import annotations

from spectra.core.animation import Keyframe, Timeline, Track
from spectra.core.primitives import PointCloud
from spectra.core.scene import Scene
from spectra.domains.physics.particles import ParticleSystemTrajectory


def compile_particle_system_scene(
    trajectory: ParticleSystemTrajectory,
    *,
    primitive_id: str | None = None,
) -> Scene:
    """Compile many-body motion into one animated batched PointCloud."""
    if len(trajectory.times) < 2:
        raise ValueError("particle-system visualization requires at least two time samples")

    start_time = trajectory.times[0]
    relative_times = tuple(time - start_time for time in trajectory.times)
    if any(time < 0.0 for time in relative_times):
        raise ValueError("particle-system times must be monotonic")

    cloud_id = primitive_id or f"{trajectory.name}.particles"
    cloud = PointCloud(
        id=cloud_id,
        positions=trajectory.positions[0],
        radii=trajectory.radii,
        colors=trajectory.colors,
    )
    position_track = Track(
        target_id=cloud_id,
        property_path="positions",
        keyframes=tuple(
            Keyframe(time, positions, "linear")
            for time, positions in zip(relative_times, trajectory.positions, strict=True)
        ),
    )
    return Scene(
        primitives=(cloud,),
        timeline=Timeline(duration=relative_times[-1], tracks=(position_track,)),
    )
