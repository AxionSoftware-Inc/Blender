from __future__ import annotations

import math

from .units import (
    COULOMB,
    JOULE,
    KELVIN,
    KILOGRAM,
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

# CODATA/reference constants used by current physics domains.
COULOMB_CONSTANT = Quantity(
    8.987_551_792_3e9,
    NEWTON * (METER ** 2) / (COULOMB ** 2),
)
VACUUM_PERMITTIVITY = Quantity(
    1.0 / (4.0 * math.pi * COULOMB_CONSTANT.si_value),
    (COULOMB ** 2) / (NEWTON * (METER ** 2)),
)
GRAVITATIONAL_CONSTANT = Quantity(
    6.674_30e-11,
    (METER ** 3) / (KILOGRAM * (SECOND ** 2)),
)


__all__ = [
    "BOLTZMANN_CONSTANT",
    "COULOMB_CONSTANT",
    "ELEMENTARY_CHARGE",
    "GRAVITATIONAL_CONSTANT",
    "PLANCK_CONSTANT",
    "REDUCED_PLANCK_CONSTANT",
    "SPEED_OF_LIGHT",
    "VACUUM_PERMITTIVITY",
]
