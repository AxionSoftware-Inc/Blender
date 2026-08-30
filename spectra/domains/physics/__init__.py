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
from spectra.domains.physics.diffusion3d import (
    Diffusion3DDomain,
    DiffusionProblem3D,
    DiffusionSolution3D,
)
from spectra.domains.physics.elasticity import (
    ElasticityDomain,
    IsotropicElasticMaterial,
    StrainTensor3D,
    StressTensor3D,
    traction_at,
    von_mises_stress,
)
from spectra.domains.physics.elasticity_fields import ElasticityFieldsDomain
from spectra.domains.physics.elasticity_principal import (
    PrincipalStressDomain,
    PrincipalStressState3D,
)
from spectra.domains.physics.electromagnetism import (
    ElectromagnetismDomain,
    PlaneElectromagneticWave,
    PointCharge,
    SPEED_OF_LIGHT,
    electric_field_from_point_charges,
)
from spectra.domains.physics.electrostatic_potential2d import (
    ElectrostaticPotential2DDomain,
    ElectrostaticPotentialProblem2D,
    ElectrostaticPotentialSolution2D,
)
from spectra.domains.physics.electrostatic_potential3d import (
    ElectrostaticPotential3DDomain,
    ElectrostaticPotentialProblem3D,
    ElectrostaticPotentialSolution3D,
)
from spectra.domains.physics.fluid_diagnostics import (
    FlowHistoryDiagnostics2D,
    FluidDiagnostics2DDomain,
    peclet_number,
    reynolds_number,
)
from spectra.domains.physics.fluid_invariants import (
    FlowInvariantHistory2D,
    FlowInvariantSnapshot2D,
    FluidInvariants2DDomain,
)
from spectra.domains.physics.fluid_kinematics import (
    FluidKinematics2DDomain,
    SteadyFlow2D,
    UnsteadyFlow2D,
)
from spectra.domains.physics.fluid_transport import (
    FluidTransport2DDomain,
    PassiveScalarProblem2D,
    PassiveScalarSolution2D,
)
from spectra.domains.physics.general_relativity import (
    GeneralRelativityDomain,
    SchwarzschildSpacetime,
)
from spectra.domains.physics.gravitational_potential3d import (
    GravitationalPotential3DDomain,
    GravitationalPotentialProblem3D,
    GravitationalPotentialSolution3D,
)
from spectra.domains.physics.incompressible_flow import (
    IncompressibleFlow2DDomain,
    IncompressibleFlowProblem2D,
    IncompressibleFlowSolution2D,
    IncompressibleFlowState2D,
)
from spectra.domains.physics.incompressible_flow_views import (
    IncompressibleFlowFields2D,
    IncompressibleFlowViews2DDomain,
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
from spectra.domains.physics.schrodinger2d import (
    Schrodinger2DDomain,
    SchrodingerProblem2D,
    SchrodingerSolution2D,
)
from spectra.domains.physics.vorticity_streamfunction import (
    VorticityStreamfunction2DDomain,
    VorticityStreamfunctionProblem2D,
    VorticityStreamfunctionSolution2D,
)
from spectra.domains.physics.wave_equation2d import (
    WaveEquation2DDomain,
    WaveEquationProblem2D,
    WaveEquationSolution2D,
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
    "Diffusion3DDomain",
    "DiffusionDomain",
    "DiffusionProblem1D",
    "DiffusionProblem2D",
    "DiffusionProblem3D",
    "DiffusionSolution1D",
    "DiffusionSolution2D",
    "DiffusionSolution3D",
    "ElasticityDomain",
    "ElasticityFieldsDomain",
    "ElectromagnetismDomain",
    "ElectrostaticPotential2DDomain",
    "ElectrostaticPotential3DDomain",
    "ElectrostaticPotentialProblem2D",
    "ElectrostaticPotentialProblem3D",
    "ElectrostaticPotentialSolution2D",
    "ElectrostaticPotentialSolution3D",
    "FlowHistoryDiagnostics2D",
    "FlowInvariantHistory2D",
    "FlowInvariantSnapshot2D",
    "FluidDiagnostics2DDomain",
    "FluidInvariants2DDomain",
    "FluidKinematics2DDomain",
    "FluidTransport2DDomain",
    "GeneralRelativityDomain",
    "GravitationalPotential3DDomain",
    "GravitationalPotentialProblem3D",
    "GravitationalPotentialSolution3D",
    "HarmonicWave1D",
    "IncompressibleFlow2DDomain",
    "IncompressibleFlowFields2D",
    "IncompressibleFlowProblem2D",
    "IncompressibleFlowSolution2D",
    "IncompressibleFlowState2D",
    "IncompressibleFlowViews2DDomain",
    "IsotropicElasticMaterial",
    "MechanicsDomain",
    "Particle",
    "ParticleProblem",
    "ParticleSystemProblem",
    "ParticleSystemTrajectory",
    "ParticleSystemsDomain",
    "PassiveScalarProblem2D",
    "PassiveScalarSolution2D",
    "PlaneElectromagneticWave",
    "PointCharge",
    "PrincipalStressDomain",
    "PrincipalStressState3D",
    "QuantumDomain",
    "QuantumObservable",
    "QuantumState",
    "RelativityDomain",
    "SPEED_OF_LIGHT",
    "Schrodinger2DDomain",
    "SchrodingerDomain",
    "SchrodingerProblem1D",
    "SchrodingerProblem2D",
    "SchrodingerSolution1D",
    "SchrodingerSolution2D",
    "SchwarzschildSpacetime",
    "SpacetimeEvent",
    "SpatialQuantumDomain",
    "SpatialWavefunction1D",
    "SteadyFlow2D",
    "StrainTensor3D",
    "StressTensor3D",
    "Trajectory",
    "UnsteadyFlow2D",
    "VorticityStreamfunction2DDomain",
    "VorticityStreamfunctionProblem2D",
    "VorticityStreamfunctionSolution2D",
    "WaveAnimation1D",
    "WaveEquation2DDomain",
    "WaveEquationProblem2D",
    "WaveEquationSolution2D",
    "WaveProfile1D",
    "WaveSuperposition1D",
    "WavesDomain",
    "as_time_scalar_field",
    "compile_spatial_wavefunction_scene",
    "electric_field_from_point_charges",
    "four_velocity",
    "lorentz_factor",
    "minkowski_metric",
    "normalize_wavefunction_samples",
    "peclet_number",
    "probability_mass_1d",
    "reynolds_number",
    "traction_at",
    "von_mises_stress",
]
