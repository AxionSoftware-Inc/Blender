from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
import math
from typing import Any, Generic, Literal, TypeVar

from .transforms import Quaternion
from .types import Color, Vec2, Vec3


T = TypeVar("T")
Interpolation = Literal["step", "linear", "smooth"]
_VALID_INTERPOLATIONS = {"step", "linear", "smooth"}


@dataclass(frozen=True, slots=True)
class Keyframe(Generic[T]):
    time: float
    value: T
    interpolation: Interpolation = "linear"

    def __post_init__(self) -> None:
        if not math.isfinite(self.time):
            raise ValueError("Animation keyframe time must be finite")
        if self.interpolation not in _VALID_INTERPOLATIONS:
            raise ValueError(f"unknown animation interpolation: {self.interpolation}")


@dataclass(frozen=True, slots=True)
class Track(Generic[T]):
    target_id: str
    property_path: str
    keyframes: tuple[Keyframe[T], ...]

    def __post_init__(self) -> None:
        if not self.target_id:
            raise ValueError("Animation track target_id cannot be empty")
        if not self.property_path:
            raise ValueError("Animation track property_path cannot be empty")
        if not self.keyframes:
            raise ValueError("Animation track requires at least one keyframe")
        times = [keyframe.time for keyframe in self.keyframes]
        if any(right <= left for left, right in zip(times, times[1:])):
            raise ValueError("Animation keyframe times must be strictly increasing")

    def evaluate(self, time: float) -> T:
        if time <= self.keyframes[0].time:
            return self.keyframes[0].value
        if time >= self.keyframes[-1].time:
            return self.keyframes[-1].value

        for left, right in zip(self.keyframes, self.keyframes[1:]):
            if left.time <= time <= right.time:
                span = right.time - left.time
                progress = (time - left.time) / span
                return interpolate_values(
                    left.value,
                    right.value,
                    progress,
                    interpolation=left.interpolation,
                )
        return self.keyframes[-1].value


@dataclass(frozen=True, slots=True)
class Timeline:
    duration: float = 0.0
    tracks: tuple[Track[object], ...] = ()

    def __post_init__(self) -> None:
        if not math.isfinite(self.duration) or self.duration < 0.0:
            raise ValueError("Timeline duration must be a finite non-negative value")
        seen: set[tuple[str, str]] = set()
        for track in self.tracks:
            key = (track.target_id, track.property_path)
            if key in seen:
                raise ValueError(
                    f"Timeline contains duplicate track for {track.target_id}.{track.property_path}"
                )
            seen.add(key)
            if track.keyframes[0].time < 0.0:
                raise ValueError("Animation keyframes cannot start before time zero")
            if track.keyframes[-1].time > self.duration:
                raise ValueError("Animation keyframe exceeds timeline duration")

    def evaluate(self, time: float) -> dict[tuple[str, str], object]:
        if not math.isfinite(time):
            raise ValueError("Timeline sample time must be finite")
        clamped = min(max(time, 0.0), self.duration)
        return {
            (track.target_id, track.property_path): track.evaluate(clamped)
            for track in self.tracks
        }


def _smoothstep(value: float) -> float:
    return value * value * (3.0 - 2.0 * value)


def _lerp_number(left: float, right: float, progress: float) -> float:
    return left + (right - left) * progress


def _slerp_quaternion(left: Quaternion, right: Quaternion, progress: float) -> Quaternion:
    dot = left.dot(right)
    right_values = (right.w, right.x, right.y, right.z)
    if dot < 0.0:
        dot = -dot
        right_values = tuple(-value for value in right_values)

    if dot > 0.9995:
        return Quaternion(
            _lerp_number(left.w, right_values[0], progress),
            _lerp_number(left.x, right_values[1], progress),
            _lerp_number(left.y, right_values[2], progress),
            _lerp_number(left.z, right_values[3], progress),
        )

    dot = min(max(dot, -1.0), 1.0)
    theta_0 = math.acos(dot)
    sin_theta_0 = math.sin(theta_0)
    theta = theta_0 * progress
    scale_left = math.sin(theta_0 - theta) / sin_theta_0
    scale_right = math.sin(theta) / sin_theta_0
    return Quaternion(
        left.w * scale_left + right_values[0] * scale_right,
        left.x * scale_left + right_values[1] * scale_right,
        left.y * scale_left + right_values[2] * scale_right,
        left.z * scale_left + right_values[3] * scale_right,
    )


