from __future__ import annotations

from dataclasses import dataclass, replace
import math

from spectra.core.attributes import VisualAttribute, VisualAttributeSet
from spectra.core.composition import compose_scenes
from spectra.core.primitives import Point, Polyline, Surface, TextLabel, VectorGlyphSet
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.core.units import COULOMB, Quantity, VOLT
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.mathematics import AxisSample, RegularGrid3D
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid3D
from spectra.domains.physics import PointChargeSource3D
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


_POSITIVE_COLOR = Color(1.0, 0.24, 0.16, 1.0)
_NEGATIVE_COLOR = Color(0.20, 0.48, 1.0, 1.0)
_FIELD_COLOR = Color(0.92, 0.96, 1.0, 0.92)
_FIELD_LINE_COLOR = Color(1.0, 0.80, 0.22, 0.95)
_LABEL_COLOR = Color(0.94, 0.96, 1.0, 1.0)


@dataclass(frozen=True, slots=True)
class ElectrostaticLabShowcaseConfig:
    """Canonical dipole electrostatic laboratory configuration.

    Scientific electrostatic quantities remain SI. ``vector_display_scale`` only
    changes arrow geometry in the renderer-neutral view; it never rewrites the
    underlying electric-field values or units.
    """

    extent_m: float = 4.0
    z_extent_m: float = 1.5
    source_offset_m: float = 1.5
    charge_coulombs: float = 1.0e-10
    solver_grid_xy_count: int = 17
    solver_grid_z_count: int = 7
    slice_samples: int = 41
    vector_samples: int = 9
    vector_display_scale: float = 0.18
    field_line_seed_count: int = 12
    field_line_seed_radius_m: float = 0.45
    field_line_parameter_length: float = 7.0
    field_line_steps: int = 96
    max_iterations: int = 5000
    tolerance: float = 1.0e-5

    def __post_init__(self) -> None:
        positive = {
            "extent_m": self.extent_m,
            "z_extent_m": self.z_extent_m,
            "source_offset_m": self.source_offset_m,
            "charge_coulombs": self.charge_coulombs,
            "vector_display_scale": self.vector_display_scale,
            "field_line_seed_radius_m": self.field_line_seed_radius_m,
            "field_line_parameter_length": self.field_line_parameter_length,
            "tolerance": self.tolerance,
        }
        for name, value in positive.items():
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        if self.source_offset_m >= self.extent_m:
            raise ValueError("source_offset_m must lie inside the laboratory extent")
        if self.field_line_seed_radius_m >= self.extent_m - self.source_offset_m:
            raise ValueError("field-line seed radius must stay inside the laboratory extent")
        if self.solver_grid_xy_count < 5 or self.solver_grid_z_count < 5:
            raise ValueError("electrostatic solver grid counts must be >= 5")
        if self.slice_samples < 3:
            raise ValueError("slice_samples must be >= 3")
        if self.vector_samples < 2:
            raise ValueError("vector_samples must be >= 2")
        if self.field_line_seed_count < 4:
            raise ValueError("field_line_seed_count must be >= 4")
        if self.field_line_steps < 4:
            raise ValueError("field_line_steps must be >= 4")
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")

    @property
    def positive_position(self) -> Vec3:
        return Vec3(-self.source_offset_m, 0.0, 0.0)

    @property
    def negative_position(self) -> Vec3:
        return Vec3(self.source_offset_m, 0.0, 0.0)

    @property
    def sources(self) -> tuple[PointChargeSource3D, PointChargeSource3D]:
        magnitude = Quantity(self.charge_coulombs, COULOMB)
        return (
            PointChargeSource3D(self.positive_position, magnitude),
            PointChargeSource3D(
                self.negative_position,
                Quantity(-self.charge_coulombs, COULOMB),
            ),
        )


def _registry() -> DomainRegistry:
    registry = DomainRegistry()
    builtin_domain_catalog().load(
        registry,
        [
            "physics.potential_sources.3d",
            "physics.potential_fields.views3d",
        ],
    )
    return registry


