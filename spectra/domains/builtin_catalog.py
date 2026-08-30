from __future__ import annotations

from spectra.domains.calculus import CalculusDomain
from spectra.domains.catalog import DomainCatalog, DomainDescriptor
from spectra.domains.differential_equations import DifferentialEquationsDomain
from spectra.domains.differential_geometry import DifferentialGeometryDomain, GeodesicsDomain
from spectra.domains.graph_theory import GraphTheoryDomain
from spectra.domains.linear_algebra import LinearAlgebraDomain
from spectra.domains.mathematics import MathematicsDomain
from spectra.domains.partial_differential_equations import (
    ComplexPartialDifferentialEquationsDomain,
    PartialDifferentialEquations2DDomain,
    PartialDifferentialEquationsDomain,
)
from spectra.domains.physics import (
    DiffusionDomain,
    ElectromagnetismDomain,
    MechanicsDomain,
    ParticleSystemsDomain,
    QuantumDomain,
    RelativityDomain,
    SchrodingerDomain,
    SpatialQuantumDomain,
    WavesDomain,
)
from spectra.domains.probability import ContinuousProbabilityDomain, ProbabilityDomain
from spectra.domains.statistics import StatisticsDomain
from spectra.domains.tensor_algebra import TensorAlgebraDomain


def builtin_domain_catalog() -> DomainCatalog:
    """Return a fresh catalog for all currently bundled scientific domains."""

    catalog = DomainCatalog()
    catalog.register_many(
        (
            DomainDescriptor(
                name="mathematics",
                factory=MathematicsDomain,
                provides=(
                    "mathematics.compile_expression",
                    "mathematics.interval",
                    "mathematics.rect_domain2d",
                    "mathematics.real_function1d",
                    "mathematics.function1d",
                    "mathematics.callable_function1d",
                    "mathematics.complex_function1d",
                    "mathematics.function2d",
                    "mathematics.parametric_curve3d",
                    "mathematics.parametric_surface3d",
                    "mathematics.scalar_field3d",
                    "mathematics.vector_field3d",
                    "mathematics.time_scalar_field3d",
                    "mathematics.time_vector_field3d",
                    "mathematics.regular_grid3d",
                    "mathematics.vector_field_view3d",
                    "mathematics.time_vector_field_animation3d",
                    "mathematics.scalar_field_surface_view2d",
                    "mathematics.time_scalar_field_surface_animation2d",
                ),
                tags=("math", "foundation"),
            ),
            DomainDescriptor(
                name="calculus",
                factory=CalculusDomain,
                provides=(
                    "calculus.derivative_at",
                    "calculus.tangent_at",
                    "calculus.integrate",
                    "calculus.gradient_at",
                    "calculus.divergence_at",
                    "calculus.curl_at",
                ),
                tags=("math", "calculus", "vector-calculus"),
            ),
            DomainDescriptor(
                name="linear_algebra",
                factory=LinearAlgebraDomain,
                provides=(
                    "linear_algebra.vector",
                    "linear_algebra.complex_vector",
                    "linear_algebra.matrix",
                    "linear_algebra.complex_matrix",
                    "linear_algebra.inner_product",
                    "linear_algebra.complex_inner_product",
                    "linear_algebra.norm",
                    "linear_algebra.complex_norm",
                    "linear_algebra.normalize",
                    "linear_algebra.normalize_complex",
                    "linear_algebra.matrix_vector_product",
                    "linear_algebra.complex_matrix_vector_product",
                    "linear_algebra.conjugate_transpose",
                    "linear_algebra.is_hermitian",
                    "linear_algebra.complex_quadratic_form",
                    "linear_algebra.complex_identity",
                    "linear_algebra.determinant",
                    "linear_algebra.inverse",
                    "linear_algebra.complex_determinant",
                    "linear_algebra.complex_inverse",
                ),
                tags=("math", "linear-algebra"),
            ),
            DomainDescriptor(
                name="tensor_algebra",
                factory=TensorAlgebraDomain,
                provides=(
                    "tensor.tensor",
                    "tensor.add",
                    "tensor.scale",
                    "tensor.outer_product",
                    "tensor.permute_axes",
                    "tensor.contract",
                    "tensor.trace",
                ),
                tags=("math", "tensor", "foundation"),
            ),
            DomainDescriptor(
                name="differential_geometry",
                factory=DifferentialGeometryDomain,
                provides=(
                    "geometry.metric_tensor_field",
                    "geometry.metric_matrix",
                    "geometry.inverse_metric",
                    "geometry.metric_inner_product",
                    "geometry.lower_index",
                    "geometry.raise_index",
                    "geometry.christoffel_symbols",
                    "geometry.riemann_curvature",
                    "geometry.ricci_tensor",
                    "geometry.scalar_curvature",
                ),
                tags=("math", "geometry", "metric", "curvature"),
            ),
            DomainDescriptor(
                name="differential_geometry.geodesics",
                factory=GeodesicsDomain,
                provides=(
                    "geometry.geodesic_problem",
                    "geometry.solve_geodesic",
                ),
                tags=("math", "geometry", "geodesic", "ode"),
            ),
            DomainDescriptor(
                name="probability",
                factory=ProbabilityDomain,
                provides=(
                    "probability.discrete_distribution",
                    "probability.expectation",
                    "probability.variance",
                ),
                tags=("math", "probability"),
            ),
            DomainDescriptor(
                name="probability.continuous",
                factory=ContinuousProbabilityDomain,
                provides=(
                    "probability.continuous.make_distribution",
                    "probability.continuous.probability_between",
                    "probability.continuous.cdf",
                ),
                tags=("math", "probability", "continuous"),
            ),
            DomainDescriptor(
                name="statistics",
                factory=StatisticsDomain,
                provides=(
                    "statistics.dataset1d",
                    "statistics.mean",
                    "statistics.sample_variance",
                    "statistics.summarize",
                    "statistics.histogram",
                    "statistics.empirical_distribution",
                ),
                tags=("math", "statistics"),
            ),
            DomainDescriptor(
                name="differential_equations",
                factory=DifferentialEquationsDomain,
                provides=("ode.first_order_system", "ode.solve_rk4"),
                tags=("math", "ode", "solver"),
            ),
            DomainDescriptor(
                name="partial_differential_equations",
                factory=PartialDifferentialEquationsDomain,
                provides=(
                    "pde.uniform_grid1d",
                    "pde.second_derivative_1d",
                    "pde.solve_method_of_lines",
                ),
                tags=("math", "pde", "solver"),
            ),
            DomainDescriptor(
                name="partial_differential_equations.2d",
                factory=PartialDifferentialEquations2DDomain,
                provides=(
                    "pde.uniform_grid2d",
                    "pde.laplacian_2d",
                    "pde.solve_method_of_lines_2d",
                ),
                tags=("math", "pde", "2d", "solver"),
            ),
            DomainDescriptor(
                name="partial_differential_equations.complex",
                factory=ComplexPartialDifferentialEquationsDomain,
                provides=(
                    "pde.complex.problem1d",
                    "pde.complex.second_derivative_1d",
                    "pde.complex.solve_method_of_lines",
                ),
                tags=("math", "pde", "complex", "solver"),
            ),
            DomainDescriptor(
                name="graph_theory",
                factory=GraphTheoryDomain,
                provides=(
                    "graph_theory.graph",
                    "graph_theory.neighbors",
                    "graph_theory.shortest_path_unweighted",
                ),
                tags=("math", "discrete", "graph-theory"),
            ),
            DomainDescriptor(
                name="mechanics",
                factory=MechanicsDomain,
                provides=(
                    "physics.mechanics.particle_problem",
                    "physics.mechanics.solve_particle",
                ),
                tags=("physics", "mechanics"),
            ),
            DomainDescriptor(
                name="physics.particles",
                factory=ParticleSystemsDomain,
                provides=(
                    "physics.particles.particle",
                    "physics.particles.solve_system",
                ),
                tags=("physics", "particles", "simulation"),
            ),
            DomainDescriptor(
                name="physics.diffusion",
                factory=DiffusionDomain,
                provides=(
                    "physics.diffusion.problem1d",
                    "physics.diffusion.solve1d",
                ),
                tags=("physics", "diffusion", "pde"),
            ),
            DomainDescriptor(
                name="electromagnetism",
                factory=ElectromagnetismDomain,
                provides=(
                    "physics.electromagnetism.point_charge",
                    "physics.electromagnetism.electric_field_from_point_charges",
                    "physics.electromagnetism.plane_wave",
                ),
                tags=("physics", "electromagnetism", "fields"),
            ),
            DomainDescriptor(
                name="physics.waves",
                factory=WavesDomain,
                provides=(
                    "physics.waves.harmonic1d",
                    "physics.waves.superposition1d",
                    "physics.waves.as_time_scalar_field",
                ),
                tags=("physics", "waves", "fields"),
            ),
            DomainDescriptor(
                name="physics.quantum",
                factory=QuantumDomain,
                provides=(
                    "physics.quantum.make_state",
                    "physics.quantum.measurement_distribution",
                    "physics.quantum.make_observable",
                    "physics.quantum.apply_observable",
                    "physics.quantum.expectation_value",
                ),
                tags=("physics", "quantum"),
            ),
            DomainDescriptor(
                name="physics.quantum.spatial",
                factory=SpatialQuantumDomain,
                provides=(
                    "physics.quantum.spatial.make_wavefunction",
                    "physics.quantum.spatial.normalize",
                    "physics.quantum.spatial.position_distribution",
                    "physics.quantum.spatial.probability_between",
                ),
                tags=("physics", "quantum", "wavefunction", "probability"),
            ),
            DomainDescriptor(
                name="physics.quantum.schrodinger1d",
                factory=SchrodingerDomain,
                provides=(
                    "physics.quantum.schrodinger1d.problem",
                    "physics.quantum.schrodinger1d.solve",
                    "physics.quantum.schrodinger1d.probability_mass",
                ),
                tags=("physics", "quantum", "pde", "schrodinger"),
            ),
            DomainDescriptor(
                name="physics.relativity",
                factory=RelativityDomain,
                provides=(
                    "physics.relativity.event",
                    "physics.relativity.minkowski_metric",
                    "physics.relativity.interval_squared",
                    "physics.relativity.classify_interval",
                    "physics.relativity.proper_time_between",
                    "physics.relativity.lorentz_factor",
                    "physics.relativity.four_velocity",
                ),
                tags=("physics", "relativity", "spacetime", "geometry"),
            ),
        )
    )
    return catalog
