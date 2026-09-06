from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.animation import Keyframe, Timeline, Track
from spectra.core.composition import compose_scenes
from spectra.core.primitives import Polyline, TextLabel, VectorGlyph
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.mathematics import AxisSample, RegularGrid3D, TimeVectorFieldAnimation3D
from spectra.domains.mathematics.field_visualization import (
    compile_time_vector_field_animation_scene,
)
from spectra.domains.physics import PlaneElectromagneticWave
from spectra.presentation import compose_presentation
from spectra.presentation_models import (
    AnnotationDensity,
    AnnotationPolicy,
    AnimationPolicy,
    PresentationContext,
    PresentationIntent,
    RevealMode,
)


_ELECTRIC_COLOR = Color(0.20, 0.65, 1.00, 1.0)
_MAGNETIC_COLOR = Color(1.00, 0.35, 0.18, 1.0)
_AXIS_COLOR = Color(0.62, 0.68, 0.78, 0.75)
_PROPAGATION_COLOR = Color(1.00, 0.82, 0.22, 1.0)


@dataclass(frozen=True, slots=True)
class MaxwellWaveShowcaseConfig:
    """Canonical SI Maxwell plane-wave showcase configuration.

    The scientific model always uses SI seconds and the physical wave speed.
    ``playback_duration`` is presentation transport metadata for Blender or other
    clients; it never changes the scientific Scene Timeline.
    """

    wavelength_m: float = 4.0
    electric_amplitude_n_per_c: float = 1.0
    visible_wavelengths: float = 3.0
    scientific_periods: float = 2.0
    spatial_samples: int = 49
    temporal_samples: int = 121
    display_amplitude: float = 1.0
    playback_duration: float = 4.0

    def __post_init__(self) -> None:
        numeric_positive = {
            "wavelength_m": self.wavelength_m,
            "electric_amplitude_n_per_c": self.electric_amplitude_n_per_c,
            "visible_wavelengths": self.visible_wavelengths,
            "scientific_periods": self.scientific_periods,
            "display_amplitude": self.display_amplitude,
            "playback_duration": self.playback_duration,
        }
        for name, value in numeric_positive.items():
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        if self.spatial_samples < 3:
            raise ValueError("spatial_samples must be >= 3")
        if self.temporal_samples < 2:
            raise ValueError("temporal_samples must be >= 2")

    @property
    def wave(self) -> PlaneElectromagneticWave:
        return PlaneElectromagneticWave(
            electric_amplitude=self.electric_amplitude_n_per_c,
            wavelength=self.wavelength_m,
            propagation_direction=Vec3(1.0, 0.0, 0.0),
            polarization=Vec3(0.0, 1.0, 0.0),
            name="showcase.maxwell.wave",
        )

    @property
    def period_seconds(self) -> float:
        return 1.0 / self.wave.frequency

    @property
    def scientific_duration(self) -> float:
        return self.scientific_periods * self.period_seconds

    @property
    def half_extent(self) -> float:
        return 0.5 * self.visible_wavelengths * self.wavelength_m

    @property
    def electric_display_scale(self) -> float:
        return self.display_amplitude / self.electric_amplitude_n_per_c

    @property
    def magnetic_display_scale(self) -> float:
        # B0 = E0 / c, so this displays c*B on the same visual scale as E.
        return self.wave.speed * self.electric_display_scale


def _field_trace_scene(
    config: MaxwellWaveShowcaseConfig,
    *,
    electric: bool,
) -> Scene:
    wave = config.wave
    field = wave.electric_field() if electric else wave.magnetic_field()
    scale = config.electric_display_scale if electric else config.magnetic_display_scale
    primitive_id = (
        "showcase.maxwell.electric.trace"
        if electric
        else "showcase.maxwell.magnetic.trace"
    )
    color = _ELECTRIC_COLOR if electric else _MAGNETIC_COLOR
    axis = AxisSample(-config.half_extent, config.half_extent, config.spatial_samples)
    x_values = axis.values()

    keyframes: list[Keyframe[tuple[Vec3, ...]]] = []
    for index in range(config.temporal_samples):
        scientific_time = (
            config.scientific_duration * index / (config.temporal_samples - 1)
        )
        points: list[Vec3] = []
        for x in x_values:
            value = field.evaluate(Vec3(x, 0.0, 0.0), scientific_time) * scale
            if electric:
                points.append(Vec3(x, value.y, 0.0))
            else:
                points.append(Vec3(x, 0.0, value.z))
        keyframes.append(Keyframe(scientific_time, tuple(points), "linear"))

    return Scene(
        primitives=(
            Polyline(
                id=primitive_id,
                points=keyframes[0].value,
                width=max(config.wavelength_m * 0.012, 0.01),
                color=color,
            ),
        ),
        timeline=Timeline(
            duration=config.scientific_duration,
            tracks=(
                Track(
                    target_id=primitive_id,
                    property_path="points",
                    keyframes=tuple(keyframes),
                    owner="scientific",
                ),
            ),
        ),
    )


