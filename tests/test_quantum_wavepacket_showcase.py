from __future__ import annotations

import math

import pytest

from spectra.core.primitives import Surface
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.showcases import (
    PROBABILITY_DENSITY_2D,
    RADIAN,
    QuantumWavepacketShowcaseConfig,
    build_quantum_wavepacket_base_scene,
    build_quantum_wavepacket_scene,
    solve_quantum_wavepacket_showcase,
)


def _config() -> QuantumWavepacketShowcaseConfig:
    return QuantumWavepacketShowcaseConfig(
        x_extent_m=4.0e-9,
        y_extent_m=3.0e-9,
        x_count=15,
        y_count=13,
        packet_center_x_m=-1.2e-9,
        packet_sigma_m=0.7e-9,
        wave_number_per_m=2.0e9,
        end_time_s=1.5e-15,
        steps=32,
        display_meters_per_unit=1.0e-9,
        probability_height_units=2.0,
        panel_gap_units=2.0,
    )


def _probability_mass(solution, state) -> float:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.quantum.schrodinger2d"])
    return registry.require("physics.quantum.schrodinger2d.probability_mass")(
        state,
        solution.grid,
    )


def _expectation_x(solution, state) -> float:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.quantum.schrodinger2d"])
    integrate = registry.require("pde.integrate_scalar_grid_2d")
    density = tuple(abs(complex(value)) ** 2 for value in state)
    total = float(integrate(density, solution.grid))
    weighted = tuple(
        x * value
        for (x, _y), value in zip(solution.grid.coordinates, density, strict=True)
    )
    return float(integrate(weighted, solution.grid)) / total


@pytest.fixture(scope="module")
def solution():
    return solve_quantum_wavepacket_showcase(_config())


@pytest.fixture(scope="module")
def base_scene():
    return build_quantum_wavepacket_base_scene(_config())


@pytest.fixture(scope="module")
def presented_scene():
    return build_quantum_wavepacket_scene(_config())


def test_quantum_showcase_uses_real_schrodinger_evolution_and_preserves_probability(solution) -> None:
    assert solution.duration == pytest.approx(_config().end_time_s)
    initial_mass = _probability_mass(solution, solution.states[0])
    final_mass = _probability_mass(solution, solution.states[-1])
    assert initial_mass == pytest.approx(1.0, rel=1e-10)
    assert final_mass == pytest.approx(1.0, rel=5e-3)

    initial_x = _expectation_x(solution, solution.states[0])
    final_x = _expectation_x(solution, solution.states[-1])
    assert final_x > initial_x


def test_quantum_base_scene_preserves_probability_and_phase_semantics(base_scene) -> None:
    probability = base_scene.get("showcase.quantum.probability.surface")
    phase = base_scene.get("showcase.quantum.phase.surface")
    assert isinstance(probability, Surface)
    assert isinstance(phase, Surface)

    density = probability.attributes.get("probability_density")
    assert density.kind == "scalar"
    assert density.association == "vertex"
    assert density.quantity_id == "probability_density"
    assert density.unit == PROBABILITY_DENSITY_2D
    assert len(density.values) == _config().x_count * _config().y_count
    assert min(density.values) >= 0.0
    assert max(density.values) > 0.0

    phase_scalar = phase.attributes.get("phase")
    phase_colors = phase.attributes.get("display_color")
    assert phase_scalar.unit == RADIAN
    assert phase_scalar.quantity_id == "wavefunction_phase"
    assert all(-math.pi <= value <= math.pi for value in phase_scalar.values)
    assert phase_colors.kind == "color"
    assert phase_colors.association == "vertex"
    assert len(set(phase_colors.values)) > 5
    assert any(color.a < 0.2 for color in phase_colors.values)
    assert any(color.a > 0.8 for color in phase_colors.values)

    # The Scene geometry is display-scaled; the scientific solver remains in meters.
    assert max(abs(vertex.x) for vertex in probability.vertices) > 1.0
    assert base_scene.timeline.duration == 0.0
    assert base_scene.timeline.tracks == ()


def test_probability_height_is_display_normalized_not_raw_density(base_scene) -> None:
    probability = base_scene.get("showcase.quantum.probability.surface")
    density = probability.attributes.get("probability_density")
    assert max(vertex.z for vertex in probability.vertices) == pytest.approx(
        _config().probability_height_units
    )
    assert max(density.values) > 1.0e10


def test_presented_quantum_scene_keeps_cyclic_phase_and_adds_probability_legend(presented_scene) -> None:
    probability = presented_scene.get("showcase.quantum.probability.surface")
    phase = presented_scene.get("showcase.quantum.phase.surface")

    probability_colors = probability.attributes.get("display_color")
    phase_colors = phase.attributes.get("display_color")
    assert probability_colors.quantity_id == "probability_density"
    assert phase_colors.quantity_id == "wavefunction_phase"
    assert probability_colors.values != phase_colors.values

    quantity_label = presented_scene.get("presentation.legend.label.quantity").text
    assert quantity_label == "probability_density [m^-2]"
    assert presented_scene.get("presentation.title.primary").text == (
        "Quantum Wavepacket · Probability + Phase"
    )
    assert presented_scene.active_camera_id == "presentation.camera.primary"
    assert presented_scene.get("presentation.axes.world") is not None
    assert presented_scene.timeline.duration == 0.0


def test_quantum_showcase_configuration_rejects_invalid_scales() -> None:
    with pytest.raises(ValueError, match="grid counts"):
        QuantumWavepacketShowcaseConfig(x_count=4)
    with pytest.raises(ValueError, match="packet_center_x_m"):
        QuantumWavepacketShowcaseConfig(packet_center_x_m=10.0e-9)
    with pytest.raises(ValueError, match="phase_alpha_floor_fraction"):
        QuantumWavepacketShowcaseConfig(phase_alpha_floor_fraction=1.0)
