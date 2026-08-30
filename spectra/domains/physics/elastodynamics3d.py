from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec3
from spectra.core.units import ACCELERATION, DENSITY, Quantity
from spectra.domains.mathematics.fields import TimeDependentVectorField3D
from spectra.domains.partial_differential_equations.domain3d import BoundaryMode3D, UniformGrid3D
from spectra.domains.partial_differential_equations.vector_second_order3d import (
    SecondOrderVectorPDEProblem3D,
    SecondOrderVectorPDESolution3D,
)
from spectra.domains.physics.elasticity import IsotropicElasticMaterial
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class ElastodynamicsProblem3D:
    """Small-strain homogeneous isotropic linear elastodynamics on a regular grid."""

    grid: UniformGrid3D
    initial_displacement: tuple[Vec3, ...]
    initial_velocity: tuple[Vec3, ...]
    material: IsotropicElasticMaterial
    density: Quantity
    boundary: BoundaryMode3D = "fixed"
    body_acceleration: TimeDependentVectorField3D | None = None
    initial_time: float = 0.0
    name: str = "elastodynamics3d"

    def __post_init__(self) -> None:
        if len(self.initial_displacement) != self.grid.count:
            raise ValueError("elastodynamics displacement sample count must match grid")
        if len(self.initial_velocity) != self.grid.count:
            raise ValueError("elastodynamics velocity sample count must match grid")
        if any(not isinstance(value, Vec3) for value in self.initial_displacement):
            raise TypeError("elastodynamics displacement samples must be Vec3")
        if any(not isinstance(value, Vec3) for value in self.initial_velocity):
            raise TypeError("elastodynamics velocity samples must be Vec3")
        if self.density.unit.dimension != DENSITY or self.density.si_value <= 0.0:
            raise ValueError("elastodynamics density must be a positive density quantity")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown elastodynamics boundary mode: {self.boundary}")
        if self.body_acceleration is not None and self.body_acceleration.output_unit is not None:
            if self.body_acceleration.output_unit.dimension != ACCELERATION:
                raise ValueError("elastodynamics body field must represent acceleration")
        if not math.isfinite(self.initial_time):
            raise ValueError("elastodynamics initial_time must be finite")
        if not self.name:
            raise ValueError("elastodynamics name cannot be empty")
        if self.boundary == "fixed":
            for index, velocity in enumerate(self.initial_velocity):
                if _is_boundary(self.grid, index) and velocity != Vec3(0.0, 0.0, 0.0):
                    raise ValueError("fixed elastodynamics boundary requires zero initial velocity")


@dataclass(frozen=True, slots=True)
class ElastodynamicsSolution3D:
    pde_solution: SecondOrderVectorPDESolution3D
    material: IsotropicElasticMaterial
    density: Quantity
    boundary: BoundaryMode3D

    @property
    def grid(self) -> UniformGrid3D:
        return self.pde_solution.grid

    @property
    def times(self) -> tuple[float, ...]:
        return self.pde_solution.times

    @property
    def displacements(self) -> tuple[tuple[Vec3, ...], ...]:
        return self.pde_solution.values

    @property
    def velocities(self) -> tuple[tuple[Vec3, ...], ...]:
        return self.pde_solution.velocities

    @property
    def duration(self) -> float:
        return self.pde_solution.duration

    @property
    def name(self) -> str:
        return self.pde_solution.name


def _is_boundary(grid: UniformGrid3D, index: int) -> bool:
    xy = grid.x.count * grid.y.count
    z_index = index // xy
    remainder = index % xy
    y_index = remainder // grid.x.count
    x_index = remainder % grid.x.count
    return (
        x_index in {0, grid.x.count - 1}
        or y_index in {0, grid.y.count - 1}
        or z_index in {0, grid.z.count - 1}
    )


def _vector_to_si(field: TimeDependentVectorField3D, value: Vec3) -> Vec3:
    unit = field.output_unit
    if unit is None:
        return value
    return Vec3(unit.to_si(value.x), unit.to_si(value.y), unit.to_si(value.z))


def elastic_wave_speeds(
    material: IsotropicElasticMaterial,
    density: Quantity,
) -> tuple[float, float]:
    """Return longitudinal and shear wave speeds in SI metres/second."""

    if density.unit.dimension != DENSITY or density.si_value <= 0.0:
        raise ValueError("elastic wave speed density must be positive")
    rho = density.si_value
    lam = material.lame_lambda_si
    mu = material.shear_modulus_si
    longitudinal = math.sqrt((lam + 2.0 * mu) / rho)
    shear = math.sqrt(mu / rho)
    return longitudinal, shear


