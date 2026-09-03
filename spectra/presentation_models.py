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


class ColorPalette(str, Enum):
    VIRIDIS = "viridis"
    MAGMA = "magma"
    COOLWARM = "coolwarm"
    PHASE = "phase"


class ColorRangeMode(str, Enum):
    DATA = "data"
    FIXED = "fixed"
    SYMMETRIC = "symmetric"


@dataclass(frozen=True, slots=True)
class CameraPolicy:
    mode: CameraMode = CameraMode.FIT_ALL
    projection: str = "perspective"
    padding: float = 0.12
    aspect_ratio: float = 16.0 / 9.0
    fov_y_radians: float = math.radians(50.0)

    def __post_init__(self) -> None:
        if self.projection not in {"perspective", "orthographic"}:
            raise ValueError(f"unknown camera projection: {self.projection}")
        if not math.isfinite(self.padding) or self.padding < 0.0:
            raise ValueError("camera padding must be finite and non-negative")
        if not math.isfinite(self.aspect_ratio) or self.aspect_ratio <= 0.0:
            raise ValueError("camera aspect_ratio must be finite and positive")
        if not 0.0 < self.fov_y_radians < math.pi:
            raise ValueError("camera fov_y_radians must lie within (0, pi)")


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

    def __post_init__(self) -> None:
        if not math.isfinite(self.reveal_duration) or self.reveal_duration <= 0.0:
            raise ValueError("reveal_duration must be finite and positive")
        if not math.isfinite(self.stagger) or self.stagger < 0.0:
            raise ValueError("stagger must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class QualityPolicy:
    level: QualityLevel = QualityLevel.INTERACTIVE


@dataclass(frozen=True, slots=True)
class ColorScalePolicy:
    palette: ColorPalette = ColorPalette.VIRIDIS
    range_mode: ColorRangeMode = ColorRangeMode.DATA
    minimum: float | None = None
    maximum: float | None = None
    center: float = 0.0
    clamp: bool = True
    scalar_attribute_name: str | None = None
    output_attribute_name: str = "display_color"

    def __post_init__(self) -> None:
        if not math.isfinite(self.center):
            raise ValueError("color scale center must be finite")
        if not self.output_attribute_name.strip():
            raise ValueError("color scale output_attribute_name cannot be empty")
        if self.scalar_attribute_name is not None and not self.scalar_attribute_name.strip():
            raise ValueError("scalar_attribute_name cannot be empty")
        if self.range_mode == ColorRangeMode.FIXED:
            if self.minimum is None or self.maximum is None:
                raise ValueError("fixed color scale requires minimum and maximum")
            if not math.isfinite(self.minimum) or not math.isfinite(self.maximum):
                raise ValueError("fixed color scale bounds must be finite")
            if self.maximum <= self.minimum:
                raise ValueError("fixed color scale maximum must exceed minimum")
        elif self.minimum is not None or self.maximum is not None:
            raise ValueError("minimum/maximum are only valid for fixed color scales")


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
    color_scale: ColorScalePolicy | None = None


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
    color_scale: ColorScalePolicy = ColorScalePolicy()


_PRESETS = {"analysis", "publication", "presentation", "cinematic", "dark_lab"}


def resolve_presentation(intent: PresentationIntent | str = PresentationIntent()) -> ResolvedPresentation:
    if isinstance(intent, str):
        intent = PresentationIntent(preset=intent)
    if intent.preset not in _PRESETS:
        raise ValueError(f"unknown presentation preset: {intent.preset}")
    p = intent.preset
    camera = CameraPolicy(
        mode=(
            CameraMode.ORTHOGRAPHIC_ANALYSIS
            if p == "analysis"
            else CameraMode.PERSPECTIVE_CONTEXT
            if p in {"cinematic", "dark_lab"}
            else CameraMode.FIT_ALL
        ),
        projection="orthographic" if p in {"analysis", "publication"} else "perspective",
    )
    legend = LegendPolicy(
        visible=p in {"publication", "presentation", "cinematic", "dark_lab"},
        compact=p == "publication",
    )
    axes = AxesPolicy(visible=p == "analysis")
    annotations = AnnotationPolicy(
        density={
            "analysis": AnnotationDensity.ANALYSIS,
            "publication": AnnotationDensity.MINIMAL,
            "presentation": AnnotationDensity.TEACHING,
            "cinematic": AnnotationDensity.IMPORTANT_ONLY,
            "dark_lab": AnnotationDensity.IMPORTANT_ONLY,
        }[p]
    )
    lighting = LightingPolicy(
        LightingMode.FLAT_ANALYSIS
        if p == "analysis"
        else LightingMode.UNLIT_DATA
        if p == "publication"
        else LightingMode.RIM_EMPHASIS
        if p == "dark_lab"
        else LightingMode.SCIENTIFIC_STUDIO
    )
    animation = AnimationPolicy(
        RevealMode.STAGGERED
        if p in {"presentation", "cinematic", "dark_lab"}
        else RevealMode.NONE
    )
    quality = QualityPolicy(
        {
            "analysis": QualityLevel.INTERACTIVE,
            "publication": QualityLevel.HIGH,
            "presentation": QualityLevel.INTERACTIVE,
            "cinematic": QualityLevel.PREVIEW,
            "dark_lab": QualityLevel.INTERACTIVE,
        }[p]
    )
    color_scale = ColorScalePolicy(
        palette=ColorPalette.MAGMA if p == "dark_lab" else ColorPalette.VIRIDIS
    )
    return ResolvedPresentation(
        p,
        intent.camera or camera,
        intent.legend or legend,
        intent.axes or axes,
        intent.annotations or annotations,
        intent.lighting or lighting,
        intent.animation or animation,
        intent.quality or quality,
        intent.color_scale or color_scale,
    )


__all__ = [name for name in globals() if not name.startswith("_")]
