from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real


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
        if not isinstance(exponent, int):
            raise TypeError("dimension exponent must be an integer")
        return Dimension(
            self.length * exponent,
            self.mass * exponent,
            self.time * exponent,
            self.current * exponent,
            self.temperature * exponent,
            self.amount * exponent,
            self.luminous_intensity * exponent,
        )

    @property
    def is_dimensionless(self) -> bool:
        return self == DIMENSIONLESS


DIMENSIONLESS = Dimension()
LENGTH = Dimension(length=1)
MASS = Dimension(mass=1)
TIME = Dimension(time=1)
CURRENT = Dimension(current=1)
TEMPERATURE = Dimension(temperature=1)
CHARGE = CURRENT * TIME
CHARGE_DENSITY = CHARGE / (LENGTH ** 3)
CURRENT_DENSITY = CURRENT / (LENGTH ** 2)
VELOCITY = LENGTH / TIME
ACCELERATION = LENGTH / (TIME ** 2)
FREQUENCY = TIME ** -1
FORCE = MASS * ACCELERATION
MOMENTUM = MASS * VELOCITY
ENERGY = FORCE * LENGTH
POWER = ENERGY / TIME
PRESSURE = FORCE / (LENGTH ** 2)
DENSITY = MASS / (LENGTH ** 3)
KINEMATIC_VISCOSITY = (LENGTH ** 2) / TIME
DYNAMIC_VISCOSITY = PRESSURE * TIME
SPECIFIC_HEAT = ENERGY / (MASS * TEMPERATURE)
THERMAL_CONDUCTIVITY = POWER / (LENGTH * TEMPERATURE)
THERMAL_EXPANSION = TEMPERATURE ** -1
TEMPERATURE_RATE = TEMPERATURE / TIME
VOLUMETRIC_POWER = POWER / (LENGTH ** 3)
ELECTRIC_FIELD = FORCE / CHARGE
ELECTRIC_POTENTIAL = ENERGY / CHARGE
MAGNETIC_FIELD = MASS / (CURRENT * (TIME ** 2))


@dataclass(frozen=True, slots=True)
class Unit:
    name: str
    symbol: str
    dimension: Dimension = DIMENSIONLESS
    scale_to_si: float = 1.0
    offset_to_si: float = 0.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("unit name cannot be empty")
        if not self.symbol:
            raise ValueError("unit symbol cannot be empty")
        if not math.isfinite(self.scale_to_si) or self.scale_to_si == 0.0:
            raise ValueError("unit scale_to_si must be finite and non-zero")
        if not math.isfinite(self.offset_to_si):
            raise ValueError("unit offset_to_si must be finite")

    @property
    def is_affine(self) -> bool:
        return self.offset_to_si != 0.0

    def to_si(self, value: float) -> float:
        return float(value) * self.scale_to_si + self.offset_to_si

    def from_si(self, value: float) -> float:
        return (float(value) - self.offset_to_si) / self.scale_to_si

    def convert_value_to(self, value: float, target: "Unit") -> float:
        if self.dimension != target.dimension:
            raise ValueError(f"incompatible dimensions: {self.dimension} vs {target.dimension}")
        return target.from_si(self.to_si(value))

    def _require_multiplicative(self) -> None:
        if self.is_affine:
            raise ValueError("affine units cannot participate in multiplication or division")

    def __mul__(self, other: "Unit") -> "Unit":
        if not isinstance(other, Unit):
            return NotImplemented
        self._require_multiplicative()
        other._require_multiplicative()
        return Unit(
            name=f"{self.name} * {other.name}",
            symbol=f"{self.symbol}*{other.symbol}",
            dimension=self.dimension * other.dimension,
            scale_to_si=self.scale_to_si * other.scale_to_si,
        )

    def __truediv__(self, other: "Unit") -> "Unit":
        if not isinstance(other, Unit):
            return NotImplemented
        self._require_multiplicative()
        other._require_multiplicative()
        return Unit(
            name=f"{self.name} / {other.name}",
            symbol=f"{self.symbol}/{other.symbol}",
            dimension=self.dimension / other.dimension,
            scale_to_si=self.scale_to_si / other.scale_to_si,
        )

    def __pow__(self, exponent: int) -> "Unit":
        if not isinstance(exponent, int):
            raise TypeError("unit exponent must be an integer")
        self._require_multiplicative()
        return Unit(
            name=f"{self.name}^{exponent}",
            symbol=f"{self.symbol}^{exponent}",
            dimension=self.dimension ** exponent,
            scale_to_si=self.scale_to_si ** exponent,
        )