class Elastodynamics3DDomain:
    """Linear isotropic solid dynamics composed from generic PDE operators."""

    name = "physics.elastodynamics.3d"
    version = "1"
    dependencies = (
        DomainDependency("physics.elasticity.material"),
        DomainDependency("pde.second_order_vector_problem3d"),
        DomainDependency("pde.solve_second_order_vector_3d"),
        DomainDependency("pde.laplacian_3d"),
        DomainDependency("pde.divergence_grid_3d"),
        DomainDependency("pde.gradient_grid_3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        vector_problem_type = registry.require("pde.second_order_vector_problem3d")
        solve_second_order = registry.require("pde.solve_second_order_vector_3d")
        laplacian = registry.require("pde.laplacian_3d")
        divergence = registry.require("pde.divergence_grid_3d")
        gradient = registry.require("pde.gradient_grid_3d")

        def solve_elastodynamics(
            problem: ElastodynamicsProblem3D,
            *,
            end_time: float,
            steps: int = 128,
        ) -> ElastodynamicsSolution3D:
            rho = problem.density.si_value
            lam = problem.material.lame_lambda_si
            mu = problem.material.shear_modulus_si
            grad_div_factor = (lam + mu) / rho
            laplacian_factor = mu / rho

            def acceleration(
                time: float,
                grid: UniformGrid3D,
                displacement: tuple[Vec3, ...],
                _velocity: tuple[Vec3, ...],
            ) -> tuple[Vec3, ...]:
                div_u = divergence(displacement, grid, boundary=problem.boundary)
                grad_div_u = gradient(div_u, grid, boundary=problem.boundary)
                lap_x = laplacian(
                    tuple(value.x for value in displacement),
                    grid,
                    boundary=problem.boundary,
                )
                lap_y = laplacian(
                    tuple(value.y for value in displacement),
                    grid,
                    boundary=problem.boundary,
                )
                lap_z = laplacian(
                    tuple(value.z for value in displacement),
                    grid,
                    boundary=problem.boundary,
                )

                result = []
                for index, (grad_div_value, lx, ly, lz) in enumerate(
                    zip(grad_div_u, lap_x, lap_y, lap_z, strict=True)
                ):
                    if problem.boundary == "fixed" and _is_boundary(grid, index):
                        result.append(Vec3(0.0, 0.0, 0.0))
                        continue
                    elastic = Vec3(
                        grad_div_factor * grad_div_value.x + laplacian_factor * lx,
                        grad_div_factor * grad_div_value.y + laplacian_factor * ly,
                        grad_div_factor * grad_div_value.z + laplacian_factor * lz,
                    )
                    if problem.body_acceleration is not None:
                        x, y, z = grid.coordinates[index]
                        body = problem.body_acceleration.evaluate(Vec3(x, y, z), time)
                        elastic = elastic + _vector_to_si(problem.body_acceleration, body)
                    result.append(elastic)
                return tuple(result)

            pde_solution = solve_second_order(
                vector_problem_type(
                    grid=problem.grid,
                    initial_values=problem.initial_displacement,
                    initial_velocity=problem.initial_velocity,
                    acceleration_rhs=acceleration,
                    initial_time=problem.initial_time,
                    name=problem.name,
                ),
                end_time=end_time,
                steps=steps,
            )
            return ElastodynamicsSolution3D(
                pde_solution=pde_solution,
                material=problem.material,
                density=problem.density,
                boundary=problem.boundary,
            )

        registry.register_semantic_type(
            "physics.elastodynamics.problem3d",
            ElastodynamicsProblem3D,
        )
        registry.register_semantic_type(
            "physics.elastodynamics.solution3d",
            ElastodynamicsSolution3D,
        )
        registry.provide("physics.elastodynamics.problem3d", ElastodynamicsProblem3D)
        registry.provide("physics.elastodynamics.solution3d", ElastodynamicsSolution3D)
        registry.provide("physics.elastodynamics.wave_speeds", elastic_wave_speeds)
        registry.provide("physics.elastodynamics.solve3d", solve_elastodynamics)
