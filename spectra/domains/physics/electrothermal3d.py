from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec3
from spectra.core.units import (
    CURRENT_DENSITY,
    ELECTRIC_FIELD,
    WATT_PER_CUBIC_METER,
)
from spectra.domains.mathematics.fields import TimeDependentVectorField3D, TimeDependentScalarField3D
from spectra.domains.partial_differential_equations.domain3d import BoundaryMode3D
from spectra.domains.physics.heat_conduction3d import HeatConductionProblem3D, ThermalMaterial3D
from spectra.domains.physics.maxwell3d import MaxwellSolution3D
from spectra.domains.physics.maxwell_sources3d import MaxwellSourceFields3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class ElectrothermalSource3D:
    electric_field: TimeDependentVectorField3D
    current_density: TimeDependentVectorField3D
    name: str = "electrothermal_source3d"

    def __post_init__(self) -> None:
        if self.electric_field.output_unit is None:
            raise ValueError("electrothermal electric field requires explicit units")
        if self.electric_field.output_unit.dimension != ELECTRIC_FIELD:
            raise ValueError("electrothermal electric field has incompatible units")
        if self.current_density.output_unit is None:
            raise ValueError("electrothermal current density requires explicit units")
        if self.current_density.output_unit.dimension != CURRENT_DENSITY:
            raise ValueError("electrothermal current density has incompatible units")
        if not self.name:
            raise ValueError("electrothermal source name cannot be empty")


class Electrothermal3DDomain:
    """One-way electromagnetic-to-thermal coupling through Joule heating."""

    name = "physics.electrothermal.3d"
    version = "1"
    dependencies = (
        DomainDependency("physics.maxwell.fields_from_solution3d"),
        DomainDependency("physics.maxwell.source_fields3d"),
        DomainDependency("physics.heat_conduction.problem3d"),
        DomainDependency("mathematics.time_scalar_field3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        maxwell_fields = registry.require("physics.maxwell.fields_from_solution3d")
        heat_problem_type = registry.require("physics.heat_conduction.problem3d")

        def source_from_maxwell(
            solution: MaxwellSolution3D,
            sources: MaxwellSourceFields3D,
            *,
            name: str | None = None,
        ) -> ElectrothermalSource3D:
            if sources.current_density is None:
                raise ValueError("electrothermal coupling requires Maxwell current density")
            fields = maxwell_fields(solution)
            return ElectrothermalSource3D(
                electric_field=fields.electric,
                current_density=sources.current_density,
                name=name or f"{solution.name}.joule_heat",
            )

        def joule_heat_field(
            source: ElectrothermalSource3D,
        ) -> TimeDependentScalarField3D:
            electric_unit = source.electric_field.output_unit
            current_unit = source.current_density.output_unit

            def to_si(unit, value: Vec3) -> Vec3:
                return Vec3(
                    unit.to_si(value.x),
                    unit.to_si(value.y),
                    unit.to_si(value.z),
                )

            def evaluate(position: Vec3, time: float) -> float:
                electric = to_si(
                    electric_unit,
                    source.electric_field.evaluate(position, time),
                )
                current = to_si(
                    current_unit,
                    source.current_density.evaluate(position, time),
                )
                power_density = current.dot(electric)
                if not math.isfinite(power_density):
                    raise ValueError("Joule heat source became non-finite")
                return power_density

            return TimeDependentScalarField3D(
                evaluator=evaluate,
                name=source.name,
                output_unit=WATT_PER_CUBIC_METER,
            )

        def heat_problem_from_maxwell(
            solution: MaxwellSolution3D,
            sources: MaxwellSourceFields3D,
            *,
            initial_temperature: tuple[float, ...],
            material: ThermalMaterial3D,
            boundary: BoundaryMode3D = "fixed",
            initial_time: float | None = None,
            name: str = "electrothermal_heat3d",
        ) -> HeatConductionProblem3D:
            source = source_from_maxwell(solution, sources)
            start_time = solution.times[0] if initial_time is None else float(initial_time)
            if start_time < solution.times[0] or start_time > solution.times[-1]:
                raise ValueError("electrothermal initial_time must lie inside Maxwell history")
            return heat_problem_type(
                grid=solution.grid,
                initial_temperature=initial_temperature,
                material=material,
                boundary=boundary,
                volumetric_heat_source=joule_heat_field(source),
                initial_time=start_time,
                name=name,
            )

        registry.register_semantic_type(
            "physics.electrothermal.source3d",
            ElectrothermalSource3D,
        )
        registry.provide("physics.electrothermal.source3d", ElectrothermalSource3D)
        registry.provide(
            "physics.electrothermal.source_from_maxwell3d",
            source_from_maxwell,
        )
        registry.provide(
            "physics.electrothermal.joule_heat_field3d",
            joule_heat_field,
        )
        registry.provide(
            "physics.electrothermal.heat_problem_from_maxwell3d",
            heat_problem_from_maxwell,
        )
