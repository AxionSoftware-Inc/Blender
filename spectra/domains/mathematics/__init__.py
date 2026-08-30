from spectra.domains.mathematics.domain import MathematicsDomain
from spectra.domains.mathematics.field_slices3d import (
    MathematicsFieldSlices3DDomain,
    ScalarFieldSliceSurface3D,
    compile_scalar_field_slice_surface_scene,
)
from spectra.domains.mathematics.field_views import (
    ScalarFieldSurfaceView2D,
    TimeScalarFieldSurfaceAnimation2D,
    TimeVectorFieldAnimation3D,
    VectorFieldView3D,
)
from spectra.domains.mathematics.field_views2d import (
    ScalarFieldHeightView2D,
    TimeScalarFieldHeightAnimation2D,
    TimeVectorFieldAnimation2D,
    VectorFieldView2D,
)
from spectra.domains.mathematics.fields import (
    AxisSample,
    RegularGrid3D,
    ScalarField3D,
    TimeDependentScalarField3D,
    TimeDependentVectorField3D,
    VectorField3D,
)
from spectra.domains.mathematics.fields2d import (
    ScalarField2D,
    TimeDependentScalarField2D,
    TimeDependentVectorField2D,
    VectorField2D,
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
    "MathematicsFieldSlices3DDomain",
    "ParametricCurve3D",
    "ParametricSurface3D",
    "RealFunction1D",
    "RectDomain2D",
    "RegularGrid3D",
    "ScalarField2D",
    "ScalarField3D",
    "ScalarFieldHeightView2D",
    "ScalarFieldSliceSurface3D",
    "ScalarFieldSurfaceView2D",
    "TimeDependentScalarField2D",
    "TimeDependentScalarField3D",
    "TimeDependentVectorField2D",
    "TimeDependentVectorField3D",
    "TimeScalarFieldHeightAnimation2D",
    "TimeScalarFieldSurfaceAnimation2D",
    "TimeVectorFieldAnimation2D",
    "TimeVectorFieldAnimation3D",
    "VectorField2D",
    "VectorField3D",
    "VectorFieldView2D",
    "VectorFieldView3D",
    "compile_scalar_field_slice_surface_scene",
]
