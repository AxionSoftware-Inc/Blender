from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.domains.physics.incompressible_flow3d import IncompressibleFlowSolution3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class FlowInvariantSnapshot3D:
    time: float
    kinetic_energy_per_unit_mass: float
    enstrophy: float
    max_divergence: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.time):
            raise ValueError("3D flow invariant time must be finite")
        if not math.isfinite(self.kinetic_energy_per_unit_mass) or self.kinetic_energy_per_unit_mass < 0.0:
            raise ValueError("3D kinetic energy per unit mass must be finite and non-negative")
        if not math.isfinite(self.enstrophy) or self.enstrophy < 0.0:
            raise ValueError("3D enstrophy must be finite and non-negative")
        if not math.isfinite(self.max_divergence) or self.max_divergence < 0.0:
            raise ValueError("3D max divergence must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class FlowInvariantHistory3D:
    snapshots: tuple[FlowInvariantSnapshot3D, ...]
    name: str = "flow_invariants3d"

    def __post_init__(self) -> None:
        if not self.snapshots:
            raise ValueError("3D flow invariant history cannot be empty")
        if any(right.time <= left.time for left, right in zip(self.snapshots, self.snapshots[1:])):
            raise ValueError("3D flow invariant times must be strictly increasing")


class FluidInvariants3DDomain:
    name = "physics.fluid_invariants.3d"
    version = "1"
    dependencies = (
        DomainDependency("physics.incompressible_flow.solution3d"),
        DomainDependency("pde.curl_grid_3d"),
        DomainDependency("pde.integrate_vector_magnitude_squared_grid_3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        curl = registry.require("pde.curl_grid_3d")
        integrate_vector_sq = registry.require(
            "pde.integrate_vector_magnitude_squared_grid_3d"
        )

        def invariant_history(
            solution: IncompressibleFlowSolution3D,
        ) -> FlowInvariantHistory3D:
            snapshots = []
            for state in solution.states:
                vorticity = curl(
                    state.velocity,
                    solution.grid,
                    boundary=solution.velocity_boundary,
                )
                kinetic = 0.5 * integrate_vector_sq(state.velocity, solution.grid)
                enstrophy = 0.5 * integrate_vector_sq(vorticity, solution.grid)
                snapshots.append(
                    FlowInvariantSnapshot3D(
                        time=state.time,
                        kinetic_energy_per_unit_mass=kinetic,
                        enstrophy=enstrophy,
                        max_divergence=state.max_divergence,
                    )
                )
            return FlowInvariantHistory3D(
                snapshots=tuple(snapshots),
                name=f"{solution.name}.invariants",
            )

        registry.register_semantic_type(
            "physics.fluid.invariant_snapshot3d",
            FlowInvariantSnapshot3D,
        )
        registry.register_semantic_type(
            "physics.fluid.invariant_history3d",
            FlowInvariantHistory3D,
        )
        registry.provide("physics.fluid.invariant_snapshot3d", FlowInvariantSnapshot3D)
        registry.provide("physics.fluid.invariant_history3d", FlowInvariantHistory3D)
        registry.provide("physics.fluid.compute_invariant_history3d", invariant_history)
