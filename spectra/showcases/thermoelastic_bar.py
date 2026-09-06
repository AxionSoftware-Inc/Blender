from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.attributes import VisualAttribute, VisualAttributeSet
from spectra.core.composition import compose_scenes
from spectra.core.primitives import Polyline, Surface, TextLabel
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.core.units import (
    JOULE_PER_KILOGRAM_KELVIN,
    KELVIN,
    KILOGRAM_PER_CUBIC_METER,
    ONE,
    PASCAL,
    PER_KELVIN,
    WATT_PER_METER_KELVIN,
    Quantity,
)
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid3D
from spectra.domains.physics.elasticity import IsotropicElasticMaterial
from spectra.domains.physics.heat_conduction3d import HeatConductionProblem3D, ThermalMaterial3D
from spectra.domains.physics.thermoelasticity3d import ThermoelasticMaterial3D
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


_OUTLINE_COLOR = Color(0.58, 0.64, 0.72, 0.55)
_LABEL_COLOR = Color(0.94, 0.96, 1.0, 1.0)


@dataclass(frozen=True, slots=True)
class ThermoelasticBarShowcaseConfig:
    """Slender free-heating bar composition over heat + thermoelastic capabilities.

    The heat solve is 3D SI. Final free expansion is interpreted with a declared
    slender-bar approximation: axial strain equals the existing isotropic thermal
    strain capability and is integrated from the anchored left end. Deformation
    can be exaggerated for display without changing the stored temperature or
    strain data.
    """

    length_m: float = 1.0
    width_m: float = 0.15
    height_m: float = 0.15
    x_count: int = 17
    y_count: int = 5
    z_count: int = 5
    reference_temperature_k: float = 293.15
    peak_temperature_rise_k: float = 180.0
    hot_center_x_m: float = -0.32
    hot_width_m: float = 0.11
    end_time_s: float = 60.0
    steps: int = 128
    density_kg_m3: float = 2700.0
    specific_heat_j_kg_k: float = 900.0
    thermal_conductivity_w_m_k: float = 205.0
    young_modulus_pa: float = 69.0e9
    poisson_ratio: float = 0.33
    thermal_expansion_per_k: float = 23.0e-6
    deformation_exaggeration: float = 80.0

    def __post_init__(self) -> None:
        positive = {
            "length_m": self.length_m,
            "width_m": self.width_m,
            "height_m": self.height_m,
            "reference_temperature_k": self.reference_temperature_k,
            "peak_temperature_rise_k": self.peak_temperature_rise_k,
            "hot_width_m": self.hot_width_m,
            "end_time_s": self.end_time_s,
            "density_kg_m3": self.density_kg_m3,
            "specific_heat_j_kg_k": self.specific_heat_j_kg_k,
            "thermal_conductivity_w_m_k": self.thermal_conductivity_w_m_k,
            "young_modulus_pa": self.young_modulus_pa,
            "thermal_expansion_per_k": self.thermal_expansion_per_k,
            "deformation_exaggeration": self.deformation_exaggeration,
        }
        for name, value in positive.items():
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        if self.x_count < 5 or self.y_count < 3 or self.z_count < 3:
            raise ValueError("thermoelastic bar grid counts are too small")
        if self.steps < 1:
            raise ValueError("steps must be >= 1")
        if not -1.0 < self.poisson_ratio < 0.5:
            raise ValueError("poisson_ratio must lie within (-1, 0.5)")
        half_length = 0.5 * self.length_m
        if not -half_length < self.hot_center_x_m < half_length:
            raise ValueError("hot_center_x_m must lie inside the bar")


def _registry() -> DomainRegistry:
    registry = DomainRegistry()
    builtin_domain_catalog().load(
        registry,
        ["physics.heat_conduction.views3d", "physics.thermoelasticity.3d"],
    )
    return registry


