from spectra.domains.field_dynamics.domain import (
    CurveSolution3D,
    FieldDynamicsDomain,
    IntegralCurveProblem3D,
    PathlineProblem3D,
)
from spectra.domains.field_dynamics.domain2d import (
    CurveSolution2D,
    FieldDynamics2DDomain,
    IntegralCurveProblem2D,
    PathlineProblem2D,
)
from spectra.domains.field_dynamics.visualization import compile_curve_solution_scene
from spectra.domains.field_dynamics.visualization2d import compile_curve_solution_2d_scene

__all__ = [
    "CurveSolution2D",
    "CurveSolution3D",
    "FieldDynamics2DDomain",
    "FieldDynamicsDomain",
    "IntegralCurveProblem2D",
    "IntegralCurveProblem3D",
    "PathlineProblem2D",
    "PathlineProblem3D",
    "compile_curve_solution_2d_scene",
    "compile_curve_solution_scene",
]
