import pytest

from spectra.core.constants import (
    COULOMB_CONSTANT,
    ELEMENTARY_CHARGE,
    PLANCK_CONSTANT,
    REDUCED_PLANCK_CONSTANT,
    SPEED_OF_LIGHT,
)
from spectra.core.units import (
    ELECTRIC_FIELD,
    ENERGY,
    LENGTH,
    METER,
    NEWTON_PER_COULOMB,
    TIME,
    Quantity,
    VELOCITY,
)


def test_physical_constants_carry_dimensions() -> None:
    assert SPEED_OF_LIGHT.unit.dimension == VELOCITY
    assert ELEMENTARY_CHARGE.value > 0.0
    assert PLANCK_CONSTANT.unit.dimension == ENERGY * TIME
    assert REDUCED_PLANCK_CONSTANT.unit.dimension == PLANCK_CONSTANT.unit.dimension


def test_coulomb_constant_composes_to_electric_field_dimension() -> None:
    field = COULOMB_CONSTANT * ELEMENTARY_CHARGE / (Quantity(1.0, METER) ** 2)
    assert field.unit.dimension == ELECTRIC_FIELD
    assert field.to(NEWTON_PER_COULOMB).value == pytest.approx(field.si_value)
