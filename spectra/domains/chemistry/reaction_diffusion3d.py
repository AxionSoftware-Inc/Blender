from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.units import KINEMATIC_VISCOSITY, Quantity
from spectra.domains.chemistry.domain import ReactionNetwork
from spectra.domains.partial_differential_equations.coupled3d import (
    CoupledScalarPDEProblem3D,
    CoupledScalarPDESolution3D,
)
from spectra.domains.partial_differential_equations.domain3d import BoundaryMode3D, UniformGrid3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class ReactionDiffusionProblem3D:
    grid: UniformGrid3D
    network: ReactionNetwork
    initial_concentrations: tuple[tuple[float, ...], ...]
    diffusivities: tuple[Quantity, ...]
    boundary: BoundaryMode3D = "fixed"
    initial_time: float = 0.0
    name: str = "reaction_diffusion3d"

    def __post_init__(self) -> None:
        species_count = len(self.network.species)
        if len(self.initial_concentrations) != species_count:
            raise ValueError("reaction-diffusion concentration component count mismatch")
        if len(self.diffusivities) != species_count:
            raise ValueError("reaction-diffusion diffusivity count mismatch")
        if any(len(component) != self.grid.count for component in self.initial_concentrations):
            raise ValueError("reaction-diffusion concentration samples must match grid")
        if any(
            not math.isfinite(float(value)) or float(value) < 0.0
            for component in self.initial_concentrations
            for value in component
        ):
            raise ValueError("reaction-diffusion concentrations must be finite and non-negative")
        for diffusivity in self.diffusivities:
            if diffusivity.unit.dimension != KINEMATIC_VISCOSITY:
                raise ValueError("reaction-diffusion diffusivity must have length^2/time dimension")
            if diffusivity.si_value < 0.0:
                raise ValueError("reaction-diffusion diffusivity must be non-negative")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown reaction-diffusion boundary mode: {self.boundary}")
        if not math.isfinite(self.initial_time):
            raise ValueError("reaction-diffusion initial_time must be finite")
        if not self.name:
            raise ValueError("reaction-diffusion name cannot be empty")


@dataclass(frozen=True, slots=True)
class ReactionDiffusionSolution3D:
    coupled_solution: CoupledScalarPDESolution3D
    network: ReactionNetwork
    diffusivities_si: tuple[float, ...]
    boundary: BoundaryMode3D

    @property
    def grid(self) -> UniformGrid3D:
        return self.coupled_solution.grid

    @property
    def times(self) -> tuple[float, ...]:
        return self.coupled_solution.times

    @property
    def states(self):
        return self.coupled_solution.states

    @property
    def duration(self) -> float:
        return self.coupled_solution.duration

    @property
    def name(self) -> str:
        return self.coupled_solution.name

    def species_solution(self, species: int | str):
        return self.coupled_solution.component_solution(species)


def _is_boundary(grid: UniformGrid3D, index: int) -> bool:
    xy = grid.x.count * grid.y.count
    z_index = index // xy
    rem = index % xy
    y_index = rem // grid.x.count
    x_index = rem % grid.x.count
    return (
        x_index in {0, grid.x.count - 1}
        or y_index in {0, grid.y.count - 1}
        or z_index in {0, grid.z.count - 1}
    )


class ReactionDiffusion3DDomain:
    """Spatial chemical kinetics composed from reaction networks + coupled PDEs."""

    name = "chemistry.reaction_diffusion.3d"
    version = "1"
    dependencies = (
        DomainDependency("chemistry.reaction_network"),
        DomainDependency("pde.coupled_scalar_problem3d"),
        DomainDependency("pde.solve_coupled_scalar_3d"),
        DomainDependency("pde.laplacian_3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        coupled_problem_type = registry.require("pde.coupled_scalar_problem3d")
        solve_coupled = registry.require("pde.solve_coupled_scalar_3d")
        laplacian = registry.require("pde.laplacian_3d")

        def solve(
            problem: ReactionDiffusionProblem3D,
            *,
            end_time: float,
            steps: int = 128,
        ) -> ReactionDiffusionSolution3D:
            diffusivities_si = tuple(value.si_value for value in problem.diffusivities)
            species_count = len(problem.network.species)

            def rhs(time, grid, components):
                diffusion_terms = tuple(
                    laplacian(component, grid, boundary=problem.boundary)
                    for component in components
                )
                reaction_terms = [
                    [0.0 for _ in range(grid.count)] for _ in range(species_count)
                ]
                for index in range(grid.count):
                    if problem.boundary == "fixed" and _is_boundary(grid, index):
                        continue
                    local = tuple(components[species][index] for species in range(species_count))
                    derivative = problem.network.derivative(time, local)
                    for species, value in enumerate(derivative):
                        reaction_terms[species][index] = value

                result = []
                for species in range(species_count):
                    diffusion = diffusivities_si[species]
                    result.append(
                        tuple(
                            0.0
                            if problem.boundary == "fixed" and _is_boundary(grid, index)
                            else diffusion * diffusion_terms[species][index]
                            + reaction_terms[species][index]
                            for index in range(grid.count)
                        )
                    )
                return tuple(result)

            solution = solve_coupled(
                coupled_problem_type(
                    grid=problem.grid,
                    component_names=problem.network.species,
                    initial_components=problem.initial_concentrations,
                    rhs=rhs,
                    initial_time=problem.initial_time,
                    name=problem.name,
                ),
                end_time=end_time,
                steps=steps,
            )
            return ReactionDiffusionSolution3D(
                coupled_solution=solution,
                network=problem.network,
                diffusivities_si=diffusivities_si,
                boundary=problem.boundary,
            )

        registry.register_semantic_type(
            "chemistry.reaction_diffusion.problem3d",
            ReactionDiffusionProblem3D,
        )
        registry.register_semantic_type(
            "chemistry.reaction_diffusion.solution3d",
            ReactionDiffusionSolution3D,
        )
        registry.provide(
            "chemistry.reaction_diffusion.problem3d",
            ReactionDiffusionProblem3D,
        )
        registry.provide(
            "chemistry.reaction_diffusion.solution3d",
            ReactionDiffusionSolution3D,
        )
        registry.provide("chemistry.reaction_diffusion.solve3d", solve)