def interpolate_values(
    left: T,
    right: T,
    progress: float,
    *,
    interpolation: Interpolation = "linear",
) -> T:
    """Interpolate engine-owned animation values without renderer involvement."""
    if interpolation not in _VALID_INTERPOLATIONS:
        raise ValueError(f"unknown animation interpolation: {interpolation}")
    progress = min(max(float(progress), 0.0), 1.0)
    if interpolation == "step":
        return left if progress < 1.0 else right
    if interpolation == "smooth":
        progress = _smoothstep(progress)

    if isinstance(left, bool) or isinstance(right, bool):
        raise TypeError("boolean animation requires step interpolation")
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return _lerp_number(float(left), float(right), progress)  # type: ignore[return-value]
    if isinstance(left, Vec2) and isinstance(right, Vec2):
        return Vec2(
            _lerp_number(left.x, right.x, progress),
            _lerp_number(left.y, right.y, progress),
        )  # type: ignore[return-value]
    if isinstance(left, Vec3) and isinstance(right, Vec3):
        return Vec3(
            _lerp_number(left.x, right.x, progress),
            _lerp_number(left.y, right.y, progress),
            _lerp_number(left.z, right.z, progress),
        )  # type: ignore[return-value]
    if isinstance(left, Color) and isinstance(right, Color):
        return Color(
            _lerp_number(left.r, right.r, progress),
            _lerp_number(left.g, right.g, progress),
            _lerp_number(left.b, right.b, progress),
            _lerp_number(left.a, right.a, progress),
        )  # type: ignore[return-value]
    if isinstance(left, Quaternion) and isinstance(right, Quaternion):
        return _slerp_quaternion(left, right, progress)  # type: ignore[return-value]
    if type(left) is type(right) and isinstance(left, tuple) and isinstance(right, tuple):
        if len(left) != len(right):
            raise TypeError("tuple animation values must have equal lengths")
        return tuple(
            interpolate_values(a, b, progress, interpolation=interpolation)
            for a, b in zip(left, right, strict=True)
        )  # type: ignore[return-value]
    raise TypeError(
        f"unsupported animation interpolation: {type(left).__qualname__} -> {type(right).__qualname__}"
    )


def get_property_path(value: object, property_path: str) -> object:
    current: object = value
    for segment in property_path.split("."):
        if not segment or not hasattr(current, segment):
            raise ValueError(f"unknown animation property: {property_path}")
        current = getattr(current, segment)
    return current


def property_path_exists(value: object, property_path: str) -> bool:
    try:
        get_property_path(value, property_path)
    except ValueError:
        return False
    return True


def replace_property_path(value: T, property_path: str, replacement: object) -> T:
    """Immutable nested dataclass replacement used by Scene sampling."""
    segments = property_path.split(".")
    if not segments or any(not segment for segment in segments):
        raise ValueError("invalid animation property path")

    def replace_nested(current: object, index: int) -> object:
        if not is_dataclass(current):
            raise ValueError(
                f"animation path enters non-dataclass value at: {'.'.join(segments[:index])}"
            )
        field_names = {item.name for item in fields(current)}
        segment = segments[index]
        if segment not in field_names:
            raise ValueError(f"unknown animation property: {property_path}")
        if index == len(segments) - 1:
            return replace(current, **{segment: replacement})
        child = getattr(current, segment)
        return replace(current, **{segment: replace_nested(child, index + 1)})

    return replace_nested(value, 0)  # type: ignore[return-value]


def fade_track(
    target_id: str,
    *,
    start_time: float,
    end_time: float,
    start_opacity: float = 0.0,
    end_opacity: float = 1.0,
    interpolation: Interpolation = "smooth",
) -> Track[float]:
    return Track(
        target_id=target_id,
        property_path="opacity",
        keyframes=(
            Keyframe(start_time, start_opacity, interpolation),
            Keyframe(end_time, end_opacity),
        ),
    )


def draw_track(
    target_id: str,
    *,
    start_time: float,
    end_time: float,
    interpolation: Interpolation = "smooth",
) -> Track[float]:
    """Animate Polyline trim_end from 0 to 1."""
    return Track(
        target_id=target_id,
        property_path="trim_end",
        keyframes=(
            Keyframe(start_time, 0.0, interpolation),
            Keyframe(end_time, 1.0),
        ),
    )


def move_track(
    target_id: str,
    start: Vec3,
    end: Vec3,
    *,
    start_time: float,
    end_time: float,
    interpolation: Interpolation = "smooth",
) -> Track[Vec3]:
    return Track(
        target_id=target_id,
        property_path="transform.translation",
        keyframes=(
            Keyframe(start_time, start, interpolation),
            Keyframe(end_time, end),
        ),
    )
