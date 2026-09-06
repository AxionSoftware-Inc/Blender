"""Open the canonical Spectra electrostatic laboratory in Blender.

Run inside Blender from the repository root:

    blender --python examples/blender_electrostatic_lab.py

Scientific construction stays renderer-independent. Blender is only the final
native realization of the already-presented Scene.
"""

from spectra.backends.blender import QuantitativeBlenderBackend
from spectra.showcases import (
    ElectrostaticLabShowcaseConfig,
    build_electrostatic_lab_scene,
)


config = ElectrostaticLabShowcaseConfig()
scene = build_electrostatic_lab_scene(config)
backend = QuantitativeBlenderBackend()
handle = backend.create(scene)

print(
    "Spectra electrostatic laboratory created:",
    f"{config.slice_samples ** 2} potential samples,",
    f"{config.vector_samples ** 2} E vectors,",
    f"{config.field_line_seed_count} field lines,",
    len(scene.primitives),
    "Scene primitives",
)
