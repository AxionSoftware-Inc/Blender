from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.composition import compose_scenes
from spectra.core.primitives import Point, Polyline, Surface, TextLabel
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.core.units import KILOGRAM, Quantity
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.differential_geometry.geodesics import GeodesicProblem, GeodesicSolution
from spectra.domains.physics.general_relativity import SchwarzschildSpacetime
from spectra.presentation import compose_presentation
from spectra.presentation_models import (
    AnnotationDensity,
    AnnotationPolicy,
    AnimationPolicy,
    AxesPolicy,
    LegendPolicy,
    PresentationContext,
    PresentationIntent,
    RevealMode,
)


_HORIZON_COLOR = Color(0.012, 0.016, 0.028, 1.0)
_HORIZON_RING_COLOR = Color(0.90, 0.38, 0.16, 0.92)
_PHOTON_SPHERE_COLOR = Color(1.00, 0.78, 0.20, 0.82)
_ORBIT_COLOR = Color(1.00, 0.86, 0.30, 1.0)
_RAY_COLORS = (
    Color(0.30, 0.82, 1.00, 1.0),
    Color(0.47, 0.94, 0.62, 1.0),
    Color(0.86, 0.56, 1.00, 1.0),
)
_LABEL_COLOR = Color(0.94, 0.96, 1.0, 1.0)


@dataclass(frozen=True, slots=True)
class BlackHoleGeodesicShowcaseConfig:
    """Canonical exterior-Schwarzschild null-geodesic showcase.

    Scientific coordinates use ``(ct, r, theta, phi)`` in SI-compatible length
    coordinates. Renderer coordinates are an explicit equatorial projection,
    ``(x, y) = (r cos(phi), r sin(phi)) / r_s``. Therefore changing the black-hole
    mass changes the physical scale without changing the normalized display layout.
    """

    # Approximate 10-solar-mass stellar black hole. The value is explicit in kg;
    # all numerical/display scales below are derived from the resulting r_s.
    black_hole_mass_kg: float = 1.988_47e31
    photon_orbit_steps: int = 128
    scatter_steps: int = 160
    scatter_start_radius_rs: float = 8.0
    scatter_start_phi_rad: float = -1.0
    scatter_parameter_length_rs: float = 16.0
    impact_parameters_rs: tuple[float, ...] = (2.7, 3.0, 4.0)
    derivative_step_fraction_rs: float = 1.0e-4
    horizon_latitudes: int = 10
    horizon_longitudes: int = 24

    def __post_init__(self) -> None:
        positive = {
            "black_hole_mass_kg": self.black_hole_mass_kg,
            "scatter_start_radius_rs": self.scatter_start_radius_rs,
            "scatter_parameter_length_rs": self.scatter_parameter_length_rs,
            "derivative_step_fraction_rs": self.derivative_step_fraction_rs,
        }
        for name, value in positive.items():
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        if self.photon_orbit_steps < 8 or self.scatter_steps < 8:
            raise ValueError("black-hole showcase geodesic step counts must be >= 8")
        if self.scatter_start_radius_rs <= 1.5:
            raise ValueError("scatter_start_radius_rs must exceed the photon sphere")
        if not math.isfinite(self.scatter_start_phi_rad):
            raise ValueError("scatter_start_phi_rad must be finite")
        if not self.impact_parameters_rs:
            raise ValueError("impact_parameters_rs cannot be empty")
        critical = 1.5 * math.sqrt(3.0)
        for impact in self.impact_parameters_rs:
            if not math.isfinite(impact) or impact <= critical:
                raise ValueError(
                    "scattering impact parameters must exceed the Schwarzschild "
                    "critical value 3*sqrt(3)/2 r_s"
                )
        if self.horizon_latitudes < 4 or self.horizon_longitudes < 8:
            raise ValueError("horizon mesh resolution is too small")

    @property
    def spacetime(self) -> SchwarzschildSpacetime:
        return SchwarzschildSpacetime(
            Quantity(self.black_hole_mass_kg, KILOGRAM),
            name="showcase.black_hole.schwarzschild",
        )

    @property
    def schwarzschild_radius_m(self) -> float:
        return self.spacetime.schwarzschild_radius


