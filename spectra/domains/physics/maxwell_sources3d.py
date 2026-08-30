from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.constants import VACUUM_PERMITTIVITY
from spectra.core.types import Vec3
from spectra.core.units import CHARGE_DENSITY, CURRENT_DENSITY
from spectra.domains.mathematics.fields import (
    TimeDependentScalarField3D,
    TimeDependentVectorField3D,
)
from spectra.domains.partial_differential_equations.conservation3d import (
    ContinuityResidualHistory3D,
)
from spectra.domains.physics.maxwell3d import MaxwellProblem3D, MaxwellSolution3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class MaxwellSourceFields3D:
    """Charge/current source semantics for time-domain electromagnetism."""

    charge_density: TimeDependentScalarField3D | None = None
    current_density: TimeDependentVectorField3D | None = None
    name: str = "maxwell_sources3d"

    def __post_init__(self) -> None:
        if self.charge_density is None and self.current_density is None:
            raise ValueError("Maxwell sources require charge density, current density, or both")
        if self.charge_density is not None:
            if self.charge_density.output_unit is None:
                raise ValueError("Maxwell charge-density source requires explicit units")
            if self.charge_density.output_unit.dimension != CHARGE_DENSITY:
                raise ValueError("Maxwell charge-density source has incompatible units")
        if self.current_density is not None:
            if self.current_density.output_unit is None:
                raise ValueError("Maxwell current-density source requires explicit units")
            if self.current_density.output_unit.dimension != CURRENT_DENSITY:
                raise ValueError("Maxwell current-density source has incompatible units")
        if not self.name:
            raise ValueError("Maxwell source name cannot be empty")


@dataclass(frozen=True, slots=True)
class MaxwellSourceHistory3D:
    times: tuple[float, ...]
    charge_density_states: tuple[tuple[float, ...], ...]
    current_density_states: tuple[tuple[Vec3, ...], ...]
    name: str = "maxwell_source_history3d"

    def __post_init__(self) -> None:
        if not self.times:
            raise ValueError("Maxwell source history cannot be empty")
        if not (
            len(self.times)
            == len(self.charge_density_states)
            == len(self.current_density_states)
        ):
            raise ValueError("Maxwell source-history lengths must match")
        if any(right <= left for left, right in zip(self.times, self.times[1:])):
            raise ValueError("Maxwell source-history times must be strictly increasing")


@dataclass(frozen=True, slots=True)
class MaxwellGaussSnapshot3D:
    time: float
    max_abs_electric_gauss_residual: float
    max_abs_magnetic_divergence: float
    total_charge_si: float

    def __post_init__(self) -> None:
        values = (
            self.time,
            self.max_abs_electric_gauss_residual,
            self.max_abs_magnetic_divergence,
            self.total_charge_si,
        )
        if any(not math.isfinite(value) for value in values):
            raise ValueError("Maxwell source diagnostics must be finite")
        if self.max_abs_electric_gauss_residual < 0.0:
            raise ValueError("electric Gauss residual magnitude must be non-negative")
        if self.max_abs_magnetic_divergence < 0.0:
            raise ValueError("magnetic divergence magnitude must be non-negative")


@dataclass(frozen=True, slots=True)
class MaxwellSourceDiagnostics3D:
    gauss_snapshots: tuple[MaxwellGaussSnapshot3D, ...]
    continuity: ContinuityResidualHistory3D
    name: str = "maxwell_source_diagnostics3d"

    def __post_init__(self) -> None:
        if not self.gauss_snapshots:
            raise ValueError("Maxwell source diagnostics require Gauss snapshots")


