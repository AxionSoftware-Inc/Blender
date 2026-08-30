from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.domains.physics.elasticity import StrainTensor3D, StressTensor3D
from spectra.domains.physics.elastodynamics3d import ElastodynamicsSolution3D
from spectra.domains.registry import DomainDependency, DomainRegistry
from spectra.domains.tensor_algebra import Tensor


@dataclass(frozen=True, slots=True)
class ElastodynamicsDiagnosticSnapshot3D:
    time: float
    max_displacement: float
    max_speed: float
    max_von_mises_stress_si: float
    kinetic_energy_si: float
    strain_energy_si: float

    def __post_init__(self) -> None:
        for name, value in (
            ("time", self.time),
            ("max_displacement", self.max_displacement),
            ("max_speed", self.max_speed),
            ("max_von_mises_stress_si", self.max_von_mises_stress_si),
            ("kinetic_energy_si", self.kinetic_energy_si),
            ("strain_energy_si", self.strain_energy_si),
        ):
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        if min(
            self.max_displacement,
            self.max_speed,
            self.max_von_mises_stress_si,
            self.kinetic_energy_si,
            self.strain_energy_si,
        ) < 0.0:
            raise ValueError("elastodynamics diagnostic magnitudes must be non-negative")


@dataclass(frozen=True, slots=True)
class ElastodynamicsDiagnostics3D:
    snapshots: tuple[ElastodynamicsDiagnosticSnapshot3D, ...]
    longitudinal_wave_speed_si: float
    shear_wave_speed_si: float
    name: str = "elastodynamics_diagnostics3d"

    def __post_init__(self) -> None:
        if not self.snapshots:
            raise ValueError("elastodynamics diagnostics cannot be empty")
        if any(right.time <= left.time for left, right in zip(self.snapshots, self.snapshots[1:])):
            raise ValueError("elastodynamics diagnostic times must be strictly increasing")
        if self.longitudinal_wave_speed_si <= 0.0 or self.shear_wave_speed_si <= 0.0:
            raise ValueError("elastic wave speeds must be positive")


def _strain_states(
    displacement,
    grid,
    gradient,
    boundary,
) -> tuple[StrainTensor3D, ...]:
    grad_x = gradient(tuple(value.x for value in displacement), grid, boundary=boundary)
    grad_y = gradient(tuple(value.y for value in displacement), grid, boundary=boundary)
    grad_z = gradient(tuple(value.z for value in displacement), grid, boundary=boundary)
    result = []
    for gx, gy, gz in zip(grad_x, grad_y, grad_z, strict=True):
        rows = (
            (gx.x, gx.y, gx.z),
            (gy.x, gy.y, gy.z),
            (gz.x, gz.y, gz.z),
        )
        values = tuple(
            0.5 * (rows[row][column] + rows[column][row])
            for row in range(3)
            for column in range(3)
        )
        result.append(StrainTensor3D(Tensor((3, 3), values, name="sampled_strain")))
    return tuple(result)


def _strain_energy_density(stress: StressTensor3D, strain: StrainTensor3D) -> float:
    return 0.5 * sum(
        stress.tensor.at(row, column) * strain.tensor.at(row, column)
        for row in range(3)
        for column in range(3)
    )


class ElastodynamicsDiagnostics3DDomain:
    """Stress and energy verification for sampled linear elastodynamics histories."""

    name = "physics.elastodynamics.diagnostics3d"
    version = "1"
    dependencies = (
        DomainDependency("physics.elastodynamics.solution3d"),
        DomainDependency("physics.elastodynamics.wave_speeds"),
        DomainDependency("physics.elasticity.stress_from_strain"),
        DomainDependency("physics.elasticity.von_mises_stress"),
        DomainDependency("pde.gradient_grid_3d"),
        DomainDependency("pde.integrate_scalar_grid_3d"),
        DomainDependency("pde.integrate_vector_magnitude_squared_grid_3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        wave_speeds = registry.require("physics.elastodynamics.wave_speeds")
        stress_from_strain = registry.require("physics.elasticity.stress_from_strain")
        von_mises = registry.require("physics.elasticity.von_mises_stress")
        gradient = registry.require("pde.gradient_grid_3d")
        integrate_scalar = registry.require("pde.integrate_scalar_grid_3d")
        integrate_vector_sq = registry.require("pde.integrate_vector_magnitude_squared_grid_3d")

        def diagnose(solution: ElastodynamicsSolution3D) -> ElastodynamicsDiagnostics3D:
            rho = solution.density.si_value
            snapshots = []
            for time, displacement, velocity in zip(
                solution.times,
                solution.displacements,
                solution.velocities,
                strict=True,
            ):
                strains = _strain_states(
                    displacement,
                    solution.grid,
                    gradient,
                    solution.boundary,
                )
                stresses = tuple(
                    stress_from_strain(solution.material, strain) for strain in strains
                )
                energy_density = tuple(
                    max(0.0, _strain_energy_density(stress, strain))
                    for stress, strain in zip(stresses, strains, strict=True)
                )
                snapshots.append(
                    ElastodynamicsDiagnosticSnapshot3D(
                        time=time,
                        max_displacement=max(value.magnitude for value in displacement),
                        max_speed=max(value.magnitude for value in velocity),
                        max_von_mises_stress_si=max(
                            von_mises(stress).si_value for stress in stresses
                        ),
                        kinetic_energy_si=0.5
                        * rho
                        * integrate_vector_sq(velocity, solution.grid),
                        strain_energy_si=integrate_scalar(energy_density, solution.grid),
                    )
                )
            longitudinal, shear = wave_speeds(solution.material, solution.density)
            return ElastodynamicsDiagnostics3D(
                snapshots=tuple(snapshots),
                longitudinal_wave_speed_si=longitudinal,
                shear_wave_speed_si=shear,
                name=f"{solution.name}.diagnostics",
            )

        registry.register_semantic_type(
            "physics.elastodynamics.diagnostic_snapshot3d",
            ElastodynamicsDiagnosticSnapshot3D,
        )
        registry.register_semantic_type(
            "physics.elastodynamics.diagnostics3d",
            ElastodynamicsDiagnostics3D,
        )
        registry.provide(
            "physics.elastodynamics.diagnose3d",
            diagnose,
        )
