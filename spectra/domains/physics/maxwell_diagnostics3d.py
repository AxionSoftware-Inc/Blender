from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.constants import VACUUM_PERMEABILITY, VACUUM_PERMITTIVITY
from spectra.domains.physics.maxwell3d import MaxwellSolution3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class MaxwellDiagnosticSnapshot3D:
    time: float
    max_abs_divergence_electric: float
    max_abs_divergence_magnetic: float
    total_field_energy_si: float
    max_poynting_magnitude_si: float

    def __post_init__(self) -> None:
        values = (
            self.time,
            self.max_abs_divergence_electric,
            self.max_abs_divergence_magnetic,
            self.total_field_energy_si,
            self.max_poynting_magnitude_si,
        )
        if any(not math.isfinite(value) for value in values):
            raise ValueError("Maxwell diagnostics must be finite")
        if min(values[1:]) < 0.0:
            raise ValueError("Maxwell diagnostic magnitudes must be non-negative")


@dataclass(frozen=True, slots=True)
class MaxwellDiagnostics3D:
    snapshots: tuple[MaxwellDiagnosticSnapshot3D, ...]
    source_free: bool
    name: str = "maxwell_diagnostics3d"

    def __post_init__(self) -> None:
        if not self.snapshots:
            raise ValueError("Maxwell diagnostics cannot be empty")
        if any(right.time <= left.time for left, right in zip(self.snapshots, self.snapshots[1:])):
            raise ValueError("Maxwell diagnostic times must be strictly increasing")


class MaxwellDiagnostics3DDomain:
    """Constraint and energy diagnostics for sampled time-domain electromagnetic fields."""

    name = "physics.electromagnetism.maxwell_diagnostics3d"
    version = "1"
    dependencies = (
        DomainDependency("physics.maxwell.solution3d"),
        DomainDependency("pde.divergence_grid_3d"),
        DomainDependency("pde.integrate_scalar_grid_3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        divergence = registry.require("pde.divergence_grid_3d")
        integrate_scalar = registry.require("pde.integrate_scalar_grid_3d")
        epsilon0 = VACUUM_PERMITTIVITY.si_value
        mu0 = VACUUM_PERMEABILITY.si_value

        def diagnose(solution: MaxwellSolution3D) -> MaxwellDiagnostics3D:
            snapshots = []
            for time, electric, magnetic in zip(
                solution.times,
                solution.electric_states,
                solution.magnetic_states,
                strict=True,
            ):
                div_e = divergence(electric, solution.grid, boundary=solution.boundary)
                div_b = divergence(magnetic, solution.grid, boundary=solution.boundary)
                energy_density = tuple(
                    0.5 * epsilon0 * e.dot(e) + 0.5 * b.dot(b) / mu0
                    for e, b in zip(electric, magnetic, strict=True)
                )
                poynting = tuple(
                    e.cross(b) * (1.0 / mu0)
                    for e, b in zip(electric, magnetic, strict=True)
                )
                snapshots.append(
                    MaxwellDiagnosticSnapshot3D(
                        time=time,
                        max_abs_divergence_electric=max(abs(value) for value in div_e),
                        max_abs_divergence_magnetic=max(abs(value) for value in div_b),
                        total_field_energy_si=integrate_scalar(energy_density, solution.grid),
                        max_poynting_magnitude_si=max(value.magnitude for value in poynting),
                    )
                )
            return MaxwellDiagnostics3D(
                snapshots=tuple(snapshots),
                source_free=solution.source_free,
                name=f"{solution.name}.diagnostics",
            )

        registry.register_semantic_type(
            "physics.maxwell.diagnostic_snapshot3d",
            MaxwellDiagnosticSnapshot3D,
        )
        registry.register_semantic_type(
            "physics.maxwell.diagnostics3d",
            MaxwellDiagnostics3D,
        )
        registry.provide("physics.maxwell.diagnose3d", diagnose)
