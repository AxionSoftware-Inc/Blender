from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.domains.physics.incompressible_flow3d import IncompressibleFlowSolution3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class FlowHistoryDiagnostics3D:
    max_speed: float
    worst_divergence: float
    worst_pressure_residual: float
    all_pressure_solves_converged: bool
    max_conservative_load: float
    all_steps_within_conservative_envelope: bool
    minimum_suggested_dt: float
    name: str = "flow_diagnostics3d"

    def __post_init__(self) -> None:
        for value_name, value in (
            ("max_speed", self.max_speed),
            ("worst_divergence", self.worst_divergence),
            ("worst_pressure_residual", self.worst_pressure_residual),
            ("max_conservative_load", self.max_conservative_load),
        ):
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{value_name} must be finite and non-negative")
        if not (math.isfinite(self.minimum_suggested_dt) or math.isinf(self.minimum_suggested_dt)):
            raise ValueError("minimum_suggested_dt must be finite or infinity")


class FluidDiagnostics3DDomain:
    name = "physics.fluid_diagnostics.3d"
    version = "1"
    dependencies = (
        DomainDependency("physics.incompressible_flow.solution3d"),
        DomainDependency("pde.explicit_stability_from_samples_3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        stability = registry.require("pde.explicit_stability_from_samples_3d")

        def diagnose_solution(
            solution: IncompressibleFlowSolution3D,
            *,
            safety: float = 0.9,
        ) -> FlowHistoryDiagnostics3D:
            max_speed = max(
                vector.magnitude
                for state in solution.states
                for vector in state.velocity
            )
            worst_divergence = max(state.max_divergence for state in solution.states)
            worst_pressure_residual = max(state.pressure_residual for state in solution.states)
            all_pressure = all(state.pressure_converged for state in solution.states)

            step_diagnostics = []
            for left, right in zip(solution.states, solution.states[1:]):
                dt = right.time - left.time
                step_diagnostics.append(
                    stability(
                        solution.grid,
                        left.velocity,
                        dt=dt,
                        diffusivity=solution.kinematic_viscosity_si,
                        safety=safety,
                    )
                )

            if step_diagnostics:
                max_load = max(item.conservative_load for item in step_diagnostics)
                all_within = all(item.within_conservative_envelope for item in step_diagnostics)
                minimum_dt = min(item.suggested_max_dt for item in step_diagnostics)
            else:
                max_load = 0.0
                all_within = True
                minimum_dt = math.inf

            return FlowHistoryDiagnostics3D(
                max_speed=max_speed,
                worst_divergence=worst_divergence,
                worst_pressure_residual=worst_pressure_residual,
                all_pressure_solves_converged=all_pressure,
                max_conservative_load=max_load,
                all_steps_within_conservative_envelope=all_within,
                minimum_suggested_dt=minimum_dt,
                name=f"{solution.name}.diagnostics",
            )

        registry.register_semantic_type(
            "physics.fluid.history_diagnostics3d",
            FlowHistoryDiagnostics3D,
        )
        registry.provide(
            "physics.fluid.history_diagnostics3d",
            FlowHistoryDiagnostics3D,
        )
        registry.provide("physics.fluid.diagnose_solution3d", diagnose_solution)
