from __future__ import annotations

from dataclasses import dataclass, replace
import math

from spectra.color_scales import map_scalar_values
from spectra.core.attributes import VisualAttribute, VisualAttributeSet
from spectra.core.composition import compose_scenes
from spectra.core.primitives import Surface, TextLabel
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.core.units import KILOGRAM, METER, Quantity, Unit
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid2D
from spectra.domains.physics import SchrodingerProblem2D
from spectra.presentation import compose_presentation
from spectra.presentation_models import (
    AnnotationDensity,
    AnnotationPolicy,
    AnimationPolicy,
    AxesPolicy,
    ColorPalette,
    ColorRangeMode,
    ColorScalePolicy,
    LegendPolicy,
    PresentationContext,
    PresentationIntent,
    RevealMode,
)


RADIAN = Unit("radian", "rad")
PROBABILITY_DENSITY_2D = METER ** -2
_PANEL_LABEL_COLOR = Color(0.94, 0.96, 1.0, 1.0)


@dataclass(frozen=True, slots=True)
class QuantumWavepacketShowcaseConfig:
    """Free 2D electron wavepacket snapshot in SI scientific coordinates.

    The solver grid is expressed in meters. ``display_meters_per_unit`` maps the
    nanoscale scientific coordinates into renderer-friendly display coordinates;
    it does not change the Schrodinger problem. Probability height is likewise a
    normalized display geometry while the attached scalar data retain m^-2.
    """

    x_extent_m: float = 6.0e-9
    y_extent_m: float = 4.0e-9
    x_count: int = 31
    y_count: int = 25
    electron_mass_kg: float = 9.109_383_7139e-31
    packet_center_x_m: float = -2.0e-9
    packet_sigma_m: float = 0.8e-9
    wave_number_per_m: float = 3.0e9
    end_time_s: float = 6.0e-15
    steps: int = 96
    display_meters_per_unit: float = 1.0e-9
    probability_height_units: float = 2.6
    panel_gap_units: float = 2.5
    phase_alpha_floor_fraction: float = 2.0e-3

    def __post_init__(self) -> None:
        positive = {
            "x_extent_m": self.x_extent_m,
            "y_extent_m": self.y_extent_m,
            "electron_mass_kg": self.electron_mass_kg,
            "packet_sigma_m": self.packet_sigma_m,
            "wave_number_per_m": self.wave_number_per_m,
            "end_time_s": self.end_time_s,
            "display_meters_per_unit": self.display_meters_per_unit,
            "probability_height_units": self.probability_height_units,
            "panel_gap_units": self.panel_gap_units,
            "phase_alpha_floor_fraction": self.phase_alpha_floor_fraction,
        }
        for name, value in positive.items():
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        if self.x_count < 5 or self.y_count < 5:
            raise ValueError("quantum showcase grid counts must be >= 5")
        if self.steps < 1:
            raise ValueError("steps must be >= 1")
        if abs(self.packet_center_x_m) >= self.x_extent_m:
            raise ValueError("packet_center_x_m must lie inside the x extent")
        if self.packet_sigma_m >= min(self.x_extent_m, self.y_extent_m):
            raise ValueError("packet_sigma_m must be smaller than the domain extents")
        if not 0.0 < self.phase_alpha_floor_fraction < 1.0:
            raise ValueError("phase_alpha_floor_fraction must lie within (0, 1)")

    @property
    def scientific_width_m(self) -> float:
        return 2.0 * self.x_extent_m

    @property
    def display_width_units(self) -> float:
        return self.scientific_width_m / self.display_meters_per_unit

    @property
    def probability_panel_offset_x(self) -> float:
        return -0.5 * (self.display_width_units + self.panel_gap_units)

    @property
    def phase_panel_offset_x(self) -> float:
        return 0.5 * (self.display_width_units + self.panel_gap_units)


def _registry() -> DomainRegistry:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.quantum.schrodinger2d"])
    return registry


def _grid(config: QuantumWavepacketShowcaseConfig) -> UniformGrid2D:
    return UniformGrid2D(
        UniformGrid1D(-config.x_extent_m, config.x_extent_m, config.x_count),
        UniformGrid1D(-config.y_extent_m, config.y_extent_m, config.y_count),
    )


