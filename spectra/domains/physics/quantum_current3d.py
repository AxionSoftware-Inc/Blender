from __future__ import annotations

from dataclasses import dataclass

from spectra.core.constants import REDUCED_PLANCK_CONSTANT
from spectra.core.types import Vec3
from spectra.core.units import METER, ONE, SECOND
from spectra.domains.mathematics.fields import (
    TimeDependentScalarField3D,
    TimeDependentVectorField3D,
)
from spectra.domains.partial_differential_equations.domain3d import BoundaryMode3D, UniformGrid3D
from spectra.domains.physics.schrodinger3d import SchrodingerSolution3D
from spectra.domains.registry import DomainDependency, DomainRegistry


PROBABILITY_DENSITY_UNIT = ONE / (METER ** 3)
PROBABILITY_CURRENT_UNIT = ONE / ((METER ** 2) * SECOND)


@dataclass(frozen=True, slots=True)
class QuantumProbabilityFlow3D:
    grid: UniformGrid3D
    times: tuple[float, ...]
    density_states: tuple[tuple[float, ...], ...]
    current_states: tuple[tuple[Vec3, ...], ...]
    boundary: BoundaryMode3D = "fixed"
    name: str = "quantum_probability_flow3d"

    def __post_init__(self) -> None:
        count = self.grid.count
        if not self.times:
            raise ValueError("quantum probability flow cannot be empty")
        if not (len(self.times) == len(self.density_states) == len(self.current_states)):
            raise ValueError("quantum probability-flow history length mismatch")
        if any(len(state) != count for state in self.density_states):
            raise ValueError("quantum density state length must match grid")
        if any(len(state) != count for state in self.current_states):
            raise ValueError("quantum current state length must match grid")
        if any(right <= left for left, right in zip(self.times, self.times[1:])):
            raise ValueError("quantum probability-flow times must be strictly increasing")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown quantum probability-flow boundary mode: {self.boundary}")


@dataclass(frozen=True, slots=True)
class QuantumProbabilityFields3D:
    density: TimeDependentScalarField3D
    current: TimeDependentVectorField3D
    start_time: float
    end_time: float
    name: str = "quantum_probability_fields3d"

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


class QuantumProbabilityCurrent3DDomain:
    """Probability density/current derived from generic Schrodinger and grid operators."""

    name = "physics.quantum.probability_current3d"
    version = "3"
    dependencies = (
        DomainDependency("physics.quantum.schrodinger3d.solution"),
        DomainDependency("pde.gradient_grid_3d"),
        DomainDependency("pde.time_scalar_field_from_grid_3d"),
        DomainDependency("pde.time_vector_field_from_grid_3d"),
        DomainDependency("pde.continuity_residual_history_3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        gradient = registry.require("pde.gradient_grid_3d")
        time_scalar = registry.require("pde.time_scalar_field_from_grid_3d")
        time_vector = registry.require("pde.time_vector_field_from_grid_3d")
        continuity_history = registry.require("pde.continuity_residual_history_3d")
        hbar = REDUCED_PLANCK_CONSTANT.si_value

        def probability_flow(solution: SchrodingerSolution3D) -> QuantumProbabilityFlow3D:
            coefficient = hbar / solution.mass.si_value
            densities = []
            currents = []
            for state in solution.states:
                real = tuple(complex(value).real for value in state)
                imaginary = tuple(complex(value).imag for value in state)
                grad_real = gradient(real, solution.grid, boundary=solution.boundary)
                grad_imag = gradient(imaginary, solution.grid, boundary=solution.boundary)
                density = tuple(abs(complex(value)) ** 2 for value in state)
                current = tuple(
                    Vec3(
                        coefficient * (re * gi.x - im * gr.x),
                        coefficient * (re * gi.y - im * gr.y),
                        coefficient * (re * gi.z - im * gr.z),
                    )
                    for re, im, gr, gi in zip(
                        real,
                        imaginary,
                        grad_real,
                        grad_imag,
                        strict=True,
                    )
                )
                densities.append(density)
                currents.append(current)
            return QuantumProbabilityFlow3D(
                grid=solution.grid,
                times=solution.times,
                density_states=tuple(densities),
                current_states=tuple(currents),
                boundary=solution.boundary,
                name=f"{solution.name}.probability_flow",
            )

        def fields_from_flow(flow: QuantumProbabilityFlow3D) -> QuantumProbabilityFields3D:
            return QuantumProbabilityFields3D(
                density=time_scalar(
                    flow.grid,
                    flow.times,
                    flow.density_states,
                    name=f"{flow.name}.density",
                    output_unit=PROBABILITY_DENSITY_UNIT,
                    temporal_outside="clamp",
                ),
                current=time_vector(
                    flow.grid,
                    flow.times,
                    flow.current_states,
                    name=f"{flow.name}.current",
                    output_unit=PROBABILITY_CURRENT_UNIT,
                    temporal_outside="clamp",
                ),
                start_time=flow.times[0],
                end_time=flow.times[-1],
                name=f"{flow.name}.fields",
            )

        def continuity_diagnostics(
            flow: QuantumProbabilityFlow3D,
            *,
            boundary: BoundaryMode3D | None = None,
        ):
            return continuity_history(
                flow.grid,
                flow.times,
                flow.density_states,
                flow.current_states,
                boundary=flow.boundary if boundary is None else boundary,
                name=f"{flow.name}.continuity",
            )

        registry.register_semantic_type(
            "physics.quantum.probability_flow3d",
            QuantumProbabilityFlow3D,
        )
        registry.register_semantic_type(
            "physics.quantum.probability_fields3d",
            QuantumProbabilityFields3D,
        )
        registry.provide(
            "physics.quantum.probability_flow3d",
            QuantumProbabilityFlow3D,
        )
        registry.provide(
            "physics.quantum.probability_fields3d",
            QuantumProbabilityFields3D,
        )
        registry.provide(
            "physics.quantum.compute_probability_flow3d",
            probability_flow,
            version=3,
        )
        registry.provide(
            "physics.quantum.probability_fields_from_flow3d",
            fields_from_flow,
            version=3,
        )
        registry.provide(
            "physics.quantum.continuity_diagnostics3d",
            continuity_diagnostics,
            version=3,
        )
