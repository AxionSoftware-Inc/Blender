from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.domains.mathematics.fields import (
    RegularGrid3D,
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
