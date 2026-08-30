from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.units import KINEMATIC_VISCOSITY, LENGTH, VELOCITY, Quantity
from spectra.domains.physics.incompressible_flow import IncompressibleFlowSolution2D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class FlowHistoryDiagnostics2D:
    max_speed: float
    worst_divergence: float
    worst_pressure_residual: float
    all_pressure_solves_converged: bool
    max_conservative_load: float
    all_steps_within_conservative_envelope: bool
    minimum_suggested_dt: float
    name: str = "flow_diagnostics2d"

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


def reynolds_number(
    characteristic_speed: Quantity,
    characteristic_length: Quantity,
    kinematic_viscosity: Quantity,
) -> float:
    if characteristic_speed.unit.dimension != VELOCITY:
        raise ValueError("characteristic speed must have velocity dimension")
    if characteristic_length.unit.dimension != LENGTH:
        raise ValueError("characteristic length must have length dimension")
    if kinematic_viscosity.unit.dimension != KINEMATIC_VISCOSITY:
        raise ValueError("kinematic viscosity has incompatible dimension")
    speed = characteristic_speed.si_value
    length = characteristic_length.si_value
    viscosity = kinematic_viscosity.si_value
    if speed < 0.0 or length <= 0.0 or viscosity <= 0.0:
        raise ValueError("Reynolds inputs require speed >= 0, length > 0, viscosity > 0")
    return speed * length / viscosity


def peclet_number(
    characteristic_speed: Quantity,
    characteristic_length: Quantity,
    diffusivity: Quantity,
) -> float:
    if characteristic_speed.unit.dimension != VELOCITY:
        raise ValueError("characteristic speed must have velocity dimension")
    if characteristic_length.unit.dimension != LENGTH:
        raise ValueError("characteristic length must have length dimension")
    if diffusivity.unit.dimension != KINEMATIC_VISCOSITY:
        raise ValueError("scalar diffusivity must have length^2/time dimension")
    speed = characteristic_speed.si_value
    length = characteristic_length.si_value
    diffusion = diffusivity.si_value
    if speed < 0.0 or length <= 0.0 or diffusion <= 0.0:
        raise ValueError("Peclet inputs require speed >= 0, length > 0, diffusivity > 0")
    return speed * length / diffusion


class FluidDiagnostics2DDomain:
    name = "physics.fluid_diagnostics.2d"
    version = "1"
    dependencies = (
        DomainDependency("physics.incompressible_flow.solution2d", min_version=2),
        DomainDependency("pde.explicit_stability_from_samples_2d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        stability = registry.require("pde.explicit_stability_from_samples_2d")

        def diagnose_solution(
            solution: IncompressibleFlowSolution2D,
            *,
            safety: float = 0.9,
        ) -> FlowHistoryDiagnostics2D:
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

            return FlowHistoryDiagnostics2D(
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
            "physics.fluid.history_diagnostics2d",
            FlowHistoryDiagnostics2D,
        )
        registry.provide("physics.fluid.diagnose_solution2d", diagnose_solution)
        registry.provide("physics.fluid.reynolds_number", reynolds_number)
        registry.provide("physics.fluid.peclet_number", peclet_number)
