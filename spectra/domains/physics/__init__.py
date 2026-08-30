from spectra.domains.physics.electromagnetism import (
    ElectromagnetismDomain,
    PointCharge,
    electric_field_from_point_charges,
)
from spectra.domains.physics.mechanics import MechanicsDomain, ParticleProblem, Trajectory
from spectra.domains.physics.particles import (
    Particle,
    ParticleSystemProblem,
    ParticleSystemTrajectory,
    ParticleSystemsDomain,
)
from spectra.domains.physics.quantum import QuantumDomain, QuantumObservable, QuantumState
from spectra.domains.physics.waves import (
    HarmonicWave1D,
    WaveAnimation1D,
    WaveProfile1D,
    WaveSuperposition1D,
    WavesDomain,
    as_time_scalar_field,
)

__all__ = [
    "ElectromagnetismDomain",
    "PointCharge",
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
    "HarmonicWave1D",
    "WaveAnimation1D",
    "WaveProfile1D",
    "WaveSuperposition1D",
    "WavesDomain",
    "as_time_scalar_field",
]
