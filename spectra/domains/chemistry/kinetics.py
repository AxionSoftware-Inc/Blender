from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.domains.chemistry.domain import ReactionNetwork
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class ReactionKineticsProblem:
    network: ReactionNetwork
    initial_concentrations: tuple[float, ...]
    initial_time: float = 0.0
    name: str = "reaction_kinetics"

    def __post_init__(self) -> None:
        if len(self.initial_concentrations) != len(self.network.species):
            raise ValueError("kinetics concentration count must match network species")
        if any(
            not math.isfinite(float(value)) or float(value) < 0.0
            for value in self.initial_concentrations
        ):
            raise ValueError("kinetics concentrations must be finite and non-negative")
        if not math.isfinite(self.initial_time):
            raise ValueError("kinetics initial_time must be finite")
        if not self.name:
            raise ValueError("kinetics problem name cannot be empty")


@dataclass(frozen=True, slots=True)
class ReactionKineticsSolution:
    network: ReactionNetwork
    times: tuple[float, ...]
    states: tuple[tuple[float, ...], ...]
    name: str = "reaction_kinetics"

    def __post_init__(self) -> None:
        if not self.times or not self.states:
            raise ValueError("kinetics solution cannot be empty")
        if len(self.times) != len(self.states):
            raise ValueError("kinetics time/state history mismatch")
        if any(len(state) != len(self.network.species) for state in self.states):
            raise ValueError("kinetics state dimension must match species count")
        if any(right <= left for left, right in zip(self.times, self.times[1:])):
            raise ValueError("kinetics times must be strictly increasing")

    @property
    def duration(self) -> float:
        return self.times[-1] - self.times[0]

    def species_history(self, species: int | str) -> tuple[float, ...]:
        if isinstance(species, int):
            index = species
            if not 0 <= index < len(self.network.species):
                raise IndexError("kinetics species index out of range")
        else:
            try:
                index = self.network.species.index(species)
            except ValueError as exc:
                raise KeyError(f"unknown kinetics species: {species}") from exc
        return tuple(state[index] for state in self.states)


class ReactionKineticsDomain:
    """Well-mixed chemical kinetics lowered to the selectable ODE solver role."""

    name = "chemistry.kinetics"
    version = "2"
    dependencies = (
        DomainDependency("chemistry.reaction_network"),
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solve_first_order", min_version=2),
    )

    def register(self, registry: DomainRegistry) -> None:
        system_type = registry.require("ode.first_order_system")
        solve_ode = registry.require("ode.solve_first_order", min_version=2)

        def solve(
            problem: ReactionKineticsProblem,
            *,
            end_time: float,
            steps: int = 128,
        ) -> ReactionKineticsSolution:
            def derivative(time: float, state: tuple[float, ...]) -> tuple[float, ...]:
                return problem.network.derivative(time, tuple(float(value) for value in state))

            solution = solve_ode(
                system_type(
                    derivative=derivative,
                    initial_time=problem.initial_time,
                    initial_state=tuple(float(value) for value in problem.initial_concentrations),
                    name=problem.name,
                ),
                end_time=end_time,
                steps=steps,
            )
            return ReactionKineticsSolution(
                network=problem.network,
                times=solution.times,
                states=tuple(tuple(float(value) for value in state) for state in solution.states),
                name=problem.name,
            )

        registry.register_semantic_type("chemistry.kinetics.problem", ReactionKineticsProblem)
        registry.register_semantic_type("chemistry.kinetics.solution", ReactionKineticsSolution)
        registry.provide("chemistry.kinetics.problem", ReactionKineticsProblem)
        registry.provide("chemistry.kinetics.solution", ReactionKineticsSolution)
        registry.provide("chemistry.kinetics.solve", solve, version=2)
