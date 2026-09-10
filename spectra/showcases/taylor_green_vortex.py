from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.attributes import VisualAttribute, VisualAttributeSet
from spectra.core.composition import compose_scenes
from spectra.core.primitives import Polyline, Surface, TextLabel, VectorGlyphSet
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.core.units import (
    KILOGRAM_PER_CUBIC_METER,
    METER_PER_SECOND,
    PASCAL,
    SQUARE_METER_PER_SECOND,
    Quantity,
)
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid3D
from spectra.domains.physics.incompressible_flow3d import IncompressibleFlowProblem3D
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


_VECTOR_COLOR = Color(0.32, 0.88, 1.00, 0.92)
_PATHLINE_COLORS = (
    Color(1.00, 0.82, 0.25, 1.0),
    Color(0.48, 1.00, 0.58, 1.0),
    Color(1.00, 0.48, 0.72, 1.0),
    Color(0.72, 0.60, 1.00, 1.0),
    Color(1.00, 0.62, 0.30, 1.0),
    Color(0.38, 0.92, 0.92, 1.0),
)
_FRAME_COLOR = Color(0.68, 0.74, 0.84, 0.58)
_LABEL_COLOR = Color(0.94, 0.96, 1.0, 1.0)


@dataclass(frozen=True, slots=True)
class TaylorGreenVortexShowcaseConfig:
    """Bounded 3D Taylor-Green reference-CFD showcase configuration.

    The flow solve is a real 3D periodic projection-method solve. The presented
    pressure plane is a final scientific snapshot; pathlines integrate the full
    time-dependent velocity field. This intentionally does not pretend that the
    current reference solver supports an internal solid obstacle.
    """

    domain_length_m: float = 2.0 * math.pi
    xy_count: int = 9
    z_count: int = 5
    velocity_amplitude_m_s: float = 1.0
    density_kg_m3: float = 1.0
    kinematic_viscosity_m2_s: float = 0.01
    end_time_s: float = 0.25
    steps: int = 12
    pressure_max_iterations: int = 1_500
    pressure_tolerance: float = 1.0e-5
    vector_display_scale_s: float = 0.35
    pathline_steps: int = 48

    def __post_init__(self) -> None:
        positive = {
            "domain_length_m": self.domain_length_m,
            "velocity_amplitude_m_s": self.velocity_amplitude_m_s,
            "density_kg_m3": self.density_kg_m3,
            "end_time_s": self.end_time_s,
            "pressure_tolerance": self.pressure_tolerance,
            "vector_display_scale_s": self.vector_display_scale_s,
        }
        for name, value in positive.items():
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        if (
            not math.isfinite(self.kinematic_viscosity_m2_s)
            or self.kinematic_viscosity_m2_s < 0.0
        ):
            raise ValueError(
                "kinematic_viscosity_m2_s must be finite and non-negative"
            )
        if self.xy_count < 5 or self.z_count < 3:
            raise ValueError("Taylor-Green grid counts are too small")
        if self.steps < 1 or self.pathline_steps < 1:
            raise ValueError("Taylor-Green step counts must be >= 1")
        if self.pressure_max_iterations < 1:
            raise ValueError("pressure_max_iterations must be >= 1")


def _registry() -> DomainRegistry:
    registry = DomainRegistry()
    builtin_domain_catalog().load(
        registry,
        ["physics.incompressible_flow.views3d"],
    )
    return registry


def _grid(config: TaylorGreenVortexShowcaseConfig) -> UniformGrid3D:
    return UniformGrid3D(
        UniformGrid1D(0.0, config.domain_length_m, config.xy_count),
        UniformGrid1D(0.0, config.domain_length_m, config.xy_count),
        UniformGrid1D(0.0, config.domain_length_m, config.z_count),
    )


def _initial_velocity(
    config: TaylorGreenVortexShowcaseConfig,
    grid: UniformGrid3D,
) -> tuple[Vec3, ...]:
    wave_number = 2.0 * math.pi / config.domain_length_m
    amplitude = config.velocity_amplitude_m_s
    result = []
    for x, y, z in grid.coordinates:
        kx = wave_number * x
        ky = wave_number * y
        kz = wave_number * z
        result.append(
            Vec3(
                amplitude * math.sin(kx) * math.cos(ky) * math.cos(kz),
                -amplitude * math.cos(kx) * math.sin(ky) * math.cos(kz),
                0.0,
            )
        )
    return tuple(result)


