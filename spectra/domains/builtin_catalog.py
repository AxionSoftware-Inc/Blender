from __future__ import annotations

from spectra.domains.calculus import CalculusDomain, Jacobian3DDomain, VectorCalculus2DDomain
from spectra.domains.catalog import DomainCatalog
from spectra.domains.differential_equations import DifferentialEquationsDomain
from spectra.domains.differential_geometry import DifferentialGeometryDomain, GeodesicsDomain
from spectra.domains.field_dynamics import (
    FieldDynamics2DDomain,
    FieldDynamicsDomain,
    IntegralCurveBundles3DDomain,
)
from spectra.domains.graph_theory import GraphTheoryDomain
from spectra.domains.linear_algebra import LinearAlgebraDomain, SymmetricEigensystemsDomain
from spectra.domains.mathematics import MathematicsDomain, MathematicsFieldSlices3DDomain
from spectra.domains.partial_differential_equations import (
    ComplexPDE2DDomain,
    ComplexPartialDifferentialEquationsDomain,
    EllipticPDE2DDomain,
    EllipticPDE3DDomain,
    GridIntegrals2DDomain,
    PDEFieldAdapters2DDomain,
    PDEFieldAdapters3DDomain,
    PDEOperators2DDomain,
    PDEOperators3DDomain,
    PDESlices3DDomain,
    PDESolutionFields3DDomain,
    PartialDifferentialEquations2DDomain,
    PartialDifferentialEquations3DDomain,
    PartialDifferentialEquationsDomain,
    SecondOrderPDE2DDomain,
    SourceDeposition3DDomain,
    Stability2DDomain,
    Transport2DDomain,
)
from spectra.domains.physics import (
    Diffusion2DDomain,
    Diffusion3DDomain,
    DiffusionDomain,
    ElasticityDomain,
    ElasticityFieldsDomain,
    ElectromagnetismDomain,
    ElectrostaticPotential2DDomain,
    ElectrostaticPotential3DDomain,
    FieldParticleDynamicsDomain,
    FluidDiagnostics2DDomain,
    FluidInvariants2DDomain,
    FluidKinematics2DDomain,
    FluidTransport2DDomain,
    GeneralRelativityDomain,
    GravitationalPotential3DDomain,
    IncompressibleFlow2DDomain,
    IncompressibleFlowViews2DDomain,
    MechanicsDomain,
    ParticleSystemsDomain,
    PotentialEnergyDiagnosticsDomain,
    PotentialSources3DDomain,
    PrincipalStressDomain,
    QuantumDomain,
    RelativityDomain,
    Schrodinger2DDomain,
    SchrodingerDomain,
    SpatialQuantumDomain,
    VorticityStreamfunction2DDomain,
    WaveEquation2DDomain,
    WavesDomain,
)
from spectra.domains.potential_fields import PotentialFields3DDomain, PotentialFieldViews3DDomain
from spectra.domains.probability import ContinuousProbabilityDomain, ProbabilityDomain
from spectra.domains.statistics import StatisticsDomain
from spectra.domains.tensor_algebra import TensorAlgebraDomain
from spectra.domains.tensor_fields import TensorFieldsDomain


