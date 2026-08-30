from __future__ import annotations

from dataclasses import dataclass

from spectra.core.units import KELVIN
from spectra.domains.mathematics.fields import TimeDependentScalarField3D
from spectra.domains.partial_differential_equations.slices3d import ScalarPDESliceView3D
from spectra.domains.physics.heat_conduction3d import HeatConductionSolution3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class TemperatureFields3D:
    temperature: TimeDependentScalarField3D
    start_time: float
    end_time: float
    name: str = "temperature_fields3d"

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


class HeatConductionViews3DDomain:
    name = "physics.heat_conduction.views3d"
    version = "1"
    dependencies = (
        DomainDependency("physics.heat_conduction.solution3d"),
        DomainDependency("pde.time_scalar_field_from_grid_3d", min_version=2),
        DomainDependency("pde.scalar_slice_view3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        time_scalar = registry.require("pde.time_scalar_field_from_grid_3d", min_version=2)
        slice_type = registry.require("pde.scalar_slice_view3d")

        def fields_from_solution(solution: HeatConductionSolution3D) -> TemperatureFields3D:
            return TemperatureFields3D(
                temperature=time_scalar(
                    solution.grid,
                    solution.times,
                    solution.temperature_states,
                    name=f"{solution.name}.temperature",
                    output_unit=KELVIN,
                    temporal_outside="clamp",
                ),
                start_time=solution.times[0],
                end_time=solution.times[-1],
                name=f"{solution.name}.fields",
            )

        def temperature_slice(
            solution: HeatConductionSolution3D,
            *,
            axis: str = "z",
            index: int = 0,
            name: str | None = None,
        ) -> ScalarPDESliceView3D:
            return slice_type(
                solution=solution.pde_solution,
                axis=axis,
                index=index,
                name=name or f"{solution.name}.temperature_{axis}_slice_{index}",
            )

        registry.register_semantic_type("physics.temperature.fields3d", TemperatureFields3D)
        registry.provide("physics.heat_conduction.fields_from_solution3d", fields_from_solution)
        registry.provide("physics.heat_conduction.temperature_slice3d", temperature_slice)