def _solver_grid(config: ElectrostaticLabShowcaseConfig) -> UniformGrid3D:
    return UniformGrid3D(
        UniformGrid1D(-config.extent_m, config.extent_m, config.solver_grid_xy_count),
        UniformGrid1D(-config.extent_m, config.extent_m, config.solver_grid_xy_count),
        UniformGrid1D(-config.z_extent_m, config.z_extent_m, config.solver_grid_z_count),
    )


def _solve_potential_model(
    config: ElectrostaticLabShowcaseConfig,
    registry: DomainRegistry,
):
    grid = _solver_grid(config)
    problem = registry.require("physics.potential_sources.electrostatic_problem3d")(
        grid,
        config.sources,
        boundary="fixed",
        name="showcase.electrostatic.dipole",
    )
    solution = registry.require("physics.electrostatic_potential.solve3d")(
        problem,
        max_iterations=config.max_iterations,
        tolerance=config.tolerance,
    )
    if not solution.converged:
        raise RuntimeError(
            "canonical electrostatic showcase did not converge: "
            f"residual_inf={solution.residual_inf:.6g}, tolerance={config.tolerance:.6g}"
        )
    model = registry.require("physics.electrostatic_potential.potential_field3d")(solution)
    return solution, model


def _potential_slice_scene(
    config: ElectrostaticLabShowcaseConfig,
    registry: DomainRegistry,
    model,
) -> Scene:
    u = AxisSample(-config.extent_m, config.extent_m, config.slice_samples)
    v = AxisSample(-config.extent_m, config.extent_m, config.slice_samples)
    view = registry.require("physics.potential_fields.scalar_slice3d")(
        model,
        axis="z",
        coordinate=0.0,
        u=u,
        v=v,
        height_scale=0.0,
        name="showcase.electrostatic.potential.slice",
    )
    scene = registry.compile_scene(view)
    surface = scene.get(view.name)
    if not isinstance(surface, Surface):
        raise TypeError("electrostatic potential slice did not compile to Surface")

    values = tuple(
        model.potential.evaluate(Vec3(x, y, 0.0))
        for y in v.values()
        for x in u.values()
    )
    potential = VisualAttribute(
        name="electric_potential",
        association="vertex",
        kind="scalar",
        values=values,
        quantity_id="electric_potential",
        unit=VOLT,
    )
    colored = replace(
        surface,
        opacity=0.82,
        attributes=VisualAttributeSet((potential,)),
    )
    return replace(scene, primitives=(colored,))


def _vector_scene(
    config: ElectrostaticLabShowcaseConfig,
    registry: DomainRegistry,
    model,
) -> Scene:
    margin = max(config.field_line_seed_radius_m, config.extent_m * 0.10)
    extent = config.extent_m - margin
    view_grid = RegularGrid3D(
        AxisSample(-extent, extent, config.vector_samples),
        AxisSample(-extent, extent, config.vector_samples),
        AxisSample(0.0, 0.0, 1),
    )
    view = registry.require("physics.potential_fields.vector_view3d")(
        model,
        view_grid,
        vector_scale=config.vector_display_scale,
        name="showcase.electrostatic.field.vectors",
    )
    scene = registry.compile_scene(view)
    glyphs = scene.get(view.name)
    if not isinstance(glyphs, VectorGlyphSet):
        raise TypeError("electrostatic vector view did not compile to VectorGlyphSet")
    return replace(scene, primitives=(replace(glyphs, color=_FIELD_COLOR),))


def _field_line_seeds(config: ElectrostaticLabShowcaseConfig) -> tuple[Vec3, ...]:
    center = config.positive_position
    return tuple(
        center
        + Vec3(
            config.field_line_seed_radius_m * math.cos(2.0 * math.pi * index / config.field_line_seed_count),
            config.field_line_seed_radius_m * math.sin(2.0 * math.pi * index / config.field_line_seed_count),
            0.0,
        )
        for index in range(config.field_line_seed_count)
    )


