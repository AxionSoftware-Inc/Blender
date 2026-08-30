from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec3
from spectra.domains.partial_differential_equations.domain3d import BoundaryMode3D, UniformGrid3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class ContinuityResidualSnapshot3D:
    time: float
    max_abs_residual: float
    l2_residual: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.time):
            raise ValueError("continuity diagnostic time must be finite")
        if not math.isfinite(self.max_abs_residual) or self.max_abs_residual < 0.0:
            raise ValueError("continuity max residual must be finite and non-negative")
        if not math.isfinite(self.l2_residual) or self.l2_residual < 0.0:
            raise ValueError("continuity L2 residual must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class ContinuityResidualHistory3D:
    snapshots: tuple[ContinuityResidualSnapshot3D, ...]
    name: str = "continuity_residual3d"

    def __post_init__(self) -> None:
        if not self.snapshots:
            raise ValueError("continuity residual history cannot be empty")
        if any(right.time <= left.time for left, right in zip(self.snapshots, self.snapshots[1:])):
            raise ValueError("continuity diagnostic times must be strictly increasing")

    @property
    def worst_max_abs_residual(self) -> float:
        return max(snapshot.max_abs_residual for snapshot in self.snapshots)

    @property
    def worst_l2_residual(self) -> float:
        return max(snapshot.l2_residual for snapshot in self.snapshots)


class ConservationDiagnostics3DDomain:
    """Solver-neutral continuity-equation verification on sampled 3D histories."""

    name = "partial_differential_equations.conservation3d"
    version = "1"
    dependencies = (
        DomainDependency("pde.uniform_grid3d"),
        DomainDependency("pde.divergence_grid_3d"),
        DomainDependency("pde.integrate_scalar_grid_3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        divergence = registry.require("pde.divergence_grid_3d")
        integrate_scalar = registry.require("pde.integrate_scalar_grid_3d")

        def continuity_history(
            grid: UniformGrid3D,
            times: tuple[float, ...],
            density_states: tuple[tuple[float, ...], ...],
            flux_states: tuple[tuple[Vec3, ...], ...],
            *,
            boundary: BoundaryMode3D = "fixed",
            name: str = "continuity_residual3d",
        ) -> ContinuityResidualHistory3D:
            if len(times) < 2:
                raise ValueError("continuity diagnostics require at least two time samples")
            if not (len(times) == len(density_states) == len(flux_states)):
                raise ValueError("continuity time/density/flux history length mismatch")
            if any(right <= left for left, right in zip(times, times[1:])):
                raise ValueError("continuity times must be strictly increasing")
            if any(len(state) != grid.count for state in density_states):
                raise ValueError("continuity density state length must match grid")
            if any(len(state) != grid.count for state in flux_states):
                raise ValueError("continuity flux state length must match grid")

            snapshots = []
            for index, (left_time, right_time) in enumerate(zip(times, times[1:])):
                dt = right_time - left_time
                density_rate = tuple(
                    (right - left) / dt
                    for left, right in zip(
                        density_states[index],
                        density_states[index + 1],
                        strict=True,
                    )
                )
                midpoint_flux = tuple(
                    (left + right) * 0.5
                    for left, right in zip(
                        flux_states[index],
                        flux_states[index + 1],
                        strict=True,
                    )
                )
                flux_divergence = divergence(midpoint_flux, grid, boundary=boundary)
                residual = tuple(
                    rate + div
                    for rate, div in zip(density_rate, flux_divergence, strict=True)
                )
                squared = tuple(value * value for value in residual)
                l2 = math.sqrt(max(integrate_scalar(squared, grid), 0.0))
                snapshots.append(
                    ContinuityResidualSnapshot3D(
                        time=0.5 * (left_time + right_time),
                        max_abs_residual=max(abs(value) for value in residual),
                        l2_residual=l2,
                    )
                )
            return ContinuityResidualHistory3D(
                snapshots=tuple(snapshots),
                name=name,
            )

        registry.register_semantic_type(
            "pde.continuity_residual_snapshot3d",
            ContinuityResidualSnapshot3D,
        )
        registry.register_semantic_type(
            "pde.continuity_residual_history3d",
            ContinuityResidualHistory3D,
        )
        registry.provide(
            "pde.continuity_residual_snapshot3d",
            ContinuityResidualSnapshot3D,
        )
        registry.provide(
            "pde.continuity_residual_history3d",
            ContinuityResidualHistory3D,
        )
        registry.provide("pde.continuity_residual_history_3d", continuity_history)
