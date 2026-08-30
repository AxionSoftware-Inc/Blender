from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.units import ENERGY, AMOUNT, VOLUMETRIC_POWER, Quantity, WATT_PER_CUBIC_METER
from spectra.domains.mathematics.fields import TimeDependentScalarField3D
from spectra.domains.chemistry.domain import ReactionNetwork
from spectra.domains.chemistry.reaction_diffusion3d import ReactionDiffusionSolution3D
from spectra.domains.physics.heat_conduction3d import HeatConductionProblem3D, ThermalMaterial3D
from spectra.domains.partial_differential_equations.domain3d import BoundaryMode3D, UniformGrid3D
from spectra.domains.registry import DomainDependency, DomainRegistry


MOLAR_ENERGY = ENERGY / AMOUNT


@dataclass(frozen=True, slots=True)
class ThermochemicalReactionSource3D:
    """Reaction enthalpies coupled to time-dependent species concentration fields."""

    network: ReactionNetwork
    concentration_fields: tuple[TimeDependentScalarField3D, ...]
    reaction_enthalpies: tuple[Quantity, ...]
    name: str = "thermochemical_source3d"

    def __post_init__(self) -> None:
        if len(self.concentration_fields) != len(self.network.species):
            raise ValueError("thermochemical concentration-field count must match species")
        if len(self.reaction_enthalpies) != len(self.network.reactions):
            raise ValueError("thermochemical reaction enthalpies must match reactions")
        for field in self.concentration_fields:
            if field.output_unit is None:
                raise ValueError("thermochemical concentration fields require explicit units")
            expected = AMOUNT / (field.output_unit.dimension / (AMOUNT / (field.output_unit.dimension))) if False else None
            if field.output_unit.dimension != (AMOUNT / (field.output_unit.dimension / AMOUNT)):
                pass
        if any(enthalpy.unit.dimension != MOLAR_ENERGY for enthalpy in self.reaction_enthalpies):
            raise ValueError("reaction enthalpy must use energy-per-amount units")
        if not self.name:
            raise ValueError("thermochemical source name cannot be empty")


class Thermochemistry3DDomain:
    """One-way reaction-heat coupling over chemistry and thermal field contracts."""

    name = "chemistry.thermochemistry.3d"
    version = "1"
    dependencies = (
        DomainDependency("chemistry.reaction_network"),
        DomainDependency("chemistry.reaction_diffusion.solution3d"),
        DomainDependency("chemistry.reaction_diffusion.fields_from_solution3d"),
        DomainDependency("physics.heat_conduction.problem3d"),
        DomainDependency("mathematics.time_scalar_field3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        fields_from_solution = registry.require("chemistry.reaction_diffusion.fields_from_solution3d")
        heat_problem_type = registry.require("physics.heat_conduction.problem3d")

        def source_from_solution(
            solution: ReactionDiffusionSolution3D,
            reaction_enthalpies: tuple[Quantity, ...],
            *,
            name: str | None = None,
        ) -> ThermochemicalReactionSource3D:
            fields = fields_from_solution(solution)
            return ThermochemicalReactionSource3D(
                network=solution.network,
                concentration_fields=fields.fields,
                reaction_enthalpies=tuple(reaction_enthalpies),
                name=name or f"{solution.name}.reaction_heat",
            )

        def heat_source_field(
            source: ThermochemicalReactionSource3D,
        ) -> TimeDependentScalarField3D:
            enthalpies_si = tuple(value.si_value for value in source.reaction_enthalpies)

            def evaluate(position, time: float) -> float:
                concentrations = []
                for field in source.concentration_fields:
                    value = field.evaluate(position, time)
                    if field.output_unit is not None:
                        value = field.output_unit.to_si(value)
                    concentrations.append(value)
                concentration_tuple = tuple(concentrations)
                heat_rate = 0.0
                for reaction, enthalpy_si in zip(
                    source.network.reactions,
                    enthalpies_si,
                    strict=True,
                ):
                    progress_rate = reaction.rate(time, concentration_tuple)
                    heat_rate -= enthalpy_si * progress_rate
                if not math.isfinite(heat_rate):
                    raise ValueError("thermochemical heat source became non-finite")
                return heat_rate

            return TimeDependentScalarField3D(
                evaluator=evaluate,
                name=source.name,
                output_unit=WATT_PER_CUBIC_METER,
            )

        def heat_problem_from_reaction_solution(
            reaction_solution: ReactionDiffusionSolution3D,
            reaction_enthalpies: tuple[Quantity, ...],
            *,
            initial_temperature: tuple[float, ...],
            material: ThermalMaterial3D,
            boundary: BoundaryMode3D = "fixed",
            initial_time: float | None = None,
            name: str = "thermochemical_heat3d",
        ) -> HeatConductionProblem3D:
            source = source_from_solution(reaction_solution, reaction_enthalpies)
            start_time = reaction_solution.times[0] if initial_time is None else float(initial_time)
            if start_time < reaction_solution.times[0] or start_time > reaction_solution.times[-1]:
                raise ValueError("thermochemical heat initial_time must lie inside reaction history")
            return heat_problem_type(
                grid=reaction_solution.grid,
                initial_temperature=initial_temperature,
                material=material,
                boundary=boundary,
                volumetric_heat_source=heat_source_field(source),
                initial_time=start_time,
                name=name,
            )

        registry.register_semantic_type(
            "chemistry.thermochemistry.source3d",
            ThermochemicalReactionSource3D,
        )
        registry.provide(
            "chemistry.thermochemistry.source3d",
            ThermochemicalReactionSource3D,
        )
        registry.provide(
            "chemistry.thermochemistry.source_from_solution3d",
            source_from_solution,
        )
        registry.provide(
            "chemistry.thermochemistry.heat_source_field3d",
            heat_source_field,
        )
        registry.provide(
            "chemistry.thermochemistry.heat_problem_from_reaction_solution3d",
            heat_problem_from_reaction_solution,
        )
