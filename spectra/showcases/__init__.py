"""Canonical end-to-end scientific showcase scenes.

Showcases compose existing scientific semantics, visualization compilers, and
presentation policies. They are product/integration examples, not new scientific
domains and must not become alternate solver implementations.
"""

from .maxwell_wave import (
    MaxwellWaveShowcaseConfig,
    build_maxwell_wave_base_scene,
    build_maxwell_wave_scene,
)

__all__ = [
    "MaxwellWaveShowcaseConfig",
    "build_maxwell_wave_base_scene",
    "build_maxwell_wave_scene",
]
