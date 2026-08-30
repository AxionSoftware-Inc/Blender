from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.domains.mathematics import Interval, TimeDependentScalarField3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class HarmonicWave1D:
    """Traveling harmonic wave y(x,t) = A sin(kx - s*omega*t + phase)."""

    amplitude: float
    wavelength: float
    frequency: float
    domain: Interval
    phase: float = 0.0
    propagation_direction: int = 1
    name: str = "harmonic_wave"

    def __post_init__(self) -> None:
        if not math.isfinite(self.amplitude):
            raise ValueError("wave amplitude must be finite")
        if not math.isfinite(self.wavelength) or self.wavelength <= 0.0:
            raise ValueError("wave wavelength must be finite and positive")
        if not math.isfinite(self.frequency) or self.frequency < 0.0:
            raise ValueError("wave frequency must be finite and non-negative")
        if not math.isfinite(self.phase):
            raise ValueError("wave phase must be finite")
        if self.propagation_direction not in (-1, 1):
            raise ValueError("wave propagation_direction must be -1 or 1")

    @property
    def wave_number(self) -> float:
        return 2.0 * math.pi / self.wavelength

    @property
    def angular_frequency(self) -> float:
        return 2.0 * math.pi * self.frequency

    @property
    def phase_velocity(self) -> float:
        return self.wavelength * self.frequency * self.propagation_direction

    def evaluate(self, x: float, time: float) -> float:
        if not self.domain.contains(x):
            raise ValueError(f"x={x} lies outside wave domain")
        phase = (
            self.wave_number * x
            - self.propagation_direction * self.angular_frequency * float(time)
            + self.phase
        )
        return self.amplitude * math.sin(phase)


@dataclass(frozen=True, slots=True)
class WaveSuperposition1D:
    waves: tuple[HarmonicWave1D, ...]
    name: str = "wave_superposition"

    def __post_init__(self) -> None:
        if not self.waves:
            raise ValueError("wave superposition requires at least one wave")
        domain = self.waves[0].domain
        if any(wave.domain != domain for wave in self.waves[1:]):
            raise ValueError("superposed waves must share the same spatial domain")

    @property
    def domain(self) -> Interval:
        return self.waves[0].domain

    def evaluate(self, x: float, time: float) -> float:
        return sum(wave.evaluate(x, time) for wave in self.waves)


WaveLike1D = HarmonicWave1D | WaveSuperposition1D


@dataclass(frozen=True, slots=True)
class WaveProfile1D:
    wave: WaveLike1D
    time: float
    samples: int = 256
    name: str = "wave_profile"

    def __post_init__(self) -> None:
        if not math.isfinite(self.time):
            raise ValueError("wave profile time must be finite")
        if self.samples < 2:
            raise ValueError("wave profile samples must be >= 2")


@dataclass(frozen=True, slots=True)
class WaveAnimation1D:
    wave: WaveLike1D
    start_time: float
    end_time: float
    spatial_samples: int = 256
    temporal_samples: int = 60
    name: str = "wave_animation"

    def __post_init__(self) -> None:
        if not math.isfinite(self.start_time) or not math.isfinite(self.end_time):
            raise ValueError("wave animation times must be finite")
        if self.end_time <= self.start_time:
            raise ValueError("wave animation end_time must be greater than start_time")
        if self.spatial_samples < 2:
            raise ValueError("wave animation spatial_samples must be >= 2")
        if self.temporal_samples < 2:
            raise ValueError("wave animation temporal_samples must be >= 2")

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


def as_time_scalar_field(wave: WaveLike1D) -> TimeDependentScalarField3D:
    """Expose a 1D wave through the general mathematical F(position,time) contract."""

    return TimeDependentScalarField3D(
        evaluator=lambda position, time: wave.evaluate(position.x, time),
        name=getattr(wave, "name", "wave"),
    )


class WavesDomain:
    name = "physics.waves"
    version = "1"
    dependencies = (
        DomainDependency("mathematics.interval"),
        DomainDependency("mathematics.time_scalar_field3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        from spectra.domains.physics.waves_visualization import (
            compile_wave_animation_scene,
            compile_wave_profile_scene,
        )

        registry.register_semantic_type("physics.waves.harmonic1d", HarmonicWave1D)
        registry.register_semantic_type("physics.waves.superposition1d", WaveSuperposition1D)
        registry.register_semantic_type("physics.waves.profile1d", WaveProfile1D)
        registry.register_semantic_type("physics.waves.animation1d", WaveAnimation1D)

        registry.provide("physics.waves.harmonic1d", HarmonicWave1D)
        registry.provide("physics.waves.superposition1d", WaveSuperposition1D)
        registry.provide("physics.waves.as_time_scalar_field", as_time_scalar_field)

        registry.register_visualization(WaveProfile1D, compile_wave_profile_scene)
        registry.register_visualization(WaveAnimation1D, compile_wave_animation_scene)