def _initial_wavepacket(
    config: QuantumWavepacketShowcaseConfig,
    grid: UniformGrid2D,
) -> tuple[complex, ...]:
    values: list[complex] = []
    for index, (x, y) in enumerate(grid.coordinates):
        x_index = index % grid.x.count
        y_index = index // grid.x.count
        if x_index in {0, grid.x.count - 1} or y_index in {0, grid.y.count - 1}:
            values.append(0.0j)
            continue
        radius_squared = (x - config.packet_center_x_m) ** 2 + y * y
        envelope = math.exp(-radius_squared / (4.0 * config.packet_sigma_m ** 2))
        phase = config.wave_number_per_m * x
        values.append(envelope * complex(math.cos(phase), math.sin(phase)))
    return tuple(values)


def solve_quantum_wavepacket_showcase(
    config: QuantumWavepacketShowcaseConfig | None = None,
):
    """Solve the canonical free wavepacket through the existing Schrodinger domain."""
    config = config or QuantumWavepacketShowcaseConfig()
    registry = _registry()
    grid = _grid(config)
    problem = SchrodingerProblem2D(
        grid=grid,
        initial_values=_initial_wavepacket(config, grid),
        mass=Quantity(config.electron_mass_kg, KILOGRAM),
        boundary="fixed",
        initial_time=0.0,
        name="showcase.quantum.wavepacket",
    )
    return registry.require("physics.quantum.schrodinger2d.solve")(
        problem,
        end_time=config.end_time_s,
        steps=config.steps,
        normalize_initial=True,
    )


def _surface_triangles(x_count: int, y_count: int) -> tuple[tuple[int, int, int], ...]:
    triangles: list[tuple[int, int, int]] = []
    for y_index in range(y_count - 1):
        for x_index in range(x_count - 1):
            lower_left = y_index * x_count + x_index
            lower_right = lower_left + 1
            upper_left = lower_left + x_count
            upper_right = upper_left + 1
            triangles.append((lower_left, lower_right, upper_right))
            triangles.append((lower_left, upper_right, upper_left))
    return tuple(triangles)


def _density_and_phase(state: tuple[complex, ...]) -> tuple[tuple[float, ...], tuple[float, ...]]:
    density = tuple(abs(complex(value)) ** 2 for value in state)
    phase = tuple(math.atan2(complex(value).imag, complex(value).real) for value in state)
    return density, phase


def _probability_surface(
    config: QuantumWavepacketShowcaseConfig,
    solution,
) -> Surface:
    state = solution.states[-1]
    density, _phase = _density_and_phase(state)
    maximum = max(density)
    if maximum <= 0.0 or not math.isfinite(maximum):
        raise ValueError("quantum probability snapshot has invalid peak density")
    vertices = tuple(
        Vec3(
            x / config.display_meters_per_unit + config.probability_panel_offset_x,
            y / config.display_meters_per_unit,
            config.probability_height_units * value / maximum,
        )
        for (x, y), value in zip(solution.grid.coordinates, density, strict=True)
    )
    scalar = VisualAttribute(
        name="probability_density",
        association="vertex",
        kind="scalar",
        values=density,
        quantity_id="probability_density",
        unit=PROBABILITY_DENSITY_2D,
    )
    return Surface(
        id="showcase.quantum.probability.surface",
        vertices=vertices,
        triangles=_surface_triangles(solution.grid.x.count, solution.grid.y.count),
        color=Color(0.35, 0.70, 1.0, 0.96),
        attributes=VisualAttributeSet((scalar,)),
    )


def _phase_surface(
    config: QuantumWavepacketShowcaseConfig,
    solution,
) -> Surface:
    state = solution.states[-1]
    density, phase = _density_and_phase(state)
    maximum_density = max(density)
    if maximum_density <= 0.0:
        raise ValueError("quantum phase snapshot has no supported probability density")

    phase_policy = ColorScalePolicy(
        palette=ColorPalette.PHASE,
        range_mode=ColorRangeMode.FIXED,
        minimum=-math.pi,
        maximum=math.pi,
        scalar_attribute_name="phase",
    )
    base_colors = map_scalar_values(phase, phase_policy)
    floor = maximum_density * config.phase_alpha_floor_fraction
    colors = tuple(
        Color(
            color.r,
            color.g,
            color.b,
            min(max((density_value - floor) / max(maximum_density - floor, floor), 0.0), 1.0) ** 0.35,
        )
        for color, density_value in zip(base_colors, density, strict=True)
    )
    vertices = tuple(
        Vec3(
            x / config.display_meters_per_unit + config.phase_panel_offset_x,
            y / config.display_meters_per_unit,
            0.0,
        )
        for x, y in solution.grid.coordinates
    )
    phase_attribute = VisualAttribute(
        name="phase",
        association="vertex",
        kind="scalar",
        values=phase,
        quantity_id="wavefunction_phase",
        unit=RADIAN,
    )
    display_attribute = VisualAttribute(
        name="display_color",
        association="vertex",
        kind="color",
        values=colors,
        quantity_id="wavefunction_phase",
    )
    return Surface(
        id="showcase.quantum.phase.surface",
        vertices=vertices,
        triangles=_surface_triangles(solution.grid.x.count, solution.grid.y.count),
        color=Color(1.0, 1.0, 1.0, 1.0),
        attributes=VisualAttributeSet((phase_attribute, display_attribute)),
    )


