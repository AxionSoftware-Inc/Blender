"""Canonical end-to-end scientific showcase scenes.

Showcases compose existing scientific semantics, visualization compilers, and
presentation policies. They are product/integration examples, not new scientific
domains and must not become alternate solver implementations.
"""

from .black_hole_geodesics import (
    BlackHoleGeodesicShowcaseConfig,
    BlackHoleGeodesicShowcaseResult,
    build_black_hole_geodesic_base_scene,
    build_black_hole_geodesic_scene,
    solve_black_hole_geodesic_showcase,
)
from .electrostatic_lab import (
    ElectrostaticLabShowcaseConfig,
    build_electrostatic_lab_base_scene,
    build_electrostatic_lab_scene,
)
from .maxwell_wave import (
    MaxwellWaveShowcaseConfig,
    build_maxwell_wave_base_scene,
    build_maxwell_wave_scene,
)
from .quantum_wavepacket import (
    PROBABILITY_DENSITY_2D,
    RADIAN,
    QuantumWavepacketShowcaseConfig,
    build_quantum_wavepacket_base_scene,
    build_quantum_wavepacket_scene,
    solve_quantum_wavepacket_showcase,
)
from .thermoelastic_bar import (
    ThermoelasticBarShowcaseConfig,
    build_thermoelastic_bar_base_scene,
    build_thermoelastic_bar_scene,
    solve_thermoelastic_bar_showcase,
)

__all__ = [
    "BlackHoleGeodesicShowcaseConfig",
    "BlackHoleGeodesicShowcaseResult",
    "ElectrostaticLabShowcaseConfig",
    "MaxwellWaveShowcaseConfig",
    "PROBABILITY_DENSITY_2D",
    "QuantumWavepacketShowcaseConfig",
    "RADIAN",
    "ThermoelasticBarShowcaseConfig",
    "build_black_hole_geodesic_base_scene",
    "build_black_hole_geodesic_scene",
    "build_electrostatic_lab_base_scene",
    "build_electrostatic_lab_scene",
    "build_maxwell_wave_base_scene",
    "build_maxwell_wave_scene",
    "build_quantum_wavepacket_base_scene",
    "build_quantum_wavepacket_scene",
    "build_thermoelastic_bar_base_scene",
    "build_thermoelastic_bar_scene",
    "solve_black_hole_geodesic_showcase",
    "solve_quantum_wavepacket_showcase",
    "solve_thermoelastic_bar_showcase",
]
