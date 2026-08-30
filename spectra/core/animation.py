from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Keyframe(Generic[T]):
    time: float
    value: T


@dataclass(frozen=True, slots=True)
class Track(Generic[T]):
    target_id: str
    property_path: str
    keyframes: tuple[Keyframe[T], ...]

    def __post_init__(self) -> None:
        if not self.keyframes:
            raise ValueError("Animation track requires at least one keyframe")
        times = [keyframe.time for keyframe in self.keyframes]
        if times != sorted(times):
            raise ValueError("Animation keyframes must be sorted by time")


@dataclass(frozen=True, slots=True)
class Timeline:
    duration: float = 0.0
    tracks: tuple[Track[object], ...] = ()

    def __post_init__(self) -> None:
        if self.duration < 0.0:
            raise ValueError("Timeline duration cannot be negative")
