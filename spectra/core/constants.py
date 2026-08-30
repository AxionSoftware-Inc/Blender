from __future__ import annotations

import math

from .units import (
    COULOMB,
    JOULE,
    KELVIN,
    METER,
    METER_PER_SECOND,
    NEWTON,
    SECOND,
    Quantity,
)


# Exact SI-defined constants where applicable.
SPEED_OF_LIGHT = Quantity(299_792_458.0, METER_PER_SECOND)
ELEMENTARY_CHARGE = Quantity(1.602_176_634e-19, COULOMB)
PLANCK_CONSTANT = Quantity(6.626_070_15e-34, JOULE * SECOND)
REDUCED_PLANCK_CONSTANT = PLANCK_CONSTANT / (2.0 * math.pi)
BOLTZMANN_CONSTANT = Quantity(1.380_649e-23, JOULE / KELVIN)

# Reference electromagnetic constant used by the current electrostatics domain.
COULOMB_CONSTANT = Quantity(
    8.987_551_792_3e9,
    NEWTON * (METER ** 2) / (COULOMB ** 2),
)


__all__ = [
    "BOLTZMANN_CONSTANT",
    "COULOMB_CONSTANT",
    "ELEMENTARY_CHARGE",
    "PLANCK_CONSTANT",
    "REDUCED_PLANCK_CONSTANT",
    "SPEED_OF_LIGHT",
]