def _field_lines_scene(
    config: ElectrostaticLabShowcaseConfig,
    registry: DomainRegistry,
    model,
) -> Scene:
    problem = registry.require("physics.potential_fields.field_lines3d")(
        model,
        _field_line_seeds(config),
        parameter_length=config.field_line_parameter_length,
        steps_per_direction=config.field_line_steps,
        mode="normalized",
        bidirectional=False,
        name="showcase.electrostatic.field_lines",
    )
    solution = registry.require("field_dynamics.solve_integral_curve_bundle3d")(problem)
    scene = registry.compile_scene(solution)
    primitives = tuple(
        replace(primitive, color=_FIELD_LINE_COLOR, width=0.035)
        if isinstance(primitive, Polyline)
        else primitive
        for primitive in scene.primitives
    )
    return replace(scene, primitives=primitives)


def _source_scene(config: ElectrostaticLabShowcaseConfig) -> Scene:
    radius = max(config.extent_m * 0.055, 0.12)
    label_size = max(config.extent_m * 0.075, 0.14)
    return Scene(
        primitives=(
            Point(
                id="showcase.electrostatic.source.positive",
                position=config.positive_position,
                radius=radius,
                color=_POSITIVE_COLOR,
            ),
            Point(
                id="showcase.electrostatic.source.negative",
                position=config.negative_position,
                radius=radius,
                color=_NEGATIVE_COLOR,
            ),
            TextLabel(
                id="showcase.electrostatic.label.positive",
                text="+q",
                position=config.positive_position + Vec3(0.0, radius * 2.2, radius * 0.4),
                size=label_size,
                color=_POSITIVE_COLOR,
            ),
            TextLabel(
                id="showcase.electrostatic.label.negative",
                text="−q",
                position=config.negative_position + Vec3(0.0, radius * 2.2, radius * 0.4),
                size=label_size,
                color=_NEGATIVE_COLOR,
            ),
            TextLabel(
                id="showcase.electrostatic.label.field",
                text="E vectors · display-scaled",
                position=Vec3(-config.extent_m, -config.extent_m * 1.08, 0.0),
                size=label_size * 0.72,
                color=_LABEL_COLOR,
            ),
        )
    )


def build_electrostatic_lab_base_scene(
    config: ElectrostaticLabShowcaseConfig | None = None,
) -> Scene:
    """Build the renderer-neutral scientific dipole laboratory Scene.

    The potential is solved through the existing deposited-source -> Poisson ->
    potential-field capability chain. The scalar slice carries physical volts as
    a Scene-v5 quantitative attribute. Electric arrows and field lines reuse the
    common potential-field view layer.
    """
    config = config or ElectrostaticLabShowcaseConfig()
    registry = _registry()
    _solution, model = _solve_potential_model(config, registry)
    return compose_scenes(
        _potential_slice_scene(config, registry, model),
        _vector_scene(config, registry, model),
        _field_lines_scene(config, registry, model),
        _source_scene(config),
    )


def build_electrostatic_lab_scene(
    config: ElectrostaticLabShowcaseConfig | None = None,
    *,
    preset: str = "presentation",
) -> Scene:
    """Build the presented electrostatic flagship Scene."""
    config = config or ElectrostaticLabShowcaseConfig()
    intent = PresentationIntent(
        preset=preset,
        legend=LegendPolicy(visible=True, compact=False, show_units=True, show_min_max=True),
        axes=AxesPolicy(visible=True, grid=False, equal_scale=True),
        annotations=AnnotationPolicy(
            density=AnnotationDensity.TEACHING,
            title="Electrostatic Field Laboratory",
            subtitle=(
                f"dipole ±{config.charge_coulombs:.2g} C · V from Poisson solve · "
                "E = −∇V · arrow lengths display-scaled"
            ),
            show_time=False,
        ),
        animation=AnimationPolicy(reveal=RevealMode.NONE),
        color_scale=ColorScalePolicy(
            palette=ColorPalette.COOLWARM,
            range_mode=ColorRangeMode.SYMMETRIC,
            center=0.0,
            scalar_attribute_name="electric_potential",
        ),
    )
    return compose_presentation(
        build_electrostatic_lab_base_scene(config),
        intent,
        context=PresentationContext(
            primary_primitive_id="showcase.electrostatic.potential.slice",
            quantity_role="electric_potential",
        ),
    )


__all__ = [
    "ElectrostaticLabShowcaseConfig",
    "build_electrostatic_lab_base_scene",
    "build_electrostatic_lab_scene",
]
