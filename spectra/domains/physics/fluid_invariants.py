from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.domains.physics.incompressible_flow import IncompressibleFlowSolution2D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class FlowInvariantSnapshot2D:
    time: float
    kinetic_energy_per_unit_mass: float
    enstrophy: float
    circulation: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.time):
            raise ValueError("flow invariant time must be finite")
        if not math.isfinite(self.kinetic_energy_per_unit_mass) or self.kinetic_energy_per_unit_mass < 0.0:
            raise ValueError("kinetic energy per unit mass must be finite and non-negative")
        if not math.isfinite(self.enstrophy) or self.enstrophy < 0.0:
            raise ValueError("enstrophy must be finite and non-negative")
        if not math.isfinite(self.circulation):
            raise ValueError("circulation must be finite")


@dataclass(frozen=True, slots=True)
class FlowInvariantHistory2D:
    snapshots: tuple[FlowInvariantSnapshot2D, ...]
    name: str = "flow_invariants2d"

    def __post_init__(self) -> None:
        if not self.snapshots:
            raise ValueError("flow invariant history cannot be empty")
        if any(right.time <= left.time for left, right in zip(self.snapshots, self.snapshots[1:])):
            raise ValueError("flow invariant times must be strictly increasing")


class FluidInvariants2DDomain:
    name = "physics.fluid_invariants.2d"
    version = "1"
    dependencies = (
        DomainDependency("physics.incompressible_flow.solution2d", min_version=2),
        DomainDependency("pde.curl_grid_2d", min_version=2),
        DomainDependency("pde.integrate_scalar_grid_2d"),
        DomainDependency("pde.integrate_vector_magnitude_squared_grid_2d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        curl = registry.require("pde.curl_grid_2d", min_version=2)
        integrate_scalar = registry.require("pde.integrate_scalar_grid_2d")
        integrate_vector_sq = registry.require(
            "pde.integrate_vector_magnitude_squared_grid_2d"
        )

        def invariant_history(
            solution: IncompressibleFlowSolution2D,
        ) -> FlowInvariantHistory2D:
            snapshots = []
            for state in solution.states:
                vorticity = curl(
                    state.velocity,
                    solution.grid,
                    boundary=solution.velocity_boundary,
                )
                kinetic = 0.5 * integrate_vector_sq(state.velocity, solution.grid)
                enstrophy = 0.5 * integrate_scalar(
                    tuple(value * value for value in vorticity),
                    solution.grid,
                )
                circulation = integrate_scalar(vorticity, solution.grid)
                snapshots.append(
                    FlowInvariantSnapshot2D(
                        time=state.time,
                        kinetic_energy_per_unit_mass=kinetic,
                        enstrophy=enstrophy,
                        circulation=circulation,
                    )
                )
            return FlowInvariantHistory2D(
                snapshots=tuple(snapshots),
                name=f"{solution.name}.invariants",
            )

        registry.register_semantic_type(
            "physics.fluid.invariant_snapshot2d",
            FlowInvariantSnapshot2D,
        )
        registry.register_semantic_type(
            "physics.fluid.invariant_history2d",
            FlowInvariantHistory2D,
        )
        registry.provide("physics.fluid.invariant_history2d", invariant_history)