def _expectation_x_m(registry: DomainRegistry, solution, state: tuple[complex, ...]) -> float:
    integrate = registry.require("pde.integrate_scalar_grid_2d")
    density = tuple(abs(complex(value)) ** 2 for value in state)
    probability = float(integrate(density, solution.grid))
    weighted_x = tuple(
        x * value
        for (x, _y), value in zip(solution.grid.coordinates, density, strict=True)
    )
    return float(integrate(weighted_x, solution.grid)) / probability


def _labels_scene(
    config: QuantumWavepacketShowcaseConfig,
    solution,
) -> Scene:
    registry = _registry()
    initial_x = _expectation_x_m(registry, solution, solution.states[0])
    final_x = _expectation_x_m(registry, solution, solution.states[-1])
    y_label = -config.y_extent_m / config.display_meters_per_unit - 1.1
    return Scene(
        primitives=(
            TextLabel(
                id="showcase.quantum.label.probability",
                text="Probability density |ψ|² · height normalized · color carries m⁻²",
                position=Vec3(config.probability_panel_offset_x, y_label, 0.0),
                size=0.45,
                color=_PANEL_LABEL_COLOR,
            ),
            TextLabel(
                id="showcase.quantum.label.phase",
                text="Phase arg(ψ) · cyclic −π…π rad · low-density phase faded",
                position=Vec3(config.phase_panel_offset_x, y_label, 0.0),
                size=0.45,
                color=_PANEL_LABEL_COLOR,
            ),
            TextLabel(
                id="showcase.quantum.label.scale",
                text=(
                    f"display: 1 unit = {config.display_meters_per_unit * 1e9:.3g} nm · "
                    f"t = {solution.times[-1] * 1e15:.3g} fs · "
                    f"⟨x⟩ {initial_x * 1e9:.3g} → {final_x * 1e9:.3g} nm"
                ),
                position=Vec3(0.0, y_label - 0.85, 0.0),
                size=0.40,
                color=_PANEL_LABEL_COLOR,
            ),
        )
    )


def build_quantum_wavepacket_base_scene(
    config: QuantumWavepacketShowcaseConfig | None = None,
) -> Scene:
    """Solve and build a static final-state probability + phase comparison Scene."""
    config = config or QuantumWavepacketShowcaseConfig()
    solution = solve_quantum_wavepacket_showcase(config)
    return compose_scenes(
        Scene(primitives=(_probability_surface(config, solution),)),
        Scene(primitives=(_phase_surface(config, solution),)),
        _labels_scene(config, solution),
    )


def build_quantum_wavepacket_scene(
    config: QuantumWavepacketShowcaseConfig | None = None,
    *,
    preset: str = "presentation",
) -> Scene:
    """Build the presented quantum probability + phase flagship Scene."""
    config = config or QuantumWavepacketShowcaseConfig()
    intent = PresentationIntent(
        preset=preset,
        legend=LegendPolicy(visible=True, compact=False, show_units=True, show_min_max=True),
        axes=AxesPolicy(visible=True, grid=False, equal_scale=True),
        annotations=AnnotationPolicy(
            density=AnnotationDensity.TEACHING,
            title="Quantum Wavepacket · Probability + Phase",
            subtitle=(
                "free 2D electron packet · Schrödinger evolution in SI · "
                "scientific nanometers mapped to display units"
            ),
            show_time=False,
        ),
        animation=AnimationPolicy(reveal=RevealMode.NONE),
        color_scale=ColorScalePolicy(
            palette=ColorPalette.VIRIDIS,
            range_mode=ColorRangeMode.DATA,
            scalar_attribute_name="probability_density",
        ),
    )
    return compose_presentation(
        build_quantum_wavepacket_base_scene(config),
        intent,
        context=PresentationContext(
            primary_primitive_id="showcase.quantum.probability.surface",
            quantity_role="probability_density",
        ),
    )


__all__ = [
    "PROBABILITY_DENSITY_2D",
    "RADIAN",
    "QuantumWavepacketShowcaseConfig",
    "solve_quantum_wavepacket_showcase",
    "build_quantum_wavepacket_base_scene",
    "build_quantum_wavepacket_scene",
]