def solve_taylor_green_vortex_showcase(
    config: TaylorGreenVortexShowcaseConfig | None = None,
):
    """Run the existing 3D incompressible reference solver on Taylor-Green data."""
    config = config or TaylorGreenVortexShowcaseConfig()
    registry = _registry()
    grid = _grid(config)
    problem = IncompressibleFlowProblem3D(
        grid=grid,
        initial_velocity=_initial_velocity(config, grid),
        density=Quantity(config.density_kg_m3, KILOGRAM_PER_CUBIC_METER),
        kinematic_viscosity=Quantity(
            config.kinematic_viscosity_m2_s,
            SQUARE_METER_PER_SECOND,
        ),
        velocity_boundary="periodic",
        pressure_boundary="periodic",
        name="showcase.cfd.taylor_green",
    )
    return registry.require("physics.incompressible_flow.simulate3d")(
        problem,
        end_time=config.end_time_s,
        steps=config.steps,
        pressure_max_iterations=config.pressure_max_iterations,
        pressure_tolerance=config.pressure_tolerance,
    )


def _surface_triangles(
    x_count: int,
    y_count: int,
) -> tuple[tuple[int, int, int], ...]:
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


def _final_pressure_surface(solution) -> Surface:
    grid = solution.grid
    state = solution.states[-1]
    z_index = grid.z.count // 2
    z = grid.z.coordinates[z_index]
    vertices: list[Vec3] = []
    pressure: list[float] = []
    for y_index, y in enumerate(grid.y.coordinates):
        for x_index, x in enumerate(grid.x.coordinates):
            flat = grid.flat_index(x_index, y_index, z_index)
            vertices.append(Vec3(x, y, z))
            pressure.append(float(state.pressure[flat]))
    return Surface(
        id="showcase.cfd.pressure.slice",
        vertices=tuple(vertices),
        triangles=_surface_triangles(grid.x.count, grid.y.count),
        color=Color(0.82, 0.86, 0.94, 0.96),
        attributes=VisualAttributeSet(
            (
                VisualAttribute(
                    name="pressure",
                    association="vertex",
                    kind="scalar",
                    values=tuple(pressure),
                    quantity_id="pressure",
                    unit=PASCAL,
                ),
            )
        ),
    )


def _final_velocity_vectors(
    config: TaylorGreenVortexShowcaseConfig,
    solution,
) -> VectorGlyphSet:
    grid = solution.grid
    state = solution.states[-1]
    z_index = grid.z.count // 2
    # Lift arrows slightly above the pressure plane only to prevent z-fighting.
    # Their origins still use the exact grid x/y coordinates and their vectors
    # remain the final velocity state times an explicitly declared display scale.
    z = grid.z.coordinates[z_index] + 0.03 * config.domain_length_m
    origins: list[Vec3] = []
    vectors: list[Vec3] = []
    speeds: list[float] = []
    for y_index, y in enumerate(grid.y.coordinates):
        for x_index, x in enumerate(grid.x.coordinates):
            flat = grid.flat_index(x_index, y_index, z_index)
            velocity = state.velocity[flat]
            origins.append(Vec3(x, y, z))
            vectors.append(velocity * config.vector_display_scale_s)
            speeds.append(velocity.magnitude)
    return VectorGlyphSet(
        id="showcase.cfd.velocity.vectors",
        origins=tuple(origins),
        vectors=tuple(vectors),
        color=_VECTOR_COLOR,
        attributes=VisualAttributeSet(
            (
                VisualAttribute(
                    name="speed",
                    association="instance",
                    kind="scalar",
                    values=tuple(speeds),
                    quantity_id="speed",
                    unit=METER_PER_SECOND,
                ),
            )
        ),
    )


