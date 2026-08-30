from spectra.domains.mathematics.domain import MathematicsDomain
from spectra.domains.mathematics.field_views import (
    ScalarFieldSurfaceView2D,
    TimeScalarFieldSurfaceAnimation2D,
    TimeVectorFieldAnimation3D,
    VectorFieldView3D,
)
from spectra.domains.mathematics.fields import (
    AxisSample,
    RegularGrid3D,
    ScalarField3D,
    TimeDependentScalarField3D,
    TimeDependentVectorField3D,
    VectorField3D,
)
from spectra.domains.mathematics.functions import (
    CallableFunction1D,
    ComplexFunction1D,
    Function1D,
    Function2D,
    Interval,
    RealFunction1D,
    RectDomain2D,
)
from spectra.domains.mathematics.parametric import ParametricCurve3D, ParametricSurface3D

__all__ = [
    "AxisSample",
    "CallableFunction1D",
    "ComplexFunction1D",
    "Function1D",
    "Function2D",
    "Interval",
    "MathematicsDomain",
    "ParametricCurve3D",
    "ParametricSurface3D",
    "RealFunction1D",
    "RectDomain2D",
    "RegularGrid3D",
    "ScalarField3D",
    "ScalarFieldSurfaceView2D",
    "TimeDependentScalarField3D",
    "TimeDependentVectorField3D",
    "TimeScalarFieldSurfaceAnimation2D",
    "TimeVectorFieldAnimation3D",
    "VectorField3D",
    "VectorFieldView3D",
]
