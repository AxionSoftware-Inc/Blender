from spectra.domains.partial_differential_equations.complex_domain import (
    ComplexPDEProblem1D,
    ComplexPDESolution1D,
    ComplexPartialDifferentialEquationsDomain,
    compile_complex_pde_solution_scene,
    complex_second_derivative_1d,
)
from spectra.domains.partial_differential_equations.complex2d import (
    ComplexPDE2DDomain,
    ComplexPDEProblem2D,
    ComplexPDESolution2D,
)
from spectra.domains.partial_differential_equations.domain import (
    BoundaryMode1D,
    PartialDifferentialEquationsDomain,
    ScalarPDEProblem1D,
    ScalarPDESolution1D,
    UniformGrid1D,
    second_derivative_1d,
)
from spectra.domains.partial_differential_equations.domain2d import (
    BoundaryMode2D,
    PartialDifferentialEquations2DDomain,
    ScalarPDEProblem2D,
    ScalarPDESolution2D,
    UniformGrid2D,
    laplacian_2d,
)
from spectra.domains.partial_differential_equations.elliptic2d import (
    EllipticPDE2DDomain,
    PoissonProblem2D,
    PoissonSolution2D,
)
from spectra.domains.partial_differential_equations.field_adapters2d import (
    PDEFieldAdapters2DDomain,
    scalar_field_from_grid_2d,
    time_scalar_field_from_grid_2d,
    time_vector_field_from_grid_2d,
    vector_field_from_grid_2d,
)
from spectra.domains.partial_differential_equations.integrals2d import (
    GridIntegrals2DDomain,
    integrate_scalar_grid_2d,
    integrate_vector_magnitude_squared_grid_2d,
    scalar_l2_norm_grid_2d,
)
from spectra.domains.partial_differential_equations.operators2d import (
    PDEOperators2DDomain,
    curl_grid_2d,
    divergence_grid_2d,
    gradient_grid_2d,
    vector_upwind_advection_grid_2d,
)
from spectra.domains.partial_differential_equations.second_order2d import (
    SecondOrderPDE2DDomain,
    SecondOrderScalarPDEProblem2D,
    SecondOrderScalarPDESolution2D,
)
from spectra.domains.partial_differential_equations.stability2d import (
    ExplicitStability2D,
    Stability2DDomain,
    explicit_stability_for_field_2d,
    explicit_stability_from_samples_2d,
)
from spectra.domains.partial_differential_equations.transport2d import (
    AdvectionDiffusionProblem2D,
    AdvectionDiffusionSolution2D,
    Transport2DDomain,
    upwind_advection_2d,
)
from spectra.domains.partial_differential_equations.visualization import (
    compile_scalar_pde_solution_scene,
)
from spectra.domains.partial_differential_equations.visualization2d import (
    compile_scalar_pde_solution_2d_scene,
)

__all__ = [
    "AdvectionDiffusionProblem2D",
    "AdvectionDiffusionSolution2D",
    "BoundaryMode1D",
    "BoundaryMode2D",
    "ComplexPDE2DDomain",
    "ComplexPDEProblem1D",
    "ComplexPDEProblem2D",
    "ComplexPDESolution1D",
    "ComplexPDESolution2D",
    "ComplexPartialDifferentialEquationsDomain",
    "EllipticPDE2DDomain",
    "ExplicitStability2D",
    "GridIntegrals2DDomain",
    "PDEFieldAdapters2DDomain",
    "PDEOperators2DDomain",
    "PartialDifferentialEquations2DDomain",
    "PartialDifferentialEquationsDomain",
    "PoissonProblem2D",
    "PoissonSolution2D",
    "ScalarPDEProblem1D",
    "ScalarPDEProblem2D",
    "ScalarPDESolution1D",
    "ScalarPDESolution2D",
    "SecondOrderPDE2DDomain",
    "SecondOrderScalarPDEProblem2D",
    "SecondOrderScalarPDESolution2D",
    "Stability2DDomain",
    "Transport2DDomain",
    "UniformGrid1D",
    "UniformGrid2D",
    "compile_complex_pde_solution_scene",
    "compile_scalar_pde_solution_2d_scene",
    "compile_scalar_pde_solution_scene",
    "complex_second_derivative_1d",
    "curl_grid_2d",
    "divergence_grid_2d",
    "explicit_stability_for_field_2d",
    "explicit_stability_from_samples_2d",
    "gradient_grid_2d",
    "integrate_scalar_grid_2d",
    "integrate_vector_magnitude_squared_grid_2d",
    "laplacian_2d",
    "scalar_field_from_grid_2d",
    "scalar_l2_norm_grid_2d",
    "second_derivative_1d",
    "time_scalar_field_from_grid_2d",
    "time_vector_field_from_grid_2d",
    "upwind_advection_2d",
    "vector_field_from_grid_2d",
    "vector_upwind_advection_grid_2d",
]
