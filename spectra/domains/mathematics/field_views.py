from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.domains.mathematics.fields import (
    AxisSample,
    RegularGrid3D,
    ScalarField3D,
    TimeDependentScalarField3D,
    TimeDependentVectorField3D,
    VectorField3D,
)


@dataclass(frozen=True, slots=True)
class VectorFieldView3D:
    field: VectorField3D
    grid: RegularGrid3D
    vector_scale: float = 1.0
    name: str = "vector_field_view"

    def __post_init__(self) -> None:
        if not math.isfinite(self.vector_scale) or self.vector_scale <= 0.0:
            raise ValueError("vector field view scale must be finite and positive")


@dataclass(frozen=True, slots=True)
class TimeVectorFieldAnimation3D:
    field: TimeDependentVectorField3D
    grid: RegularGrid3D
    start_time: float
    end_time: float
    temporal_samples: int = 60
    vector_scale: float = 1.0
    name: str = "time_vector_field"

    def __post_init__(self) -> None:
        if not math.isfinite(self.start_time) or not math.isfinite(self.end_time):
            raise ValueError("vector field animation times must be finite")
        if self.end_time <= self.start_time:
            raise ValueError("vector field animation end_time must be greater than start_time")
        if self.temporal_samples < 2:
            raise ValueError("vector field animation temporal_samples must be >= 2")
        if not math.isfinite(self.vector_scale) or self.vector_scale <= 0.0:
            raise ValueError("vector field animation scale must be finite and positive")

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


@dataclass(frozen=True, slots=True)
class ScalarFieldSurfaceView2D:
    """Sample a scalar field on an XY grid and use value as visual height."""

    field: ScalarField3D
    x: AxisSample
    y: AxisSample
    plane_z: float = 0.0
    height_scale: float = 1.0
    name: str = "scalar_field_surface"

    def __post_init__(self) -> None:
        if self.x.count < 2 or self.y.count < 2:
            raise ValueError("scalar field surface requires at least 2x2 samples")
        if not math.isfinite(self.plane_z):
            raise ValueError("scalar field surface plane_z must be finite")
        if not math.isfinite(self.height_scale):
            raise ValueError("scalar field surface height_scale must be finite")


@dataclass(frozen=True, slots=True)
class TimeScalarFieldSurfaceAnimation2D:
    """Animate F(x,y,z0,t) as a stable-topology Surface vertex track."""

    field: TimeDependentScalarField3D
    x: AxisSample
    y: AxisSample
    start_time: float
    end_time: float
    temporal_samples: int = 60
    plane_z: float = 0.0
    height_scale: float = 1.0
    name: str = "time_scalar_field_surface"

    def __post_init__(self) -> None:
        if self.x.count < 2 or self.y.count < 2:
            raise ValueError("scalar field surface requires at least 2x2 samples")
        if not math.isfinite(self.start_time) or not math.isfinite(self.end_time):
            raise ValueError("scalar field animation times must be finite")
        if self.end_time <= self.start_time:
            raise ValueError("scalar field animation end_time must be greater than start_time")
        if self.temporal_samples < 2:
            raise ValueError("scalar field animation temporal_samples must be >= 2")
        if not math.isfinite(self.plane_z):
            raise ValueError("scalar field surface plane_z must be finite")
        if not math.isfinite(self.height_scale):
            raise ValueError("scalar field surface height_scale must be finite")

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time
