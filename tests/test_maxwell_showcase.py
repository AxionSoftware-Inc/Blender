import math

import pytest

from spectra.core.primitives import Polyline, TextLabel, VectorGlyphSet
from spectra.core.types import Vec3
from spectra.showcases import (
    MaxwellWaveShowcaseConfig,
    build_maxwell_wave_base_scene,
    build_maxwell_wave_scene,
)


def test_maxwell_showcase_config_keeps_physical_and_display_scales_separate() -> None:
    config = MaxwellWaveShowcaseConfig()
    wave = config.wave

    assert wave.propagation_direction == Vec3(1.0, 0.0, 0.0)
    assert wave.polarization == Vec3(0.0, 1.0, 0.0)
    assert wave.magnetic_direction == Vec3(0.0, 0.0, 1.0)
    assert config.period_seconds == pytest.approx(config.wavelength_m / wave.speed)
    assert config.scientific_duration == pytest.approx(
        config.scientific_periods * config.period_seconds
    )

    electric_display_amplitude = (
        wave.electric_amplitude * config.electric_display_scale
    )
    magnetic_display_amplitude = (
        wave.magnetic_amplitude * config.magnetic_display_scale
    )
    assert electric_display_amplitude == pytest.approx(config.display_amplitude)
    assert magnetic_display_amplitude == pytest.approx(config.display_amplitude)


def test_maxwell_showcase_config_rejects_invalid_sampling_and_scales() -> None:
    with pytest.raises(ValueError, match="wavelength_m"):
        MaxwellWaveShowcaseConfig(wavelength_m=0.0)
    with pytest.raises(ValueError, match="spatial_samples"):
        MaxwellWaveShowcaseConfig(spatial_samples=2)
    with pytest.raises(ValueError, match="temporal_samples"):
        MaxwellWaveShowcaseConfig(temporal_samples=1)
    with pytest.raises(ValueError, match="playback_duration"):
        MaxwellWaveShowcaseConfig(playback_duration=0.0)


def test_maxwell_base_scene_has_orthogonal_batched_fields_and_scientific_time() -> None:
    config = MaxwellWaveShowcaseConfig(spatial_samples=49, temporal_samples=21)
    scene = build_maxwell_wave_base_scene(config)

    electric = scene.get("showcase.maxwell.electric.vectors")
    magnetic = scene.get("showcase.maxwell.magnetic.vectors")
    assert isinstance(electric, VectorGlyphSet)
    assert isinstance(magnetic, VectorGlyphSet)
    assert electric.instance_count == config.spatial_samples
    assert magnetic.instance_count == config.spatial_samples
    assert scene.timeline.duration == pytest.approx(config.scientific_duration)
    assert len(scene.timeline.tracks) == 4
    assert all(track.owner == "scientific" for track in scene.timeline.tracks)

    center_index = config.spatial_samples // 2
    assert electric.origins[center_index] == Vec3(0.0, 0.0, 0.0)
    assert magnetic.origins[center_index] == Vec3(0.0, 0.0, 0.0)
    assert electric.vectors[center_index].x == pytest.approx(0.0)
    assert electric.vectors[center_index].y == pytest.approx(config.display_amplitude)
    assert electric.vectors[center_index].z == pytest.approx(0.0)
    assert magnetic.vectors[center_index].x == pytest.approx(0.0)
    assert magnetic.vectors[center_index].y == pytest.approx(0.0)
    assert magnetic.vectors[center_index].z == pytest.approx(config.display_amplitude)

    assert isinstance(scene.get("showcase.maxwell.electric.trace"), Polyline)
    assert isinstance(scene.get("showcase.maxwell.magnetic.trace"), Polyline)


def test_maxwell_scene_sampling_changes_fields_without_changing_topology() -> None:
    config = MaxwellWaveShowcaseConfig(spatial_samples=25, temporal_samples=33)
    scene = build_maxwell_wave_base_scene(config)
    start = scene.sample(0.0)
    quarter_period = scene.sample(config.period_seconds * 0.25)

    start_e = start.get("showcase.maxwell.electric.vectors")
    quarter_e = quarter_period.get("showcase.maxwell.electric.vectors")
    assert isinstance(start_e, VectorGlyphSet)
    assert isinstance(quarter_e, VectorGlyphSet)
    assert start_e.origins == quarter_e.origins
    assert start_e.instance_count == quarter_e.instance_count
    assert start_e.vectors != quarter_e.vectors

    center_index = config.spatial_samples // 2
    assert abs(quarter_e.vectors[center_index].y) < 1e-9


def test_presented_maxwell_scene_preserves_si_scientific_timeline() -> None:
    config = MaxwellWaveShowcaseConfig(temporal_samples=25)
    scene = build_maxwell_wave_scene(config)

    assert scene.timeline.duration == pytest.approx(config.scientific_duration)
    assert all(track.owner == "scientific" for track in scene.timeline.tracks)
    assert scene.active_camera_id == "presentation.camera.primary"
    title = scene.get("presentation.title.primary")
    subtitle = scene.get("presentation.annotation.subtitle")
    assert isinstance(title, TextLabel)
    assert isinstance(subtitle, TextLabel)
    assert title.text == "Maxwell Electromagnetic Wave"
    assert "c·B" in subtitle.text
    assert "presentation.annotation.time" not in {
        primitive.id for primitive in scene.primitives
    }


def test_maxwell_wave_e_and_b_remain_in_phase_for_canonical_plane_wave() -> None:
    config = MaxwellWaveShowcaseConfig()
    wave = config.wave
    position = Vec3(config.wavelength_m * 0.125, 0.0, 0.0)
    time = config.period_seconds * 0.125
    electric = wave.electric_field().evaluate(position, time)
    magnetic = wave.magnetic_field().evaluate(position, time)

    # At equal x/lambda and t/T fractions the phase is zero.
    assert electric.y == pytest.approx(config.electric_amplitude_n_per_c)
    assert magnetic.z == pytest.approx(wave.magnetic_amplitude)
    assert magnetic.z == pytest.approx(electric.y / wave.speed)
    assert math.isfinite(wave.frequency)
