import pytest

from spectra.core.units import (
    CENTIMETER,
    JOULE,
    KILOGRAM,
    METER,
    METER_PER_SECOND,
    NEWTON,
    SECOND,
    Quantity,
)


def test_quantity_addition_converts_compatible_units() -> None:
    total = Quantity(1.0, METER) + Quantity(25.0, CENTIMETER)
    assert total.unit == METER
    assert total.value == pytest.approx(1.25)


def test_quantity_arithmetic_tracks_derived_dimensions() -> None:
    velocity = Quantity(10.0, METER) / Quantity(2.0, SECOND)
    assert velocity.unit.dimension == METER_PER_SECOND.dimension
    assert velocity.si_value == pytest.approx(5.0)

    force = Quantity(2.0, KILOGRAM) * (Quantity(3.0, METER) / (Quantity(1.0, SECOND) ** 2))
    assert force.unit.dimension == NEWTON.dimension
    assert force.si_value == pytest.approx(6.0)

    energy = force * Quantity(4.0, METER)
    assert energy.unit.dimension == JOULE.dimension
    assert energy.si_value == pytest.approx(24.0)


def test_incompatible_quantity_addition_is_rejected() -> None:
    with pytest.raises(ValueError, match="incompatible quantity dimensions"):
        _ = Quantity(1.0, METER) + Quantity(1.0, SECOND)
