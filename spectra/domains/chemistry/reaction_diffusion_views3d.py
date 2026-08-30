from __future__ import annotations

from dataclasses import dataclass

from spectra.core.units import MOLE_PER_CUBIC_METER
from spectra.domains.mathematics.fields import TimeDependentScalarField3D
from spectra.domains.partial_differential_equations.slices3d import ScalarPDESliceView3D
from spectra.domains.chemistry.reaction_diffusion3d import ReactionDiffusionSolution3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class ReactionDiffusionFields3D:
    species: tuple[str, ...]
    fields: tuple[TimeDependentScalarField3D, ...]
    start_time: float
    end_time: float
    name: str = "reaction_diffusion_fields3d"

    def field_for(self, species: int | str) -> TimeDependentScalarField3D:
        if isinstance(species, int):
            if not 0 <= species < len(self.species):
                raise IndexError("reaction-diffusion species index out of range")
            return self.fields[species]
        try:
            index = self.species.index(species)
        except ValueError as exc:
            raise KeyError(f"unknown reaction-diffusion species: {species}") from exc
        return self.fields[index]

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


class ReactionDiffusionViews3DDomain:
    name = "chemistry.reaction_diffusion.views3d"
    version = "1"
    dependencies = (
        DomainDependency("chemistry.reaction_diffusion.solution3d"),
        DomainDependency("pde.time_scalar_field_from_solution_3d"),
        DomainDependency("pde.scalar_slice_view3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        field_from_solution = registry.require("pde.time_scalar_field_from_solution_3d")
        slice_type = registry.require("pde.scalar_slice_view3d")

        def fields_from_solution(
            solution: ReactionDiffusionSolution3D,
        ) -> ReactionDiffusionFields3D:
            fields = tuple(
                field_from_solution(
                    solution.species_solution(species),
                    output_unit=MOLE_PER_CUBIC_METER,
                    name=f"{solution.name}.{species}.concentration",
                )
                for species in solution.network.species
            )
            return ReactionDiffusionFields3D(
                species=solution.network.species,
                fields=fields,
                start_time=solution.times[0],
                end_time=solution.times[-1],
                name=f"{solution.name}.fields",
            )

        def species_slice(
            solution: ReactionDiffusionSolution3D,
            species: int | str,
            *,
            axis: str = "z",
            index: int = 0,
            name: str | None = None,
        ) -> ScalarPDESliceView3D:
            scalar = solution.species_solution(species)
            label = scalar.name.split(".")[-1]
            return slice_type(
                solution=scalar,
                axis=axis,
                index=index,
                name=name or f"{solution.name}.{label}_{axis}_slice_{index}",
            )

        registry.register_semantic_type(
            "chemistry.reaction_diffusion.fields3d",
            ReactionDiffusionFields3D,
        )
        registry.provide(
            "chemistry.reaction_diffusion.fields_from_solution3d",
            fields_from_solution,
        )
        registry.provide(
            "chemistry.reaction_diffusion.species_slice3d",
            species_slice,
        )
