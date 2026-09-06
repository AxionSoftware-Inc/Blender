"""Open the canonical Spectra quantum probability + phase showcase in Blender.

Run inside Blender from the repository root:

    blender --python examples/blender_quantum_wavepacket.py

The Schrodinger solve and probability/phase semantics are renderer-independent.
Blender only realizes the already-composed static final-state Scene.
"""

from spectra.backends.blender import QuantitativeBlenderBackend
from spectra.showcases import QuantumWavepacketShowcaseConfig, build_quantum_wavepacket_scene


config = QuantumWavepacketShowcaseConfig()
scene = build_quantum_wavepacket_scene(config)
backend = QuantitativeBlenderBackend()
handle = backend.create(scene)

print(
    "Spectra quantum wavepacket created:",
    f"{config.x_count * config.y_count} samples/panel,",
    f"t={config.end_time_s * 1e15:.3g} fs,",
    "probability + cyclic phase",
)