def _context_scene(config: MaxwellWaveShowcaseConfig) -> Scene:
    extent = config.half_extent
    label_size = max(config.wavelength_m * 0.10, 0.10)
    propagation_origin = Vec3(-extent, -1.35 * config.display_amplitude, -1.35 * config.display_amplitude)
    propagation_length = min(config.wavelength_m, extent * 0.45)
    return Scene(
        primitives=(
            Polyline(
                id="showcase.maxwell.propagation.axis",
                points=(Vec3(-extent, 0.0, 0.0), Vec3(extent, 0.0, 0.0)),
                width=max(config.wavelength_m * 0.004, 0.004),
                color=_AXIS_COLOR,
            ),
            VectorGlyph(
                id="showcase.maxwell.propagation.direction",
                origin=propagation_origin,
                vector=Vec3(propagation_length, 0.0, 0.0),
                color=_PROPAGATION_COLOR,
            ),
            TextLabel(
                id="showcase.maxwell.label.propagation",
                text="propagation +x",
                position=propagation_origin + Vec3(propagation_length * 1.1, 0.0, 0.0),
                size=label_size,
                color=_PROPAGATION_COLOR,
            ),
            TextLabel(
                id="showcase.maxwell.label.electric",
                text="E  [N/C]",
                position=Vec3(-extent, 1.25 * config.display_amplitude, 0.0),
                size=label_size,
                color=_ELECTRIC_COLOR,
            ),
            TextLabel(
                id="showcase.maxwell.label.magnetic",
                text="B  [T] · displayed as c·B",
                position=Vec3(-extent, 0.0, 1.25 * config.display_amplitude),
                size=label_size,
                color=_MAGNETIC_COLOR,
            ),
        )
    )


def build_maxwell_wave_base_scene(
    config: MaxwellWaveShowcaseConfig | None = None,
) -> Scene:
    """Build the renderer-neutral scientific Maxwell showcase Scene.

    Electric and magnetic arrows use equal *display* amplitudes. The electric
    field remains N/C and the magnetic field remains Tesla; only the visual B
    arrow scale uses ``c*B`` so both orthogonal components are readable together.
    """
    config = config or MaxwellWaveShowcaseConfig()
    wave = config.wave
    grid = RegularGrid3D(
        AxisSample(-config.half_extent, config.half_extent, config.spatial_samples),
        AxisSample(0.0, 0.0, 1),
        AxisSample(0.0, 0.0, 1),
    )

    electric_animation = TimeVectorFieldAnimation3D(
        field=wave.electric_field(),
        grid=grid,
        start_time=0.0,
        end_time=config.scientific_duration,
        temporal_samples=config.temporal_samples,
        vector_scale=config.electric_display_scale,
        name="showcase.maxwell.electric.vectors",
    )
    magnetic_animation = TimeVectorFieldAnimation3D(
        field=wave.magnetic_field(),
        grid=grid,
        start_time=0.0,
        end_time=config.scientific_duration,
        temporal_samples=config.temporal_samples,
        vector_scale=config.magnetic_display_scale,
        name="showcase.maxwell.magnetic.vectors",
    )

    electric_scene = compile_time_vector_field_animation_scene(
        electric_animation,
        color=_ELECTRIC_COLOR,
    )
    magnetic_scene = compile_time_vector_field_animation_scene(
        magnetic_animation,
        color=_MAGNETIC_COLOR,
    )

    return compose_scenes(
        electric_scene,
        magnetic_scene,
        _field_trace_scene(config, electric=True),
        _field_trace_scene(config, electric=False),
        _context_scene(config),
    )


def _format_frequency(value: float) -> str:
    if value >= 1e9:
        return f"{value / 1e9:.3g} GHz"
    if value >= 1e6:
        return f"{value / 1e6:.3g} MHz"
    if value >= 1e3:
        return f"{value / 1e3:.3g} kHz"
    return f"{value:.3g} Hz"


def _format_time(value: float) -> str:
    if value < 1e-9:
        return f"{value * 1e12:.3g} ps"
    if value < 1e-6:
        return f"{value * 1e9:.3g} ns"
    if value < 1e-3:
        return f"{value * 1e6:.3g} μs"
    return f"{value:.3g} s"


def build_maxwell_wave_scene(
    config: MaxwellWaveShowcaseConfig | None = None,
    *,
    preset: str = "cinematic",
) -> Scene:
    """Build the presented flagship Maxwell Scene.

    Presentation reveal is deliberately disabled here. The scientific Timeline
    is nanosecond-scale SI time; presentation transport speed belongs to the
    renderer/client (for Blender, use ``config.playback_duration``). Mixing a
    seconds-long reveal track into the scientific Timeline would corrupt the
    meaning of the time axis.
    """
    config = config or MaxwellWaveShowcaseConfig()
    wave = config.wave
    subtitle = (
        f"λ={config.wavelength_m:g} m · f={_format_frequency(wave.frequency)} · "
        f"T={_format_time(config.period_seconds)} · "
        "E/B arrows normalized for display; B shown as c·B"
    )
    intent = PresentationIntent(
        preset=preset,
        annotations=AnnotationPolicy(
            density=AnnotationDensity.IMPORTANT_ONLY,
            title="Maxwell Electromagnetic Wave",
            subtitle=subtitle,
            show_time=False,
        ),
        animation=AnimationPolicy(reveal=RevealMode.NONE),
    )
    return compose_presentation(
        build_maxwell_wave_base_scene(config),
        intent,
        context=PresentationContext(
            primary_primitive_id="showcase.maxwell.electric.vectors",
        ),
    )


__all__ = [
    "MaxwellWaveShowcaseConfig",
    "build_maxwell_wave_base_scene",
    "build_maxwell_wave_scene",
]
