from spectra.domains.physics.diffusion import (
    DiffusionDomain,
    DiffusionProblem1D,
    DiffusionSolution1D,
)
from spectra.domains.physics.diffusion2d import (
    Diffusion2DDomain,
    DiffusionProblem2D,
    DiffusionSolution2D,
)
from spectra.domains.physics.electromagnetism import (
    ElectromagnetismDomain,
    PlaneElectromagneticWave,
    PointCharge,
    SPEED_OF_LIGHT,
    electric_field_from_point_charges,
)
from spectra.domains.physics.general_relativity import (
    GeneralRelativityDomain,
    SchwarzschildSpacetime,
)
from spectra.domains.physics.mechanics import MechanicsDomain, ParticleProblem, Trajectory
from spectra.domains.physics.particles import (
    Particle,
    ParticleSystemProblem,
    ParticleSystemTrajectory,
    ParticleSystemsDomain,
)
from spectra.domains.physics.quantum import QuantumDomain, QuantumObservable, QuantumState
from spectra.domains.physics.quantum_spatial import (
    SpatialQuantumDomain,
    SpatialWavefunction1D,
    compile_spatial_wavefunction_scene,
)
from spectra.domains.physics.relativity import (
    RelativityDomain,
    SpacetimeEvent,
    four_velocity,
    lorentz_factor,
    minkowski_metric,
)
from spectra.domains.physics.schrodinger import (
    SchrodingerDomain,
    SchrodingerProblem1D,
    SchrodingerSolution1D,
    normalize_wavefunction_samples,
    probability_mass_1d,
)
from spectra.domains.physics.waves import (
    HarmonicWave1D,
    WaveAnimation1D,
    WaveProfile1D,
    WaveSuperposition1D,
    WavesDomain,
    as_time_scalar_field,
)

__all__ = [
    "Diffusion2DDomain",
    "DiffusionDomain",
    "DiffusionProblem1D",
    "DiffusionProblem2D",
    "DiffusionSolution1D",
    "DiffusionSolution2D",
    "ElectromagnetismDomain",
    "GeneralRelativityDomain",
    "PlaneElectromagneticWave",
    "PointCharge",
    "SPEED_OF_LIGHT",
    "SchwarzschildSpacetime",
    "electric_field_from_point_charges",
    "MechanicsDomain",
    "ParticleProblem",
    "Trajectory",
    "Particle",
    "ParticleSystemProblem",
    "ParticleSystemTrajectory",
    "ParticleSystemsDomain",
    "QuantumDomain",
    "QuantumObservable",
    "QuantumState",
    "RelativityDomain",
    "SpacetimeEvent",
    "four_velocity",
    "lorentz_factor",
    "minkowski_metric",
    "SpatialQuantumDomain",
    "SpatialWavefunction1D",
    "compile_spatial_wavefunction_scene",
    "SchrodingerDomain",
    "SchrodingerProblem1D",
    "SchrodingerSolution1D",
    "normalize_wavefunction_samples",
    "probability_mass_1d",
    "HarmonicWave1D",
    "WaveAnimation1D",
    "WaveProfile1D",
    "WaveSuperposition1D",
    "WavesDomain",
    "as_time_scalar_field",
]