@dataclass(frozen=True, slots=True)
class BlackHoleGeodesicShowcaseResult:
    spacetime: SchwarzschildSpacetime
    photon_orbit: GeodesicSolution
    scattering_rays: tuple[GeodesicSolution, ...]
    impact_parameters_rs: tuple[float, ...]


def _registry() -> DomainRegistry:
    registry = DomainRegistry()
    builtin_domain_catalog().load(
        registry,
        ["physics.relativity.general", "differential_geometry.geodesics"],
    )
    return registry


def _null_circular_initial_state(
    spacetime: SchwarzschildSpacetime,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    radius = 1.5 * spacetime.schwarzschild_radius
    factor = 1.0 - spacetime.schwarzschild_radius / radius
    # Choosing dphi/dlambda = 1/r fixes only the affine-parameter scale. The
    # null condition then determines d(ct)/dlambda; the curve itself is unchanged.
    angular_velocity = 1.0 / radius
    ct_velocity = radius * angular_velocity / math.sqrt(factor)
    return (
        (0.0, radius, 0.5 * math.pi, 0.0),
        (ct_velocity, 0.0, 0.0, angular_velocity),
    )


def _null_scatter_initial_state(
    spacetime: SchwarzschildSpacetime,
    *,
    start_radius_rs: float,
    start_phi: float,
    impact_parameter_rs: float,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    radius_s = spacetime.schwarzschild_radius
    radius = start_radius_rs * radius_s
    impact = impact_parameter_rs * radius_s
    factor = 1.0 - radius_s / radius

    # Set conserved-energy scale E=1. For equatorial Schwarzschild null motion:
    #   E = f d(ct)/dlambda, L = r^2 dphi/dlambda, b = L/E
    # and g(v,v)=0 gives the inward radial component below.
    energy = 1.0
    angular_momentum = impact * energy
    ct_velocity = energy / factor
    angular_velocity = angular_momentum / (radius * radius)
    radial_squared = energy * energy - factor * angular_momentum * angular_momentum / (radius * radius)
    if radial_squared <= 0.0:
        raise ValueError("scattering initial state is not radially accessible")
    radial_velocity = -math.sqrt(radial_squared)
    return (
        (0.0, radius, 0.5 * math.pi, start_phi),
        (ct_velocity, radial_velocity, 0.0, angular_velocity),
    )


def solve_black_hole_geodesic_showcase(
    config: BlackHoleGeodesicShowcaseConfig | None = None,
) -> BlackHoleGeodesicShowcaseResult:
    """Solve the canonical photon orbit and bending rays with the generic geodesic role."""
    config = config or BlackHoleGeodesicShowcaseConfig()
    registry = _registry()
    spacetime = config.spacetime
    metric = spacetime.metric()
    solve = registry.require("geometry.solve_geodesic", min_version=2)
    radius_s = spacetime.schwarzschild_radius
    derivative_step = config.derivative_step_fraction_rs * radius_s

    orbit_position, orbit_velocity = _null_circular_initial_state(spacetime)
    orbit_radius = orbit_position[1]
    orbit = solve(
        GeodesicProblem(
            metric=metric,
            initial_position=orbit_position,
            initial_velocity=orbit_velocity,
            name="showcase.black_hole.photon_orbit",
        ),
        end_parameter=2.0 * math.pi * orbit_radius,
        steps=config.photon_orbit_steps,
        derivative_step=derivative_step,
    )

    rays: list[GeodesicSolution] = []
    for index, impact in enumerate(config.impact_parameters_rs):
        position, velocity = _null_scatter_initial_state(
            spacetime,
            start_radius_rs=config.scatter_start_radius_rs,
            start_phi=config.scatter_start_phi_rad,
            impact_parameter_rs=impact,
        )
        rays.append(
            solve(
                GeodesicProblem(
                    metric=metric,
                    initial_position=position,
                    initial_velocity=velocity,
                    name=f"showcase.black_hole.scatter_{index:02d}",
                ),
                end_parameter=config.scatter_parameter_length_rs * radius_s,
                steps=config.scatter_steps,
                derivative_step=derivative_step,
            )
        )

    return BlackHoleGeodesicShowcaseResult(
        spacetime=spacetime,
        photon_orbit=orbit,
        scattering_rays=tuple(rays),
        impact_parameters_rs=config.impact_parameters_rs,
    )


def _project_equatorial(
    solution: GeodesicSolution,
    radius_s: float,
) -> tuple[Vec3, ...]:
    points = []
    for position in solution.positions:
        radius = position[1]
        phi = position[3]
        points.append(
            Vec3(
                radius * math.cos(phi) / radius_s,
                radius * math.sin(phi) / radius_s,
                0.0,
            )
        )
    return tuple(points)


def _circle(
    primitive_id: str,
    radius: float,
    color: Color,
    *,
    samples: int = 128,
    width: float = 0.025,
) -> Polyline:
    points = tuple(
        Vec3(
            radius * math.cos(2.0 * math.pi * index / samples),
            radius * math.sin(2.0 * math.pi * index / samples),
            0.0,
        )
        for index in range(samples + 1)
    )
    return Polyline(id=primitive_id, points=points, width=width, color=color)


def _horizon_surface(config: BlackHoleGeodesicShowcaseConfig) -> Surface:
    latitudes = config.horizon_latitudes
    longitudes = config.horizon_longitudes
    vertices: list[Vec3] = [Vec3(0.0, 0.0, 1.0)]
    for lat_index in range(1, latitudes):
        theta = math.pi * lat_index / latitudes
        sin_theta = math.sin(theta)
        cos_theta = math.cos(theta)
        for lon_index in range(longitudes):
            phi = 2.0 * math.pi * lon_index / longitudes
            vertices.append(
                Vec3(
                    sin_theta * math.cos(phi),
                    sin_theta * math.sin(phi),
                    cos_theta,
                )
            )
    south_index = len(vertices)
    vertices.append(Vec3(0.0, 0.0, -1.0))

    triangles: list[tuple[int, int, int]] = []
    first_ring = 1
    for lon_index in range(longitudes):
        next_lon = (lon_index + 1) % longitudes
        triangles.append((0, first_ring + lon_index, first_ring + next_lon))

    for lat_index in range(latitudes - 2):
        ring_a = 1 + lat_index * longitudes
        ring_b = ring_a + longitudes
        for lon_index in range(longitudes):
            next_lon = (lon_index + 1) % longitudes
            a = ring_a + lon_index
            b = ring_a + next_lon
            c = ring_b + lon_index
            d = ring_b + next_lon
            triangles.append((a, c, d))
            triangles.append((a, d, b))

    last_ring = 1 + (latitudes - 2) * longitudes
    for lon_index in range(longitudes):
        next_lon = (lon_index + 1) % longitudes
        triangles.append((last_ring + lon_index, south_index, last_ring + next_lon))

    return Surface(
        id="showcase.black_hole.event_horizon.surface",
        vertices=tuple(vertices),
        triangles=tuple(triangles),
        color=_HORIZON_COLOR,
    )


def _context_scene(config: BlackHoleGeodesicShowcaseConfig) -> Scene:
    return Scene(
        primitives=(
            _horizon_surface(config),
            _circle(
                "showcase.black_hole.event_horizon.ring",
                1.0,
                _HORIZON_RING_COLOR,
                width=0.035,
            ),
            _circle(
                "showcase.black_hole.photon_sphere.reference",
                1.5,
                _PHOTON_SPHERE_COLOR,
                width=0.020,
            ),
            TextLabel(
                id="showcase.black_hole.label.horizon",
                text="event horizon  r = r_s",
                position=Vec3(1.08, -0.15, 0.08),
                size=0.20,
                color=_HORIZON_RING_COLOR,
            ),
            TextLabel(
                id="showcase.black_hole.label.photon_sphere",
                text="photon sphere  r = 1.5 r_s",
                position=Vec3(1.62, 0.20, 0.08),
                size=0.20,
                color=_PHOTON_SPHERE_COLOR,
            ),
        )
    )


def _trajectory_scene(
    config: BlackHoleGeodesicShowcaseConfig,
    result: BlackHoleGeodesicShowcaseResult,
) -> Scene:
    radius_s = result.spacetime.schwarzschild_radius
    primitives = [
        Polyline(
            id="showcase.black_hole.photon_orbit.trajectory",
            points=_project_equatorial(result.photon_orbit, radius_s),
            width=0.045,
            color=_ORBIT_COLOR,
        )
    ]
    for index, (impact, solution) in enumerate(
        zip(result.impact_parameters_rs, result.scattering_rays, strict=True)
    ):
        points = _project_equatorial(solution, radius_s)
        color = _RAY_COLORS[index % len(_RAY_COLORS)]
        primitives.append(
            Polyline(
                id=f"showcase.black_hole.scatter_{index:02d}.trajectory",
                points=points,
                width=0.035,
                color=color,
            )
        )
        primitives.append(
            Point(
                id=f"showcase.black_hole.scatter_{index:02d}.start",
                position=points[0],
                radius=0.08,
                color=color,
            )
        )
        primitives.append(
            TextLabel(
                id=f"showcase.black_hole.scatter_{index:02d}.label",
                text=f"null ray  b={impact:.3g} r_s",
                position=points[0] + Vec3(0.15, 0.15 + 0.18 * index, 0.05),
                size=0.18,
                color=color,
            )
        )
    return Scene(primitives=tuple(primitives))


def _annotation_scene(
    result: BlackHoleGeodesicShowcaseResult,
) -> Scene:
    radius_s = result.spacetime.schwarzschild_radius
    mass = result.spacetime.mass.si_value
    return Scene(
        primitives=(
            TextLabel(
                id="showcase.black_hole.label.projection",
                text="equatorial projection: x=(r/r_s) cos(phi), y=(r/r_s) sin(phi)",
                position=Vec3(-7.8, -6.2, 0.0),
                size=0.22,
                color=_LABEL_COLOR,
            ),
            TextLabel(
                id="showcase.black_hole.label.scale",
                text=f"M={mass:.4g} kg · r_s={radius_s:.4g} m · trajectories are solved null geodesics",
                position=Vec3(-7.8, -6.65, 0.0),
                size=0.22,
                color=_LABEL_COLOR,
            ),
        )
    )


def build_black_hole_geodesic_base_scene(
    config: BlackHoleGeodesicShowcaseConfig | None = None,
) -> Scene:
    """Solve and project renderer-neutral Schwarzschild null geodesics."""
    config = config or BlackHoleGeodesicShowcaseConfig()
    result = solve_black_hole_geodesic_showcase(config)
    return compose_scenes(
        _context_scene(config),
        _trajectory_scene(config, result),
        _annotation_scene(result),
    )


def build_black_hole_geodesic_scene(
    config: BlackHoleGeodesicShowcaseConfig | None = None,
    *,
    preset: str = "cinematic",
) -> Scene:
    """Build the presented Schwarzschild-geodesic flagship Scene."""
    config = config or BlackHoleGeodesicShowcaseConfig()
    intent = PresentationIntent(
        preset=preset,
        legend=LegendPolicy(visible=False),
        axes=AxesPolicy(visible=False, grid=False, equal_scale=True),
        annotations=AnnotationPolicy(
            density=AnnotationDensity.IMPORTANT_ONLY,
            title="Schwarzschild Black Hole · Null Geodesics",
            subtitle=(
                "generic metric → Christoffel symbols → geodesic ODE → explicit equatorial projection"
            ),
            show_time=False,
        ),
        animation=AnimationPolicy(reveal=RevealMode.NONE),
    )
    return compose_presentation(
        build_black_hole_geodesic_base_scene(config),
        intent,
        context=PresentationContext(
            primary_primitive_id="showcase.black_hole.photon_orbit.trajectory",
        ),
    )


__all__ = [
    "BlackHoleGeodesicShowcaseConfig",
    "BlackHoleGeodesicShowcaseResult",
    "solve_black_hole_geodesic_showcase",
    "build_black_hole_geodesic_base_scene",
    "build_black_hole_geodesic_scene",
]