class MaxwellSources3DDomain:
    """Source-aware Maxwell constraints composed from generic conservation operators."""

    name = "physics.electromagnetism.maxwell_sources3d"
    version = "1"
    dependencies = (
        DomainDependency("physics.maxwell.problem3d"),
        DomainDependency("physics.maxwell.solution3d"),
        DomainDependency("pde.divergence_grid_3d"),
        DomainDependency("pde.integrate_scalar_grid_3d"),
        DomainDependency("pde.continuity_residual_history_3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        maxwell_problem_type = registry.require("physics.maxwell.problem3d")
        divergence = registry.require("pde.divergence_grid_3d")
        integrate_scalar = registry.require("pde.integrate_scalar_grid_3d")
        continuity_history = registry.require("pde.continuity_residual_history_3d")
        epsilon0 = VACUUM_PERMITTIVITY.si_value

        def problem_from_sources(
            sources: MaxwellSourceFields3D,
            *,
            grid,
            initial_electric: tuple[Vec3, ...],
            initial_magnetic: tuple[Vec3, ...],
            boundary: str = "fixed",
            initial_time: float = 0.0,
            name: str = "maxwell3d",
        ) -> MaxwellProblem3D:
            return maxwell_problem_type(
                grid=grid,
                initial_electric=initial_electric,
                initial_magnetic=initial_magnetic,
                boundary=boundary,
                current_density=sources.current_density,
                initial_time=initial_time,
                name=name,
            )

        def history_for_solution(
            sources: MaxwellSourceFields3D,
            solution: MaxwellSolution3D,
        ) -> MaxwellSourceHistory3D:
            charge_states = []
            current_states = []
            for time in solution.times:
                charge = []
                current = []
                for x, y, z in solution.grid.coordinates:
                    position = Vec3(x, y, z)
                    rho = 0.0
                    if sources.charge_density is not None:
                        rho = sources.charge_density.evaluate(position, time)
                        rho = sources.charge_density.output_unit.to_si(rho)
                    current_value = Vec3(0.0, 0.0, 0.0)
                    if sources.current_density is not None:
                        raw = sources.current_density.evaluate(position, time)
                        unit = sources.current_density.output_unit
                        current_value = Vec3(
                            unit.to_si(raw.x),
                            unit.to_si(raw.y),
                            unit.to_si(raw.z),
                        )
                    charge.append(rho)
                    current.append(current_value)
                charge_states.append(tuple(charge))
                current_states.append(tuple(current))
            return MaxwellSourceHistory3D(
                times=solution.times,
                charge_density_states=tuple(charge_states),
                current_density_states=tuple(current_states),
                name=f"{sources.name}.history",
            )

        def diagnose(
            solution: MaxwellSolution3D,
            sources: MaxwellSourceFields3D,
        ) -> MaxwellSourceDiagnostics3D:
            history = history_for_solution(sources, solution)
            gauss = []
            for time, electric, magnetic, rho in zip(
                solution.times,
                solution.electric_states,
                solution.magnetic_states,
                history.charge_density_states,
                strict=True,
            ):
                div_e = divergence(electric, solution.grid, boundary=solution.boundary)
                div_b = divergence(magnetic, solution.grid, boundary=solution.boundary)
                electric_residual = tuple(
                    divergence_value - charge_density / epsilon0
                    for divergence_value, charge_density in zip(div_e, rho, strict=True)
                )
                gauss.append(
                    MaxwellGaussSnapshot3D(
                        time=time,
                        max_abs_electric_gauss_residual=max(
                            abs(value) for value in electric_residual
                        ),
                        max_abs_magnetic_divergence=max(abs(value) for value in div_b),
                        total_charge_si=integrate_scalar(rho, solution.grid),
                    )
                )
            continuity = continuity_history(
                solution.grid,
                history.times,
                history.charge_density_states,
                history.current_density_states,
                boundary=solution.boundary,
                name=f"{sources.name}.continuity",
            )
            return MaxwellSourceDiagnostics3D(
                gauss_snapshots=tuple(gauss),
                continuity=continuity,
                name=f"{sources.name}.diagnostics",
            )

        registry.register_semantic_type(
            "physics.maxwell.source_fields3d",
            MaxwellSourceFields3D,
        )
        registry.register_semantic_type(
            "physics.maxwell.source_history3d",
            MaxwellSourceHistory3D,
        )
        registry.register_semantic_type(
            "physics.maxwell.source_diagnostics3d",
            MaxwellSourceDiagnostics3D,
        )
        registry.provide("physics.maxwell.source_fields3d", MaxwellSourceFields3D)
        registry.provide("physics.maxwell.source_history3d", MaxwellSourceHistory3D)
        registry.provide(
            "physics.maxwell.problem_from_sources3d",
            problem_from_sources,
        )
        registry.provide(
            "physics.maxwell.source_history_for_solution3d",
            history_for_solution,
        )
        registry.provide("physics.maxwell.source_diagnostics3d", diagnose)