BUILTIN_DOMAIN_FACTORIES = (
    MathematicsDomain,
    MathematicsFieldSlices3DDomain,
    CalculusDomain,
    VectorCalculus2DDomain,
    Jacobian3DDomain,
    LinearAlgebraDomain,
    SymmetricEigensystemsDomain,
    TensorAlgebraDomain,
    TensorFieldsDomain,
    DifferentialGeometryDomain,
    GeodesicsDomain,
    ProbabilityDomain,
    ContinuousProbabilityDomain,
    StatisticsDomain,
    DifferentialEquationsDomain,
    FieldDynamicsDomain,
    FieldDynamics2DDomain,
    IntegralCurveBundles3DDomain,
    PartialDifferentialEquationsDomain,
    PartialDifferentialEquations2DDomain,
    PartialDifferentialEquations3DDomain,
    PDEOperators2DDomain,
    PDEOperators3DDomain,
    PDEFieldAdapters2DDomain,
    PDEFieldAdapters3DDomain,
    PDESolutionFields3DDomain,
    SourceDeposition3DDomain,
    GridIntegrals2DDomain,
    Stability2DDomain,
    EllipticPDE2DDomain,
    EllipticPDE3DDomain,
    Transport2DDomain,
    SecondOrderPDE2DDomain,
    ComplexPartialDifferentialEquationsDomain,
    ComplexPDE2DDomain,
    PDESlices3DDomain,
    PotentialFields3DDomain,
    PotentialFieldViews3DDomain,
    GraphTheoryDomain,
    MechanicsDomain,
    FieldParticleDynamicsDomain,
    PotentialEnergyDiagnosticsDomain,
    ParticleSystemsDomain,
    DiffusionDomain,
    Diffusion2DDomain,
    Diffusion3DDomain,
    FluidKinematics2DDomain,
    FluidTransport2DDomain,
    IncompressibleFlow2DDomain,
    IncompressibleFlowViews2DDomain,
    FluidDiagnostics2DDomain,
    FluidInvariants2DDomain,
    VorticityStreamfunction2DDomain,
    ElasticityDomain,
    ElasticityFieldsDomain,
    PrincipalStressDomain,
    ElectromagnetismDomain,
    ElectrostaticPotential2DDomain,
    ElectrostaticPotential3DDomain,
    GravitationalPotential3DDomain,
    PotentialSources3DDomain,
    WavesDomain,
    WaveEquation2DDomain,
    QuantumDomain,
    SpatialQuantumDomain,
    SchrodingerDomain,
    Schrodinger2DDomain,
    RelativityDomain,
    GeneralRelativityDomain,
)


BUILTIN_DOMAIN_TAGS = {
    "mathematics": ("math", "foundation", "fields"),
    "mathematics.field_slices3d": ("math", "fields", "visualization", "3d"),
    "linear_algebra": ("math", "linear-algebra"),
    "tensor_algebra": ("math", "tensor"),
    "tensor_fields": ("math", "tensor", "fields"),
    "differential_geometry": ("math", "geometry"),
    "differential_equations": ("math", "ode", "solver"),
    "field_dynamics.bundles3d": ("math", "fields", "integral-curves", "3d"),
    "partial_differential_equations": ("math", "pde", "solver"),
    "partial_differential_equations.2d": ("math", "pde", "2d"),
    "partial_differential_equations.3d": ("math", "pde", "3d"),
    "partial_differential_equations.solution_fields3d": ("math", "pde", "fields", "3d"),
    "partial_differential_equations.deposition3d": ("math", "pde", "sampling", "particles", "3d"),
    "physics.potential_fields.3d": ("physics", "fields", "potential", "3d"),
    "physics.potential_fields.views3d": ("physics", "fields", "visualization", "3d"),
    "physics.potential_sources.3d": ("physics", "potential", "particles", "3d"),
    "physics.potential_energy": ("physics", "mechanics", "potential", "diagnostics"),
    "physics.field_particles": ("physics", "mechanics", "fields", "particles"),
    "physics.incompressible_flow.2d": ("physics", "fluid", "2d"),
    "physics.elasticity": ("physics", "solid-mechanics", "elasticity"),
    "electromagnetism": ("physics", "electromagnetism"),
    "physics.electrostatic_potential.3d": ("physics", "electromagnetism", "potential", "3d"),
    "physics.gravitational_potential.3d": ("physics", "gravity", "potential", "3d"),
    "physics.quantum": ("physics", "quantum"),
    "physics.relativity": ("physics", "relativity"),
}


def builtin_domain_catalog() -> DomainCatalog:
    """Build bundled provider metadata from the actual registration contracts.

    The private probe registry loads all built-in domains once, records the
    capability ownership produced by each domain's real `register()` method, and
    turns that metadata into the discovery catalog. This intentionally prevents
    runtime `provide()` calls and a second hand-maintained manifest from drifting
    apart as the number of scientific domains grows.
    """

    return DomainCatalog.from_factories(
        BUILTIN_DOMAIN_FACTORIES,
        tags=BUILTIN_DOMAIN_TAGS,
    )
