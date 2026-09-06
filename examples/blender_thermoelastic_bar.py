"""Open the canonical Spectra thermoelastic heated-bar showcase in Blender.

Run inside Blender from the repository root:

    blender --python examples/blender_thermoelastic_bar.py

The transient heat solve, thermal strain, and physical elongation are computed
renderer-independently. Blender only realizes the already-composed final-state
Scene; deformation exaggeration is a declared display scale.
"""

from spectra.backends.blender import QuantitativeBlenderBackend
from spectra.showcases import ThermoelasticBarShowcaseConfig, build_thermoelastic_bar_scene


config = ThermoelasticBarShowcaseConfig()
scene = build_thermoelastic_bar_scene(config)
backend = QuantitativeBlenderBackend()
handle = backend.create(scene)

print(
    "Spectra thermoelastic bar created:",
    f"grid={config.x_count}x{config.y_count}x{config.z_count},",
    f"t={config.end_time_s:.3g} s,",
    f"deformation display x{config.deformation_exaggeration:.3g}",
)
