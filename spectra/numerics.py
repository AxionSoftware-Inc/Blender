from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class NumericalMethodDescriptor:
    """Renderer/domain-neutral description of a numerical method implementation."""

    method_id: str
    family: str
    implementation: str
    order: int | None = None
    adaptive: bool = False
    reference_implementation: bool = True
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.method_id:
            raise ValueError("numerical method_id cannot be empty")
        if not self.family:
            raise ValueError("numerical method family cannot be empty")
        if not self.implementation:
            raise ValueError("numerical method implementation cannot be empty")
        if self.order is not None and self.order < 1:
            raise ValueError("numerical method order must be >= 1")
        if any(not note for note in self.notes):
            raise ValueError("numerical method notes cannot contain empty strings")


@dataclass(frozen=True, slots=True)
class NumericalPipelineDescriptor:
    """Ordered composition of numerical method stages used by a solver capability."""

    pipeline_id: str
    stages: tuple[NumericalMethodDescriptor, ...]
    reference_implementation: bool = True
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.pipeline_id:
            raise ValueError("numerical pipeline_id cannot be empty")
        if not self.stages:
            raise ValueError("numerical pipeline requires at least one stage")
        if any(not note for note in self.notes):
            raise ValueError("numerical pipeline notes cannot contain empty strings")


@dataclass(frozen=True, slots=True)
class NumericalRunRecord:
    method: NumericalMethodDescriptor | NumericalPipelineDescriptor
    start_time: float
    end_time: float
    steps: int
    state_size: int | None = None
    tags: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not math.isfinite(self.start_time) or not math.isfinite(self.end_time):
            raise ValueError("numerical run times must be finite")
        if self.end_time <= self.start_time:
            raise ValueError("numerical run end_time must be greater than start_time")
        if self.steps < 1:
            raise ValueError("numerical run steps must be >= 1")
        if self.state_size is not None and self.state_size < 1:
            raise ValueError("numerical run state_size must be >= 1")
        if any(not key or not value for key, value in self.tags):
            raise ValueError("numerical run tags require non-empty keys and values")

    @property
    def fixed_step_size(self) -> float:
        return (self.end_time - self.start_time) / self.steps


@dataclass(frozen=True, slots=True)
class TrackedNumericalResult(Generic[T]):
    result: T
    run: NumericalRunRecord


def fixed_step_record(
    method: NumericalMethodDescriptor | NumericalPipelineDescriptor,
    *,
    start_time: float,
    end_time: float,
    steps: int,
    state_size: int | None = None,
    tags: tuple[tuple[str, str], ...] = (),
) -> NumericalRunRecord:
    return NumericalRunRecord(
        method=method,
        start_time=float(start_time),
        end_time=float(end_time),
        steps=int(steps),
        state_size=state_size,
        tags=tags,
    )


__all__ = [
    "NumericalMethodDescriptor",
    "NumericalPipelineDescriptor",
    "NumericalRunRecord",
    "TrackedNumericalResult",
    "fixed_step_record",
]
