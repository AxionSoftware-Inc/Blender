from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math


class CameraMode(str, Enum):
    FIT_ALL = "fit_all"
    FIT_PRIMARY = "fit_primary"
    ORTHOGRAPHIC_ANALYSIS = "orthographic_analysis"
    PERSPECTIVE_CONTEXT = "perspective_context"


class AnnotationDensity(str, Enum):
    NONE = "none"
    MINIMAL = "minimal"
    ANALYSIS = "analysis"
    TEACHING = "teaching"
    IMPORTANT_ONLY = "important_only"


class LightingMode(str, Enum):
    FLAT_ANALYSIS = "flat_analysis"
    UNLIT_DATA = "unlit_data"
    SCIENTIFIC_STUDIO = "scientific_studio"
    RIM_EMPHASIS = "rim_emphasis"


class QualityLevel(str, Enum):
    INTERACTIVE = "interactive"
    PREVIEW = "preview"
    HIGH = "high"
    FINAL = "final"


class RevealMode(str, Enum):
    NONE = "none"
    STAGGERED = "staggered"


@dataclass(frozen=True, slots=True)
class CameraPolicy:
    mode: CameraMode = CameraMode.FIT_ALL
    projection: str = "perspective"
    padding: float = 0.12
    aspect_ratio: float = 16.0 / 9.0
    fov_y_radians: float = math.radians(50.0)


@dataclass(frozen=True, slots=True)
class LegendPolicy:
    visible: bool = False
    compact: bool = False
    show_units: bool = True
    show_min_max: bool = True


@dataclass(frozen=True, slots=True)
class AxesPolicy:
    visible: bool = False
    grid: bool = False
    equal_scale: bool = True


@dataclass(frozen=True, slots=True)
class AnnotationPolicy:
    density: AnnotationDensity = AnnotationDensity.NONE
    title: str | None = None
    subtitle: str | None = None
    show_time: bool = True
    show_provenance: bool = False


@dataclass(frozen=True, slots=True)
class LightingPolicy:
    mode: LightingMode = LightingMode.FLAT_ANALYSIS


@dataclass(frozen=True, slots=True)
class AnimationPolicy:
    reveal: RevealMode = RevealMode.NONE
    reveal_duration: float = 0.6
    stagger: float = 0.12


@dataclass(frozen=True, slots=True)
class QualityPolicy:
    level: QualityLevel = QualityLevel.INTERACTIVE


@dataclass(frozen=True, slots=True)
class PresentationIntent:
    preset: str = "analysis"
    camera: CameraPolicy | None = None
    legend: LegendPolicy | None = None
    axes: AxesPolicy | None = None
    annotations: AnnotationPolicy | None = None
    lighting: LightingPolicy | None = None
    animation: AnimationPolicy | None = None
    quality: QualityPolicy | None = None


@dataclass(frozen=True, slots=True)
class PresentationContext:
    primary_primitive_id: str | None = None
    title: str | None = None
    subtitle: str | None = None
    quantity_role: str | None = None
    duration: float | None = None


@dataclass(frozen=True, slots=True)
class ResolvedPresentation:
    preset: str
    camera: CameraPolicy
    legend: LegendPolicy
    axes: AxesPolicy
    annotations: AnnotationPolicy
    lighting: LightingPolicy
    animation: AnimationPolicy
    quality: QualityPolicy


_PRESETS = {"analysis", "publication", "presentation", "cinematic", "dark_lab"}


def resolve_presentation(intent: PresentationIntent | str = PresentationIntent()) -> ResolvedPresentation:
    if isinstance(intent, str):
        intent = PresentationIntent(preset=intent)
    if intent.preset not in _PRESETS:
        raise ValueError(f"unknown presentation preset: {intent.preset}")
    p = intent.preset
    camera = CameraPolicy(
        mode=(CameraMode.ORTHOGRAPHIC_ANALYSIS if p == "analysis" else
              CameraMode.PERSPECTIVE_CONTEXT if p in {"cinematic", "dark_lab"} else CameraMode.FIT_ALL),
        projection="orthographic" if p in {"analysis", "publication"} else "perspective",
    )
    legend = LegendPolicy(visible=p in {"publication", "presentation", "cinematic", "dark_lab"}, compact=p == "publication")
    axes = AxesPolicy(visible=p == "analysis")
    annotations = AnnotationPolicy(
        density={"analysis": AnnotationDensity.ANALYSIS, "publication": AnnotationDensity.MINIMAL,
                 "presentation": AnnotationDensity.TEACHING, "cinematic": AnnotationDensity.IMPORTANT_ONLY,
                 "dark_lab": AnnotationDensity.IMPORTANT_ONLY}[p]
    )
    lighting = LightingPolicy(LightingMode.FLAT_ANALYSIS if p == "analysis" else
                              LightingMode.UNLIT_DATA if p == "publication" else
                              LightingMode.RIM_EMPHASIS if p == "dark_lab" else LightingMode.SCIENTIFIC_STUDIO)
    animation = AnimationPolicy(RevealMode.STAGGERED if p in {"presentation", "cinematic", "dark_lab"} else RevealMode.NONE)
    quality = QualityPolicy({"analysis": QualityLevel.INTERACTIVE, "publication": QualityLevel.HIGH,
                             "presentation": QualityLevel.INTERACTIVE, "cinematic": QualityLevel.PREVIEW,
                             "dark_lab": QualityLevel.INTERACTIVE}[p])
    return ResolvedPresentation(
        p, intent.camera or camera, intent.legend or legend, intent.axes or axes,
        intent.annotations or annotations, intent.lighting or lighting,
        intent.animation or animation, intent.quality or quality,
    )


__all__ = [name for name in globals() if not name.startswith("_")]
