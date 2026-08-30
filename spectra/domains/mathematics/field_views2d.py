from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.domains.mathematics.fields import AxisSample
from spectra.domains.mathematics.fields2d import (
    ScalarField2D,
    TimeDependentScalarField2D,
    TimeDependentVectorField2D,
    VectorField2D,
)


@dataclass(frozen=True, slots=True)
class VectorFieldView2D:
    field: VectorField2D
    x: AxisSample
    y: AxisSample
    vector_scale: float = 1.0
    plane_z: float = 0.0
    name: str = "vector_field2d"

    def __post_init__(self) -> None:
        if not math.isfinite(self.vector_scale) or self.vector_scale <= 0.0:
            raise ValueError("2D vector field view scale must be finite and positive")
        if not math.isfinite(self.plane_z):
            raise ValueError("2D vector field plane_z must be finite")
        if not self.name:
            raise ValueError("2D vector field view name cannot be empty")


@dataclass(frozen=True, slots=True)
class TimeVectorFieldAnimation2D:
    field: TimeDependentVectorField2D
    x: AxisSample
    y: AxisSample
    start_time: float
    end_time: float
    temporal_samples: int = 60
    vector_scale: float = 1.0
    plane_z: float = 0.0
    name: str = "time_vector_field2d"

    def __post_init__(self) -> None:
        if not math.isfinite(self.start_time) or not math.isfinite(self.end_time):
            raise ValueError("2D vector animation times must be finite")
        if self.end_time <= self.start_time:
            raise ValueError("2D vector animation end_time must exceed start_time")
        if self.temporal_samples < 2:
            raise ValueError("2D vector animation temporal_samples must be >= 2")
        if not math.isfinite(self.vector_scale) or self.vector_scale <= 0.0:
            raise ValueError("2D vector animation scale must be finite and positive")
        if not math.isfinite(self.plane_z):
            raise ValueError("2D vector animation plane_z must be finite")
        if not self.name:
            raise ValueError("2D vector animation name cannot be empty")

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


@dataclass(frozen=True, slots=True)
class ScalarFieldHeightView2D:
    field: ScalarField2D
    x: AxisSample
    y: AxisSample
    height_scale: float = 1.0
    base_z: float = 0.0
    name: str = "scalar_field2d_surface"

    def __post_init__(self) -> None:
        if self.x.count < 2 or self.y.count < 2:
            raise ValueError("2D scalar surface requires at least 2x2 samples")
        if not math.isfinite(self.height_scale):
            raise ValueError("2D scalar surface height_scale must be finite")
        if not math.isfinite(self.base_z):
            raise ValueError("2D scalar surface base_z must be finite")
        if not self.name:
            raise ValueError("2D scalar surface name cannot be empty")


@dataclass(frozen=True, slots=True)
class TimeScalarFieldHeightAnimation2D:
    field: TimeDependentScalarField2D
    x: AxisSample
    y: AxisSample
    start_time: float
    end_time: float
    temporal_samples: int = 60
    height_scale: float = 1.0
    base_z: float = 0.0
    name: str = "time_scalar_field2d_surface"

    def __post_init__(self) -> None:
        if self.x.count < 2 or self.y.count < 2:
            raise ValueError("2D scalar animation requires at least 2x2 samples")
        if not math.isfinite(self.start_time) or not math.isfinite(self.end_time):
            raise ValueError("2D scalar animation times must be finite")
        if self.end_time <= self.start_time:
            raise ValueError("2D scalar animation end_time must exceed start_time")
        if self.temporal_samples < 2:
            raise ValueError("2D scalar animation temporal_samples must be >= 2")
        if not math.isfinite(self.height_scale):
            raise ValueError("2D scalar animation height_scale must be finite")
        if not math.isfinite(self.base_z):
            raise ValueError("2D scalar animation base_z must be finite")
        if not self.name:
            raise ValueError("2D scalar animation name cannot be empty")

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time
