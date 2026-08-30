from spectra.domains.physics.acoustics3d import (
    AcousticPressureProblem3D,
    AcousticPressureSolution3D,
    Acoustics3DDomain,
)
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
from spectra.domains.physics.elastodynamics3d import (
    Elastodynamics3DDomain,
    ElastodynamicsProblem3D,
    ElastodynamicsSolution3D,
    elastic_wave_speeds,
)
from spectra.domains.physics.elastodynamics_diagnostics3d import (
    ElastodynamicsDiagnosticSnapshot3D,
    ElastodynamicsDiagnostics3D,
    ElastodynamicsDiagnostics3DDomain,
)
from spectra.domains.physics.elastodynamics_views3d import (
    ElastodynamicsDeformedGridView3D,
    ElastodynamicsFields3D,
    ElastodynamicsViews3DDomain,
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
from spectra.domains.physics.field_particles import FieldParticleDynamicsDomain
from spectra.domains.physics.fluid_diagnostics import (
    FlowHistoryDiagnostics2D,
    FluidDiagnostics2DDomain,
    peclet_number,
    reynolds_number,
)
from spectra.domains.physics.fluid_diagnostics3d import (
    FlowHistoryDiagnostics3D,
    FluidDiagnostics3DDomain,
)
from spectra.domains.physics.fluid_invariants import (
    FlowInvariantHistory2D,
    FlowInvariantSnapshot2D,
    FluidInvariants2DDomain,
)
from spectra.domains.physics.fluid_invariants3d import (
    FlowInvariantHistory3D,
    FlowInvariantSnapshot3D,
    FluidInvariants3DDomain,
)
from spectra.domains.physics.fluid_kinematics import (
    FluidKinematics2DDomain,
    SteadyFlow2D,
    UnsteadyFlow2D,
)
from spectra.domains.physics.fluid_kinematics3d import (
    FluidKinematics3DDomain,
    SteadyFlow3D,
    UnsteadyFlow3D,
)
from spectra.domains.physics.fluid_transport import (
    FluidTransport2DDomain,
    PassiveScalarProblem2D,
    PassiveScalarSolution2D,
)
from spectra.domains.physics.fluid_transport3d import (
    FluidTransport3DDomain,
    PassiveScalarProblem3D,
    PassiveScalarSolution3D,
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
from spectra.domains.physics.incompressible_flow3d import (
    IncompressibleFlow3DDomain,
    IncompressibleFlowProblem3D,
    IncompressibleFlowSolution3D,
    IncompressibleFlowState3D,
)
from spectra.domains.physics.incompressible_flow_views import (
    IncompressibleFlowFields2D,
    IncompressibleFlowViews2DDomain,
)
from spectra.domains.physics.incompressible_flow_views3d import (
    IncompressibleFlowFields3D,
    IncompressibleFlowViews3DDomain,
)
from spectra.domains.physics.mechanics import MechanicsDomain, ParticleProblem, Trajectory
from spectra.domains.physics.particles import (
    Particle,
    ParticleSystemProblem,
    ParticleSystemTrajectory,
    ParticleSystemsDomain,
)
from spectra.domains.physics.potential_energy import (
    ParticleEnergyHistory,
    PotentialEnergyDiagnosticsDomain,
)
from spectra.domains.physics.potential_sources3d import (
    PointChargeSource3D,
    PointMassSource3D,
    PotentialSources3DDomain,
)
from spectra.domains.physics.quantum import QuantumDomain, QuantumObservable, QuantumState
from spectra.domains.physics.quantum_current3d import (
    QuantumProbabilityCurrent3DDomain,
    QuantumProbabilityFields3D,
    QuantumProbabilityFlow3D,
)
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
from spectra.domains.physics.schrodinger3d import (
    Schrodinger3DDomain,
    SchrodingerProblem3D,
    SchrodingerSolution3D,
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
from spectra.domains.physics.wave_equation3d import (
    WaveEquation3DDomain,
    WaveEquationProblem3D,
    WaveEquationSolution3D,
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
    "AcousticPressureProblem3D",
    "AcousticPressureSolution3D",
    "Acoustics3DDomain",
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
    "Elastodynamics3DDomain",
    "ElastodynamicsDeformedGridView3D",
    "ElastodynamicsDiagnosticSnapshot3D",
    "ElastodynamicsDiagnostics3D",
    "ElastodynamicsDiagnostics3DDomain",
    "ElastodynamicsFields3D",
    "ElastodynamicsProblem3D",
    "ElastodynamicsSolution3D",
    "ElastodynamicsViews3DDomain",
    "ElectromagnetismDomain",
    "ElectrostaticPotential2DDomain",
    "ElectrostaticPotential3DDomain",
    "ElectrostaticPotentialProblem2D",
    "ElectrostaticPotentialProblem3D",
    "ElectrostaticPotentialSolution2D",
    "ElectrostaticPotentialSolution3D",
    "FieldParticleDynamicsDomain",
    "FlowHistoryDiagnostics2D",
    "FlowHistoryDiagnostics3D",
    "FlowInvariantHistory2D",
    "FlowInvariantHistory3D",
    "FlowInvariantSnapshot2D",
    "FlowInvariantSnapshot3D",
    "FluidDiagnostics2DDomain",
    "FluidDiagnostics3DDomain",
    "FluidInvariants2DDomain",
    "FluidInvariants3DDomain",
    "FluidKinematics2DDomain",
    "FluidKinematics3DDomain",
    "FluidTransport2DDomain",
    "FluidTransport3DDomain",
    "GeneralRelativityDomain",
    "GravitationalPotential3DDomain",
    "GravitationalPotentialProblem3D",
    "GravitationalPotentialSolution3D",
    "HarmonicWave1D",
    "IncompressibleFlow2DDomain",
    "IncompressibleFlow3DDomain",
    "IncompressibleFlowFields2D",
    "IncompressibleFlowFields3D",
    "IncompressibleFlowProblem2D",
    "IncompressibleFlowProblem3D",
    "IncompressibleFlowSolution2D",
    "IncompressibleFlowSolution3D",
    "IncompressibleFlowState2D",
    "IncompressibleFlowState3D",
    "IncompressibleFlowViews2DDomain",
    "IncompressibleFlowViews3DDomain",
    "IsotropicElasticMaterial",
    "MechanicsDomain",
    "Particle",
    "ParticleEnergyHistory",
    "ParticleProblem",
    "ParticleSystemProblem",
    "ParticleSystemTrajectory",
    "ParticleSystemsDomain",
    "PassiveScalarProblem2D",
    "PassiveScalarProblem3D",
    "PassiveScalarSolution2D",
    "PassiveScalarSolution3D",
    "PlaneElectromagneticWave",
    "PointCharge",
    "PointChargeSource3D",
    "PointMassSource3D",
    "PotentialEnergyDiagnosticsDomain",
    "PotentialSources3DDomain",
    "PrincipalStressDomain",
    "PrincipalStressState3D",
    "QuantumDomain",
    "QuantumObservable",
    "QuantumProbabilityCurrent3DDomain",
    "QuantumProbabilityFields3D",
    "QuantumProbabilityFlow3D",
    "QuantumState",
    "RelativityDomain",
    "SPEED_OF_LIGHT",
    "Schrodinger2DDomain",
    "Schrodinger3DDomain",
    "SchrodingerDomain",
    "SchrodingerProblem1D",
    "SchrodingerProblem2D",
    "SchrodingerProblem3D",
    "SchrodingerSolution1D",
    "SchrodingerSolution2D",
    "SchrodingerSolution3D",
    "SchwarzschildSpacetime",
    "SpacetimeEvent",
    "SpatialQuantumDomain",
    "SpatialWavefunction1D",
    "SteadyFlow2D",
    "SteadyFlow3D",
    "StrainTensor3D",
    "StressTensor3D",
    "Trajectory",
    "UnsteadyFlow2D",
    "UnsteadyFlow3D",
    "VorticityStreamfunction2DDomain",
    "VorticityStreamfunctionProblem2D",
    "VorticityStreamfunctionSolution2D",
    "WaveAnimation1D",
    "WaveEquation2DDomain",
    "WaveEquation3DDomain",
    "WaveEquationProblem2D",
    "WaveEquationProblem3D",
    "WaveEquationSolution2D",
    "WaveEquationSolution3D",
    "WaveProfile1D",
    "WaveSuperposition1D",
    "WavesDomain",
    "as_time_scalar_field",
    "compile_spatial_wavefunction_scene",
    "elastic_wave_speeds",
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