def _grid(config: ThermoelasticBarShowcaseConfig) -> UniformGrid3D:
    return UniformGrid3D(
        UniformGrid1D(-0.5 * config.length_m, 0.5 * config.length_m, config.x_count),
        UniformGrid1D(-0.5 * config.width_m, 0.5 * config.width_m, config.y_count),
        UniformGrid1D(-0.5 * config.height_m, 0.5 * config.height_m, config.z_count),
    )


def _thermal_material(config: ThermoelasticBarShowcaseConfig) -> ThermalMaterial3D:
    return ThermalMaterial3D(
        density=Quantity(config.density_kg_m3, KILOGRAM_PER_CUBIC_METER),
        specific_heat=Quantity(config.specific_heat_j_kg_k, JOULE_PER_KILOGRAM_KELVIN),
        thermal_conductivity=Quantity(
            config.thermal_conductivity_w_m_k,
            WATT_PER_METER_KELVIN,
        ),
        name="showcase.thermoelastic.aluminum_like.thermal",
    )


def _thermoelastic_material(config: ThermoelasticBarShowcaseConfig) -> ThermoelasticMaterial3D:
    return ThermoelasticMaterial3D(
        elastic=IsotropicElasticMaterial(
            young_modulus=Quantity(config.young_modulus_pa, PASCAL),
            poisson_ratio=config.poisson_ratio,
            name="showcase.thermoelastic.aluminum_like.elastic",
        ),
        thermal_expansion=Quantity(config.thermal_expansion_per_k, PER_KELVIN),
        reference_temperature=Quantity(config.reference_temperature_k, KELVIN),
        name="showcase.thermoelastic.aluminum_like",
    )


def _initial_temperature(
    config: ThermoelasticBarShowcaseConfig,
    grid: UniformGrid3D,
) -> tuple[float, ...]:
    return tuple(
        config.reference_temperature_k
        + config.peak_temperature_rise_k
        * math.exp(-((x - config.hot_center_x_m) / config.hot_width_m) ** 2)
        for x, _y, _z in grid.coordinates
    )


def solve_thermoelastic_bar_showcase(
    config: ThermoelasticBarShowcaseConfig | None = None,
):
    """Run the canonical transient heat solve; thermoelasticity is derived downstream."""
    config = config or ThermoelasticBarShowcaseConfig()
    registry = _registry()
    grid = _grid(config)
    problem = HeatConductionProblem3D(
        grid=grid,
        initial_temperature=_initial_temperature(config, grid),
        material=_thermal_material(config),
        boundary="zero_gradient",
        name="showcase.thermoelastic.heat",
    )
    return registry.require("physics.heat_conduction.solve3d")(
        problem,
        end_time=config.end_time_s,
        steps=config.steps,
    )


