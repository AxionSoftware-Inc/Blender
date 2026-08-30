from spectra.domains.mathematics.domain import MathematicsDomain
from spectra.domains.mathematics.fields import (
    AxisSample,
    RegularGrid3D,
    ScalarField3D,
    TimeDependentScalarField3D,
    TimeDependentVectorField3D,
    VectorField3D,
)
from spectra.domains.mathematics.functions import Function1D, Function2D, Interval, RectDomain2D
from spectra.domains.mathematics.parametric import ParametricCurve3D, ParametricSurface3D

__all__ = [
    "AxisSample",
    "Function1D",
    "Function2D",
    "Interval",
    "MathematicsDomain",
    "ParametricCurve3D",
    "ParametricSurface3D",
    "RectDomain2D",
    "RegularGrid3D",
    "ScalarField3D",
    "TimeDependentScalarField3D",
    "TimeDependentVectorField3D",
    "VectorField3D",
]
