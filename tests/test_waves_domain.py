import pytest

from spectra.core.primitives import Polyline
from spectra.core.types import Vec3
from spectra.domains import DomainRegistry
from spectra.domains.mathematics import Interval, MathematicsDomain
from spectra.domains.physics import (
    HarmonicWave1D,
    WaveAnimation1D,
    WaveSuperposition1D,
    WavesDomain,
)


def test_wave_domain_reuses_time_dependent_mathematical_field_capability() -> None:
    registry = DomainRegistry()
    registry.add_domains([WavesDomain(), MathematicsDomain()])

    wave = HarmonicWave1D(
        amplitude=2.0,
        wavelength=4.0,
        frequency=0.5,
        domain=Interval(-4.0, 4.0),
    )
    to_field = registry.require("physics.waves.as_time_scalar_field")
    field = to_field(wave)

    assert field.evaluate(Vec3(1.0, 0.0, 0.0), 0.0) == pytest.approx(2.0)
    snapshot = field.at_time(0.5)
    assert snapshot.evaluate(Vec3(1.0, 0.0, 0.0)) == pytest.approx(0.0, abs=1e-10)


def test_counter_propagating_waves_form_standing_wave_pattern() -> None:
    domain = Interval(0.0, 4.0)
    right = HarmonicWave1D(1.0, 4.0, 1.0, domain, propagation_direction=1)
    left = HarmonicWave1D(1.0, 4.0, 1.0, domain, propagation_direction=-1)
    standing = WaveSuperposition1D((right, left))

    assert standing.evaluate(1.0, 0.0) == pytest.approx(2.0)
    assert standing.evaluate(1.0, 0.25) == pytest.approx(0.0, abs=1e-10)


def test_wave_animation_compiles_physical_time_into_scene_timeline() -> None:
    registry = DomainRegistry()
    registry.add_domains([MathematicsDomain(), WavesDomain()])

    wave = HarmonicWave1D(
        amplitude=1.0,
        wavelength=2.0,
        frequency=1.0,
        domain=Interval(0.0, 2.0),
    )
    animation = WaveAnimation1D(
        wave=wave,
        start_time=0.0,
        end_time=0.25,
        spatial_samples=9,
        temporal_samples=3,
        name="traveling-wave",
    )
    scene = registry.compile_scene(animation)

    assert len(scene.primitives) == 1
    assert isinstance(scene.primitives[0], Polyline)
    assert scene.timeline.duration == pytest.approx(0.25)
    assert scene.timeline.tracks[0].property_path == "points"

    start = scene.sample(0.0).get("traveling-wave")
    end = scene.sample(0.25).get("traveling-wave")
    assert isinstance(start, Polyline)
    assert isinstance(end, Polyline)
    assert start.points != end.points
    assert len(start.points) == len(end.points) == 9