def _pathline_seeds(
    config: TaylorGreenVortexShowcaseConfig,
    solution,
) -> tuple[Vec3, ...]:
    length = config.domain_length_m
    z = solution.grid.z.coordinates[solution.grid.z.count // 2]
    return (
        Vec3(0.18 * length, 0.24 * length, z),
        Vec3(0.28 * length, 0.40 * length, z),
        Vec3(0.42 * length, 0.22 * length, z),
        Vec3(0.58 * length, 0.78 * length, z),
        Vec3(0.72 * length, 0.60 * length, z),
        Vec3(0.82 * length, 0.76 * length, z),
    )


def _pathline_scene(
    config: TaylorGreenVortexShowcaseConfig,
    solution,
) -> Scene:
    registry = _registry()
    make_problem = registry.require(
        "physics.incompressible_flow.pathline_problem3d"
    )
    solve_pathline = registry.require("field_dynamics.solve_pathline", min_version=2)
    primitives = []
    for index, seed in enumerate(_pathline_seeds(config, solution)):
        pathline = solve_pathline(
            make_problem(
                solution,
                seed,
                name=f"showcase.cfd.pathline.{index:02d}",
            ),
            end_time=solution.times[-1],
            steps=config.pathline_steps,
        )
        primitives.append(
            Polyline(
                id=pathline.name,
                points=pathline.positions,
                width=0.008 * config.domain_length_m,
                color=_PATHLINE_COLORS[index % len(_PATHLINE_COLORS)],
            )
        )
    return Scene(primitives=tuple(primitives))


def _context_scene(
    config: TaylorGreenVortexShowcaseConfig,
    solution,
) -> Scene:
    length = config.domain_length_m
    z = solution.grid.z.coordinates[solution.grid.z.count // 2]
    frame = (
        Vec3(0.0, 0.0, z),
        Vec3(length, 0.0, z),
        Vec3(length, length, z),
        Vec3(0.0, length, z),
        Vec3(0.0, 0.0, z),
    )
    final = solution.states[-1]
    return Scene(
        primitives=(
            Polyline(
                id="showcase.cfd.reference.frame",
                points=frame,
                width=0.010 * length,
                color=_FRAME_COLOR,
            ),
            TextLabel(
                id="showcase.cfd.label.model",
                text=(
                    "Taylor-Green vortex · 3D periodic projection-method "
                    "REFERENCE solver"
                ),
                position=Vec3(0.0, -0.55, z),
                size=0.18,
                color=_LABEL_COLOR,
            ),
            TextLabel(
                id="showcase.cfd.label.snapshot",
                text=(
                    f"final pressure snapshot t={final.time:.3g} s · "
                    "pathlines integrate full velocity history · "
                    f"arrow scale {config.vector_display_scale_s:.3g} s"
                ),
                position=Vec3(0.0, -0.90, z),
                size=0.16,
                color=_LABEL_COLOR,
            ),
            TextLabel(
                id="showcase.cfd.label.diagnostics",
                text=(
                    f"max div(u)={final.max_divergence:.3g} s^-1 · "
                    f"pressure residual={final.pressure_residual:.3g} · "
                    f"pressure converged={final.pressure_converged}"
                ),
                position=Vec3(0.0, -1.22, z),
                size=0.16,
                color=_LABEL_COLOR,
            ),
        )
    )


def build_taylor_green_vortex_base_scene(
    config: TaylorGreenVortexShowcaseConfig | None = None,
) -> Scene:
    """Build a final quantitative CFD snapshot plus history-derived pathlines."""
    config = config or TaylorGreenVortexShowcaseConfig()
    solution = solve_taylor_green_vortex_showcase(config)
    return compose_scenes(
        Scene(
            primitives=(
                _final_pressure_surface(solution),
                _final_velocity_vectors(config, solution),
            )
        ),
        _pathline_scene(config, solution),
        _context_scene(config, solution),
    )


def build_taylor_green_vortex_scene(
    config: TaylorGreenVortexShowcaseConfig | None = None,
    *,
    preset: str = "presentation",
) -> Scene:
    """Build the presented reference-CFD Taylor-Green flagship Scene."""
    config = config or TaylorGreenVortexShowcaseConfig()
    intent = PresentationIntent(
        preset=preset,
        legend=LegendPolicy(
            visible=True,
            compact=False,
            show_units=True,
            show_min_max=True,
        ),
        axes=AxesPolicy(visible=True, grid=False, equal_scale=True),
        annotations=AnnotationPolicy(
            density=AnnotationDensity.TEACHING,
            title="Reference CFD · Taylor-Green Vortex",
            subtitle=(
                "3D incompressible projection solve · final signed pressure + "
                "velocity + time-integrated pathlines"
            ),
            show_time=False,
        ),
        animation=AnimationPolicy(reveal=RevealMode.NONE),
        color_scale=ColorScalePolicy(
            palette=ColorPalette.COOLWARM,
            range_mode=ColorRangeMode.SYMMETRIC,
            center=0.0,
            scalar_attribute_name="pressure",
        ),
    )
    return compose_presentation(
        build_taylor_green_vortex_base_scene(config),
        intent,
        context=PresentationContext(
            primary_primitive_id="showcase.cfd.pressure.slice",
            quantity_role="pressure",
        ),
    )


__all__ = [
    "TaylorGreenVortexShowcaseConfig",
    "solve_taylor_green_vortex_showcase",
    "build_taylor_green_vortex_base_scene",
    "build_taylor_green_vortex_scene",
]
