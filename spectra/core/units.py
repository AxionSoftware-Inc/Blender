from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Dimension:
    """SI base-dimension exponents: L, M, T, I, temperature, amount, luminous intensity."""

    length: int = 0
    mass: int = 0
    time: int = 0
    current: int = 0
    temperature: int = 0
    amount: int = 0
    luminous_intensity: int = 0

    def __mul__(self, other: "Dimension") -> "Dimension":
        return Dimension(
            self.length + other.length,
            self.mass + other.mass,
            self.time + other.time,
            self.current + other.current,
            self.temperature + other.temperature,
            self.amount + other.amount,
            self.luminous_intensity + other.luminous_intensity,
        )

    def __truediv__(self, other: "Dimension") -> "Dimension":
        return Dimension(
            self.length - other.length,
            self.mass - other.mass,
            self.time - other.time,
            self.current - other.current,
            self.temperature - other.temperature,
            self.amount - other.amount,
            self.luminous_intensity - other.luminous_intensity,
        )

    def __pow__(self, exponent: int) -> "Dimension":
        return Dimension(
            self.length * exponent,
            self.mass * exponent,
            self.time * exponent,
            self.current * exponent,
            self.temperature * exponent,
            self.amount * exponent,
            self.luminous_intensity * exponent,
        )


DIMENSIONLESS = Dimension()
LENGTH = Dimension(length=1)
MASS = Dimension(mass=1)
TIME = Dimension(time=1)
CURRENT = Dimension(current=1)
TEMPERATURE = Dimension(temperature=1)
CHARGE = CURRENT * TIME
FORCE = MASS * LENGTH / (TIME ** 2)
ELECTRIC_FIELD = FORCE / CHARGE


@dataclass(frozen=True, slots=True)
class Unit:
    name: str
    symbol: str
    dimension: Dimension = DIMENSIONLESS
    scale_to_si: float = 1.0
    offset_to_si: float = 0.0

    def __post_init__(self) -> None:
        if self.scale_to_si == 0.0:
            raise ValueError("unit scale_to_si cannot be zero")

    def to_si(self, value: float) -> float:
        return float(value) * self.scale_to_si + self.offset_to_si

    def from_si(self, value: float) -> float:
        return (float(value) - self.offset_to_si) / self.scale_to_si

    def convert_value_to(self, value: float, target: "Unit") -> float:
        if self.dimension != target.dimension:
            raise ValueError(f"incompatible dimensions: {self.dimension} vs {target.dimension}")
        return target.from_si(self.to_si(value))


@dataclass(frozen=True, slots=True)
class Quantity:
    value: float
    unit: Unit

    def to(self, target: Unit) -> "Quantity":
        return Quantity(self.unit.convert_value_to(self.value, target), target)

    @property
    def si_value(self) -> float:
        return self.unit.to_si(self.value)


ONE = Unit("dimensionless", "1", DIMENSIONLESS)
METER = Unit("meter", "m", LENGTH)
CENTIMETER = Unit("centimeter", "cm", LENGTH, scale_to_si=0.01)
KILOMETER = Unit("kilometer", "km", LENGTH, scale_to_si=1000.0)
SECOND = Unit("second", "s", TIME)
MILLISECOND = Unit("millisecond", "ms", TIME, scale_to_si=0.001)
KILOGRAM = Unit("kilogram", "kg", MASS)
AMPERE = Unit("ampere", "A", CURRENT)
KELVIN = Unit("kelvin", "K", TEMPERATURE)
COULOMB = Unit("coulomb", "C", CHARGE)
NEWTON = Unit("newton", "N", FORCE)
NEWTON_PER_COULOMB = Unit("newton per coulomb", "N/C", ELECTRIC_FIELD)
