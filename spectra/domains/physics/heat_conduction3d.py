from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec3
from spectra.core.units import (
    DENSITY,
    SPECIFIC_HEAT,
    THERMAL_CONDUCTIVITY,
    VOLUMETRIC_POWER,
    Quantity,
)
from spectra.domains.mathematics.fields import TimeDependentScalarField3D
from spectra.domains.partial_differential_equations.domain3d import (
    BoundaryMode3D,
    ScalarPDESolution3D,
    UniformGrid3D,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class ThermalMaterial3D:
    density: Quantity
    specific_heat: Quantity
    thermal_conductivity: Quantity
    name: str = "thermal_material"

    def __post_init__(self) -> None:
        if self.density.unit.dimension != DENSITY or self.density.si_value <= 0.0:
            raise ValueError("thermal material density must be positive")
        if self.specific_heat.unit.dimension != SPECIFIC_HEAT or self.specific_heat.si_value <= 0.0:
            raise ValueError("thermal material specific heat must be positive")
        if (
            self.thermal_conductivity.unit.dimension != THERMAL_CONDUCTIVITY
            or self.thermal_conductivity.si_value <= 0.0
        ):
            raise ValueError("thermal conductivity must be positive")
        if not self.name:
            raise ValueError("thermal material name cannot be empty")

    @property
    def thermal_diffusivity_si(self) -> float:
        return self.thermal_conductivity.si_value / (
            self.density.si_value * self.specific_heat.si_value
        )


@dataclass(frozen=True, slots=True)
class HeatConductionProblem3D:
    grid: UniformGrid3D
    initial_temperature: tuple[float, ...]
    material: ThermalMaterial3D
    boundary: BoundaryMode3D = "fixed"
    volumetric_heat_source: TimeDependentScalarField3D | None = None
    initial_time: float = 0.0
    name: str = "heat_conduction3d"

    def __post_init__(self) -> None:
        if len(self.initial_temperature) != self.grid.count:
            raise ValueError("temperature sample count must match grid")
        if not all(math.isfinite(float(value)) and float(value) >= 0.0 for value in self.initial_temperature):
            raise ValueError("absolute temperature samples must be finite and non-negative")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown heat boundary mode: {self.boundary}")
        if self.volumetric_heat_source is not None and self.volumetric_heat_source.output_unit is not None:
            if self.volumetric_heat_source.output_unit.dimension != VOLUMETRIC_POWER:
                raise ValueError("heat source field must use volumetric-power units")
        if not math.isfinite(self.initial_time):
            raise ValueError("heat initial_time must be finite")
        if not self.name:
            raise ValueError("heat-conduction name cannot be empty")


@dataclass(frozen=True, slots=True)
class HeatConductionSolution3D:
    pde_solution: ScalarPDESolution3D
    material: ThermalMaterial3D
    boundary: BoundaryMode3D

    @property
    def grid(self) -> UniformGrid3D:
        return self.pde_solution.grid

    @property
    def times(self) -> tuple[float, ...]:
        return self.pde_solution.times

    @property
    def temperature_states(self) -> tuple[tuple[float, ...], ...]:
        return self.pde_solution.states

    @property
    def duration(self) -> float:
        return self.pde_solution.duration

    @property
    def name(self) -> str:
        return self.pde_solution.name


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


class HeatConduction3DDomain:
    """Transient heat conduction composed from generic scalar PDE capabilities."""

    name = "physics.heat_conduction.3d"
    version = "1"
    dependencies = (
        DomainDependency("pde.scalar_problem3d"),
        DomainDependency("pde.laplacian_3d"),
        DomainDependency("pde.solve_method_of_lines_3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        problem_type = registry.require("pde.scalar_problem3d")
        laplacian = registry.require("pde.laplacian_3d")
        solve_pde = registry.require("pde.solve_method_of_lines_3d")

        def solve_heat(
            problem: HeatConductionProblem3D,
            *,
            end_time: float,
            steps: int = 128,
        ) -> HeatConductionSolution3D:
            alpha = problem.material.thermal_diffusivity_si
            volumetric_capacity = (
                problem.material.density.si_value * problem.material.specific_heat.si_value
            )

            def rhs(time, grid, values):
                curvature = laplacian(values, grid, boundary=problem.boundary)
                result = []
                for index, diffuse in enumerate(curvature):
                    if problem.boundary == "fixed" and _is_boundary(grid, index):
                        result.append(0.0)
                        continue
                    source_rate = 0.0
                    if problem.volumetric_heat_source is not None:
                        x, y, z = grid.coordinates[index]
                        source = problem.volumetric_heat_source.evaluate(Vec3(x, y, z), time)
                        if problem.volumetric_heat_source.output_unit is not None:
                            source = problem.volumetric_heat_source.output_unit.to_si(source)
                        source_rate = source / volumetric_capacity
                    result.append(alpha * diffuse + source_rate)
                return tuple(result)

            solution = solve_pde(
                problem_type(
                    grid=problem.grid,
                    initial_values=tuple(float(value) for value in problem.initial_temperature),
                    rhs=rhs,
                    initial_time=problem.initial_time,
                    name=problem.name,
                ),
                end_time=end_time,
                steps=steps,
            )
            return HeatConductionSolution3D(
                pde_solution=solution,
                material=problem.material,
                boundary=problem.boundary,
            )

        registry.register_semantic_type("physics.thermal.material3d", ThermalMaterial3D)
        registry.register_semantic_type("physics.heat_conduction.problem3d", HeatConductionProblem3D)
        registry.register_semantic_type("physics.heat_conduction.solution3d", HeatConductionSolution3D)
        registry.provide("physics.thermal.material3d", ThermalMaterial3D)
        registry.provide("physics.heat_conduction.problem3d", HeatConductionProblem3D)
        registry.provide("physics.heat_conduction.solution3d", HeatConductionSolution3D)
        registry.provide("physics.heat_conduction.solve3d", solve_heat)