@dataclass(frozen=True, slots=True)
class Quantity:
    value: float
    unit: Unit

    def __post_init__(self) -> None:
        value = float(self.value)
        if not math.isfinite(value):
            raise ValueError("quantity value must be finite")
        object.__setattr__(self, "value", value)

    def to(self, target: Unit) -> "Quantity":
        return Quantity(self.unit.convert_value_to(self.value, target), target)

    @property
    def si_value(self) -> float:
        return self.unit.to_si(self.value)

    def _require_linear_arithmetic(self, other: "Quantity") -> None:
        if self.unit.dimension != other.unit.dimension:
            raise ValueError(
                f"incompatible quantity dimensions: {self.unit.dimension} vs {other.unit.dimension}"
            )
        if self.unit.is_affine or other.unit.is_affine:
            raise ValueError("affine quantities must be converted to a linear unit before arithmetic")

    def __add__(self, other: "Quantity") -> "Quantity":
        if not isinstance(other, Quantity):
            return NotImplemented
        self._require_linear_arithmetic(other)
        return Quantity(self.value + other.to(self.unit).value, self.unit)

    def __sub__(self, other: "Quantity") -> "Quantity":
        if not isinstance(other, Quantity):
            return NotImplemented
        self._require_linear_arithmetic(other)
        return Quantity(self.value - other.to(self.unit).value, self.unit)

    def __mul__(self, other: "Quantity | Real") -> "Quantity":
        if isinstance(other, Quantity):
            return Quantity(self.value * other.value, self.unit * other.unit)
        if isinstance(other, Real):
            return Quantity(self.value * float(other), self.unit)
        return NotImplemented

    def __rmul__(self, other: Real) -> "Quantity":
        return self * other

    def __truediv__(self, other: "Quantity | Real") -> "Quantity":
        if isinstance(other, Quantity):
            return Quantity(self.value / other.value, self.unit / other.unit)
        if isinstance(other, Real):
            return Quantity(self.value / float(other), self.unit)
        return NotImplemented

    def __pow__(self, exponent: int) -> "Quantity":
        if not isinstance(exponent, int):
            raise TypeError("quantity exponent must be an integer")
        return Quantity(self.value ** exponent, self.unit ** exponent)

    def __neg__(self) -> "Quantity":
        return Quantity(-self.value, self.unit)


ONE = Unit("dimensionless", "1", DIMENSIONLESS)
METER = Unit("meter", "m", LENGTH)
CENTIMETER = Unit("centimeter", "cm", LENGTH, scale_to_si=0.01)
KILOMETER = Unit("kilometer", "km", LENGTH, scale_to_si=1000.0)
SECOND = Unit("second", "s", TIME)
MILLISECOND = Unit("millisecond", "ms", TIME, scale_to_si=0.001)
HERTZ = Unit("hertz", "Hz", FREQUENCY)
METER_PER_SECOND = Unit("meter per second", "m/s", VELOCITY)
METER_PER_SECOND_SQUARED = Unit("meter per second squared", "m/s^2", ACCELERATION)
SQUARE_METER_PER_SECOND = Unit("square meter per second", "m^2/s", KINEMATIC_VISCOSITY)
KILOGRAM = Unit("kilogram", "kg", MASS)
KILOGRAM_PER_CUBIC_METER = Unit("kilogram per cubic meter", "kg/m^3", DENSITY)
PASCAL_SECOND = Unit("pascal second", "Pa*s", DYNAMIC_VISCOSITY)
AMPERE = Unit("ampere", "A", CURRENT)
AMPERE_PER_SQUARE_METER = Unit("ampere per square meter", "A/m^2", CURRENT_DENSITY)
KELVIN = Unit("kelvin", "K", TEMPERATURE)
KELVIN_PER_SECOND = Unit("kelvin per second", "K/s", TEMPERATURE_RATE)
PER_KELVIN = Unit("per kelvin", "1/K", THERMAL_EXPANSION)
COULOMB = Unit("coulomb", "C", CHARGE)
COULOMB_PER_CUBIC_METER = Unit("coulomb per cubic meter", "C/m^3", CHARGE_DENSITY)
NEWTON = Unit("newton", "N", FORCE)
JOULE = Unit("joule", "J", ENERGY)
JOULE_PER_KILOGRAM_KELVIN = Unit(
    "joule per kilogram kelvin",
    "J/(kg*K)",
    SPECIFIC_HEAT,
)
WATT = Unit("watt", "W", POWER)
WATT_PER_METER_KELVIN = Unit(
    "watt per meter kelvin",
    "W/(m*K)",
    THERMAL_CONDUCTIVITY,
)
WATT_PER_CUBIC_METER = Unit("watt per cubic meter", "W/m^3", VOLUMETRIC_POWER)
PASCAL = Unit("pascal", "Pa", PRESSURE)
VOLT = Unit("volt", "V", ELECTRIC_POTENTIAL)
NEWTON_PER_COULOMB = Unit("newton per coulomb", "N/C", ELECTRIC_FIELD)
TESLA = Unit("tesla", "T", MAGNETIC_FIELD)
