from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec3
from spectra.core.units import DENSITY, METER_PER_SECOND_SQUARED, Quantity
from spectra.domains.mathematics.fields import TimeDependentScalarField3D, TimeDependentVectorField3D
from spectra.domains.partial_differential_equations.domain3d import BoundaryMode3D, UniformGrid3D
from spectra.domains.physics.elastodynamics3d import (
    ElastodynamicsProblem3D,
    ElastodynamicsSolution3D,
)
from spectra.domains.physics.thermoelasticity3d import ThermoelasticMaterial3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class ThermoelastodynamicsProblem3D:
    grid: UniformGrid3D
    initial_displacement: tuple[Vec3, ...]
    initial_velocity: tuple[Vec3, ...]
    material: ThermoelasticMaterial3D
    density: Quantity
    temperature: TimeDependentScalarField3D
    boundary: BoundaryMode3D = "fixed"
    external_body_acceleration: TimeDependentVectorField3D | None = None
    gradient_step: float = 1e-5
    initial_time: float = 0.0
    name: str = "thermoelastodynamics3d"

    def __post_init__(self) -> None:
        if len(self.initial_displacement) != self.grid.count:
            raise ValueError("thermoelastodynamic displacement sample count must match grid")
        if len(self.initial_velocity) != self.grid.count:
            raise ValueError("thermoelastodynamic velocity sample count must match grid")
        if self.density.unit.dimension != DENSITY or self.density.si_value <= 0.0:
            raise ValueError("thermoelastodynamic density must be positive")
        if not math.isfinite(self.gradient_step) or self.gradient_step <= 0.0:
            raise ValueError("thermoelastic gradient step must be finite and positive")
        if not math.isfinite(self.initial_time):
            raise ValueError("thermoelastodynamic initial_time must be finite")
        if not self.name:
            raise ValueError("thermoelastodynamic name cannot be empty")


@dataclass(frozen=True, slots=True)
class ThermoelastodynamicsSolution3D:
    elastodynamics: ElastodynamicsSolution3D
    material: ThermoelasticMaterial3D
    temperature_name: str

    @property
    def grid(self) -> UniformGrid3D:
        return self.elastodynamics.grid

    @property
    def times(self) -> tuple[float, ...]:
        return self.elastodynamics.times

    @property
    def displacements(self):
        return self.elastodynamics.displacements

    @property
    def velocities(self):
        return self.elastodynamics.velocities

    @property
    def duration(self) -> float:
        return self.elastodynamics.duration

    @property
    def name(self) -> str:
        return self.elastodynamics.name


class Thermoelastodynamics3DDomain:
    """One-way temperature-to-solid coupling composed over generic field calculus."""

    name = "physics.thermoelastodynamics.3d"
    version = "1"
    dependencies = (
        DomainDependency("physics.thermoelasticity.material3d"),
        DomainDependency("physics.elastodynamics.problem3d"),
        DomainDependency("physics.elastodynamics.solve3d"),
        DomainDependency("calculus.gradient_at"),
        DomainDependency("mathematics.time_vector_field3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        elastodynamics_problem_type = registry.require("physics.elastodynamics.problem3d")
        solve_elastodynamics = registry.require("physics.elastodynamics.solve3d")
        gradient_at = registry.require("calculus.gradient_at")

        def thermal_body_acceleration(
            problem: ThermoelastodynamicsProblem3D,
        ) -> TimeDependentVectorField3D:
            lam = problem.material.elastic.lame_lambda_si
            mu = problem.material.elastic.shear_modulus_si
            alpha = problem.material.thermal_expansion.si_value
            coefficient = -((3.0 * lam + 2.0 * mu) * alpha) / problem.density.si_value

            def evaluate(position: Vec3, time: float) -> Vec3:
                temperature_field = problem.temperature.at_time(time)
                grad_temperature = gradient_at(
                    temperature_field,
                    position,
                    step=problem.gradient_step,
                )
                thermal = grad_temperature * coefficient
                if problem.external_body_acceleration is not None:
                    thermal = thermal + problem.external_body_acceleration.evaluate(position, time)
                return thermal

            return TimeDependentVectorField3D(
                evaluator=evaluate,
                name=f"{problem.name}.thermal_acceleration",
                output_unit=METER_PER_SECOND_SQUARED,
            )

        def solve(
            problem: ThermoelastodynamicsProblem3D,
            *,
            end_time: float,
            steps: int = 128,
        ) -> ThermoelastodynamicsSolution3D:
            body = thermal_body_acceleration(problem)
            solution = solve_elastodynamics(
                elastodynamics_problem_type(
                    grid=problem.grid,
                    initial_displacement=problem.initial_displacement,
                    initial_velocity=problem.initial_velocity,
                    material=problem.material.elastic,
                    density=problem.density,
                    boundary=problem.boundary,
                    body_acceleration=body,
                    initial_time=problem.initial_time,
                    name=problem.name,
                ),
                end_time=end_time,
                steps=steps,
            )
            return ThermoelastodynamicsSolution3D(
                elastodynamics=solution,
                material=problem.material,
                temperature_name=problem.temperature.name,
            )

        registry.register_semantic_type(
            "physics.thermoelastodynamics.problem3d",
            ThermoelastodynamicsProblem3D,
        )
        registry.register_semantic_type(
            "physics.thermoelastodynamics.solution3d",
            ThermoelastodynamicsSolution3D,
        )
        registry.provide(
            "physics.thermoelastodynamics.problem3d",
            ThermoelastodynamicsProblem3D,
        )
        registry.provide(
            "physics.thermoelastodynamics.solution3d",
            ThermoelastodynamicsSolution3D,
        )
        registry.provide(
            "physics.thermoelastodynamics.thermal_body_acceleration3d",
            thermal_body_acceleration,
        )
        registry.provide("physics.thermoelastodynamics.solve3d", solve)
