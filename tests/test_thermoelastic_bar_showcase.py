from __future__ import annotations

import sys

from spectra.core.primitives import Surface
from spectra.showcases import (
    ThermoelasticBarShowcaseConfig,
    build_thermoelastic_bar_base_scene,
    build_thermoelastic_bar_scene,
)
from spectra.core.units import KELVIN, ONE


def _config() -> ThermoelasticBarShowcaseConfig:
    return ThermoelasticBarShowcaseConfig(
        x_count=5, y_count=3, z_count=3, steps=8, deformation_exaggeration=40.0,
    )


def test_thermoelastic_showcase_composes_existing_capabilities() -> None:
    scene = build_thermoelastic_bar_base_scene(_config())
    surface = scene.get("showcase.thermoelastic.bar.surface")
    assert isinstance(surface, Surface)
    assert scene.timeline.duration == 0.0
    assert surface.attributes.get("temperature").unit == KELVIN
    assert surface.attributes.get("thermal_strain").unit == ONE
    assert len({primitive.id for primitive in scene.primitives}) == len(scene.primitives)
    assert "bpy" not in sys.modules


def test_thermoelastic_display_composition_does_not_mutate_scientific_surface() -> None:
    config = _config()
    base = build_thermoelastic_bar_base_scene(config)
    base_surface = base.get("showcase.thermoelastic.bar.surface")
    presented = build_thermoelastic_bar_scene(config)
    presented_surface = presented.get("showcase.thermoelastic.bar.surface")
    assert presented_surface.attributes.get("temperature").values == base_surface.attributes.get("temperature").values
    assert presented_surface.attributes.get("thermal_strain").values == base_surface.attributes.get("thermal_strain").values
    assert presented.get("presentation.camera.primary").id == "presentation.camera.primary"
    display = presented_surface.attributes.get("display_color")
    assert display.quantity_id == "temperature"
    assert display.values != base_surface.attributes.get("temperature").values
    assert all(
        primitive.id.startswith("presentation.")
        for primitive in presented.primitives
        if primitive.id not in {item.id for item in base.primitives}
    )
