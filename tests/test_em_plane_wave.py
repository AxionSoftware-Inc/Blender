import math

import pytest

from spectra.core.primitives import VectorGlyphSet
from spectra.core.types import Vec3
from spectra.domains import DomainRegistry
from spectra.domains.mathematics import (
    AxisSample,
    MathematicsDomain,
    RegularGrid3D,
    TimeVectorFieldAnimation3D,
)
from spectra.domains.physics import (
    ElectromagnetismDomain,
    PlaneElectromagneticWave,
    SPEED_OF_LIGHT,
)


def test_plane_em_wave_has_perpendicular_e_b_and_propagation() -> None:
    wave = PlaneElectromagneticWave(
        electric_amplitude=100.0,
        wavelength=2.0,
        propagation_direction=Vec3(0.0, 0.0, 2.0),
        polarization=Vec3(3.0, 0.0, 0.0),
    )

    electric = wave.electric_field().evaluate(Vec3(0.0, 0.0, 0.0), 0.0)
    magnetic = wave.magnetic_field().evaluate(Vec3(0.0, 0.0, 0.0), 0.0)

    assert electric == Vec3(100.0, 0.0, 0.0)
    assert magnetic.x == pytest.approx(0.0)
    assert magnetic.y == pytest.approx(100.0 / SPEED_OF_LIGHT)
    assert magnetic.z == pytest.approx(0.0)
    assert electric.dot(wave.propagation_direction) == pytest.approx(0.0)
    assert magnetic.dot(wave.propagation_direction) == pytest.approx(0.0)
    assert electric.dot(magnetic) == pytest.approx(0.0)


def test_plane_em_wave_reuses_generic_dynamic_vector_field_visualization() -> None:
    registry = DomainRegistry()
    registry.add_domains([ElectromagnetismDomain(), MathematicsDomain()])

    wave = PlaneElectromagneticWave(
        electric_amplitude=1.0,
        wavelength=1.0,
        propagation_direction=Vec3(0.0, 0.0, 1.0),
        polarization=Vec3(1.0, 0.0, 0.0),
        speed=1.0,
    )
    grid = RegularGrid3D(
        AxisSample(0.0, 0.0, 1),
        AxisSample(0.0, 0.0, 1),
        AxisSample(0.0, 1.0, 3),
    )
    animation = TimeVectorFieldAnimation3D(
        field=wave.electric_field(),
        grid=grid,
        start_time=0.0,
        end_time=0.25,
        temporal_samples=3,
        name="em-electric-field",
    )
    scene = registry.compile_scene(animation)

    assert len(scene.primitives) == 1
    assert isinstance(scene.primitives[0], VectorGlyphSet)
    assert scene.timeline.tracks[0].property_path == "vectors"

    start = scene.sample(0.0).get("em-electric-field")
    quarter = scene.sample(0.25).get("em-electric-field")
    assert isinstance(start, VectorGlyphSet)
    assert isinstance(quarter, VectorGlyphSet)
    assert start.vectors[0].x == pytest.approx(1.0)
    assert quarter.vectors[0].x == pytest.approx(0.0, abs=1e-10)


def test_plane_em_wave_phase_velocity_matches_configured_speed() -> None:
    wave = PlaneElectromagneticWave(
        electric_amplitude=1.0,
        wavelength=4.0,
        propagation_direction=Vec3(0.0, 0.0, 1.0),
        polarization=Vec3(1.0, 0.0, 0.0),
        speed=2.0,
    )

    assert wave.frequency == pytest.approx(0.5)
    assert wave.angular_frequency == pytest.approx(math.pi)