def _thermal_strain_by_x(
    config: ThermoelasticBarShowcaseConfig,
    solution,
    state: tuple[float, ...],
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    registry = _registry()
    thermal_strain = registry.require("physics.thermoelasticity.thermal_strain")
    material = _thermoelastic_material(config)
    x_values = solution.grid.x.coordinates
    y_mid = solution.grid.y.count // 2
    z_mid = solution.grid.z.count // 2
    xy = solution.grid.x.count * solution.grid.y.count
    strains = []
    for x_index, _x in enumerate(x_values):
        index = z_mid * xy + y_mid * solution.grid.x.count + x_index
        sample = thermal_strain(material, state[index])
        strains.append(float(sample.tensor.at(0, 0)))

    displacement = [0.0]
    for index in range(1, len(x_values)):
        dx = x_values[index] - x_values[index - 1]
        displacement.append(
            displacement[-1] + 0.5 * (strains[index - 1] + strains[index]) * dx
        )
    return tuple(strains), tuple(displacement)


def _deformed_position(
    config: ThermoelasticBarShowcaseConfig,
    x: float,
    y: float,
    z: float,
    *,
    strain: float,
    axial_displacement: float,
) -> Vec3:
    exaggeration = config.deformation_exaggeration
    return Vec3(
        x + exaggeration * axial_displacement,
        y * (1.0 + exaggeration * strain),
        z * (1.0 + exaggeration * strain),
    )


def _append_face(
    vertices: list[Vec3],
    triangles: list[tuple[int, int, int]],
    temperatures: list[float],
    strains: list[float],
    samples: tuple[tuple[tuple[float, float, float], float, float, float], ...],
    u_count: int,
    v_count: int,
    config: ThermoelasticBarShowcaseConfig,
) -> None:
    offset = len(vertices)
    for (x, y, z), temperature, strain, displacement in samples:
        vertices.append(
            _deformed_position(
                config,
                x,
                y,
                z,
                strain=strain,
                axial_displacement=displacement,
            )
        )
        temperatures.append(temperature)
        strains.append(strain)
    for v_index in range(v_count - 1):
        for u_index in range(u_count - 1):
            lower_left = offset + v_index * u_count + u_index
            lower_right = lower_left + 1
            upper_left = lower_left + u_count
            upper_right = upper_left + 1
            triangles.append((lower_left, lower_right, upper_right))
            triangles.append((lower_left, upper_right, upper_left))


def _bar_surface(
    config: ThermoelasticBarShowcaseConfig,
    solution,
) -> tuple[Surface, float, float]:
    state = solution.temperature_states[-1]
    x_values = solution.grid.x.coordinates
    y_values = solution.grid.y.coordinates
    z_values = solution.grid.z.coordinates
    temperature_by_coordinate = dict(zip(solution.grid.coordinates, state, strict=True))
    strain_x, displacement_x = _thermal_strain_by_x(config, solution, state)
    strain_by_x = dict(zip(x_values, strain_x, strict=True))
    displacement_by_x = dict(zip(x_values, displacement_x, strict=True))

    vertices: list[Vec3] = []
    triangles: list[tuple[int, int, int]] = []
    temperatures: list[float] = []
    strains: list[float] = []

    def sample(x: float, y: float, z: float):
        return (
            (x, y, z),
            float(temperature_by_coordinate[(x, y, z)]),
            float(strain_by_x[x]),
            float(displacement_by_x[x]),
        )

    for z in (z_values[0], z_values[-1]):
        face = tuple(sample(x, y, z) for y in y_values for x in x_values)
        _append_face(vertices, triangles, temperatures, strains, face, len(x_values), len(y_values), config)
    for y in (y_values[0], y_values[-1]):
        face = tuple(sample(x, y, z) for z in z_values for x in x_values)
        _append_face(vertices, triangles, temperatures, strains, face, len(x_values), len(z_values), config)
    for x in (x_values[0], x_values[-1]):
        face = tuple(sample(x, y, z) for z in z_values for y in y_values)
        _append_face(vertices, triangles, temperatures, strains, face, len(y_values), len(z_values), config)

    attributes = VisualAttributeSet(
        (
            VisualAttribute(
                name="temperature",
                association="vertex",
                kind="scalar",
                values=tuple(temperatures),
                quantity_id="temperature",
                unit=KELVIN,
            ),
            VisualAttribute(
                name="thermal_strain",
                association="vertex",
                kind="scalar",
                values=tuple(strains),
                quantity_id="thermal_strain",
                unit=ONE,
            ),
        )
    )
    return (
        Surface(
            id="showcase.thermoelastic.bar.surface",
            vertices=tuple(vertices),
            triangles=tuple(triangles),
            color=Color(0.85, 0.88, 0.95, 0.95),
            attributes=attributes,
        ),
        displacement_x[-1],
        max(strain_x),
    )


def _undeformed_outline(config: ThermoelasticBarShowcaseConfig) -> Scene:
    x0, x1 = -0.5 * config.length_m, 0.5 * config.length_m
    y0, y1 = -0.5 * config.width_m, 0.5 * config.width_m
    z0, z1 = -0.5 * config.height_m, 0.5 * config.height_m
    corners = {
        "000": Vec3(x0, y0, z0), "001": Vec3(x0, y0, z1),
        "010": Vec3(x0, y1, z0), "011": Vec3(x0, y1, z1),
        "100": Vec3(x1, y0, z0), "101": Vec3(x1, y0, z1),
        "110": Vec3(x1, y1, z0), "111": Vec3(x1, y1, z1),
    }
    edges = (
        ("000", "001"), ("000", "010"), ("001", "011"), ("010", "011"),
        ("100", "101"), ("100", "110"), ("101", "111"), ("110", "111"),
        ("000", "100"), ("001", "101"), ("010", "110"), ("011", "111"),
    )
    return Scene(
        primitives=tuple(
            Polyline(
                id=f"showcase.thermoelastic.outline.{index:02d}",
                points=(corners[left], corners[right]),
                width=0.006,
                color=_OUTLINE_COLOR,
            )
            for index, (left, right) in enumerate(edges)
        )
    )


def build_thermoelastic_bar_base_scene(
    config: ThermoelasticBarShowcaseConfig | None = None,
) -> Scene:
    """Build a static final-temperature/free-expansion renderer-neutral Scene."""
    config = config or ThermoelasticBarShowcaseConfig()
    solution = solve_thermoelastic_bar_showcase(config)
    surface, actual_elongation_m, max_strain = _bar_surface(config, solution)
    labels = Scene(
        primitives=(
            TextLabel(
                id="showcase.thermoelastic.label.model",
                text="slender free bar · heat conduction → thermal strain → free expansion",
                position=Vec3(-0.5 * config.length_m, -0.16, -0.16),
                size=0.045,
                color=_LABEL_COLOR,
            ),
            TextLabel(
                id="showcase.thermoelastic.label.result",
                text=(
                    f"t={solution.times[-1]:.3g} s · actual ΔL={actual_elongation_m * 1e3:.3g} mm · "
                    f"max ε_th={max_strain:.3g} · deformation shown ×{config.deformation_exaggeration:.3g}"
                ),
                position=Vec3(-0.5 * config.length_m, -0.22, -0.16),
                size=0.040,
                color=_LABEL_COLOR,
            ),
        )
    )
    return compose_scenes(
        Scene(primitives=(surface,)),
        _undeformed_outline(config),
        labels,
    )


def build_thermoelastic_bar_scene(
    config: ThermoelasticBarShowcaseConfig | None = None,
    *,
    preset: str = "presentation",
) -> Scene:
    """Build the presented thermoelastic heated-bar flagship Scene."""
    config = config or ThermoelasticBarShowcaseConfig()
    intent = PresentationIntent(
        preset=preset,
        legend=LegendPolicy(visible=True, compact=False, show_units=True, show_min_max=True),
        axes=AxesPolicy(visible=True, grid=False, equal_scale=True),
        annotations=AnnotationPolicy(
            density=AnnotationDensity.TEACHING,
            title="Thermoelastic Solid · Heat → Expansion",
            subtitle=(
                "3D transient heat solve · aluminum-like material · "
                "slender-bar free-expansion interpretation"
            ),
            show_time=False,
        ),
        animation=AnimationPolicy(reveal=RevealMode.NONE),
        color_scale=ColorScalePolicy(
            palette=ColorPalette.MAGMA,
            range_mode=ColorRangeMode.DATA,
            scalar_attribute_name="temperature",
        ),
    )
    return compose_presentation(
        build_thermoelastic_bar_base_scene(config),
        intent,
        context=PresentationContext(
            primary_primitive_id="showcase.thermoelastic.bar.surface",
            quantity_role="temperature",
        ),
    )


__all__ = [
    "ThermoelasticBarShowcaseConfig",
    "solve_thermoelastic_bar_showcase",
    "build_thermoelastic_bar_base_scene",
    "build_thermoelastic_bar_scene",
]
