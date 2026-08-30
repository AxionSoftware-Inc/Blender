from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.primitives import Group, Polyline
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.field_dynamics.domain import CurveSolution3D, IntegralCurveProblem3D
from spectra.domains.mathematics.fields import VectorField3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class IntegralCurveBundleProblem3D:
    """A reusable set of field lines/streamlines from multiple seed points."""

    field: VectorField3D
    seeds: tuple[Vec3, ...]
    parameter_length: float
    steps_per_direction: int = 128
    mode: str = "normalized"
    bidirectional: bool = True
    name: str = "integral_curve_bundle3d"

    def __post_init__(self) -> None:
        if not self.seeds:
            raise ValueError("integral-curve bundle requires at least one seed")
        if any(not isinstance(seed, Vec3) for seed in self.seeds):
            raise TypeError("integral-curve bundle seeds must be Vec3")
        if not math.isfinite(self.parameter_length) or self.parameter_length <= 0.0:
            raise ValueError("integral-curve bundle parameter_length must be finite and positive")
        if self.steps_per_direction < 1:
            raise ValueError("integral-curve bundle steps_per_direction must be >= 1")
        if self.mode not in {"field", "normalized"}:
            raise ValueError("integral-curve bundle mode must be field or normalized")
        if not self.name:
            raise ValueError("integral-curve bundle name cannot be empty")


@dataclass(frozen=True, slots=True)
class IntegralCurveBundleSolution3D:
    curves: tuple[CurveSolution3D, ...]
    name: str = "integral_curve_bundle3d"

    def __post_init__(self) -> None:
        if not self.curves:
            raise ValueError("integral-curve bundle solution cannot be empty")
        if not self.name:
            raise ValueError("integral-curve bundle solution name cannot be empty")


def compile_integral_curve_bundle_scene(
    solution: IntegralCurveBundleSolution3D,
    *,
    color: Color = Color(0.95, 0.72, 0.25, 1.0),
    width: float = 0.02,
) -> Scene:
    ids = tuple(f"{solution.name}.curve_{index}" for index in range(len(solution.curves)))
    curves = tuple(
        Polyline(
            id=primitive_id,
            points=curve.positions,
            width=width,
            color=color,
        )
        for primitive_id, curve in zip(ids, solution.curves, strict=True)
    )
    return Scene(
        primitives=(
            *curves,
            Group(id=f"{solution.name}.group", children=ids),
        )
    )


class IntegralCurveBundles3DDomain:
    """Batch field-line construction composed from the generic curve solver."""

    name = "field_dynamics.bundles3d"
    version = "1"
    dependencies = (
        DomainDependency("mathematics.vector_field3d"),
        DomainDependency("field_dynamics.integral_curve_problem3d"),
        DomainDependency("field_dynamics.solve_integral_curve"),
    )

    def register(self, registry: DomainRegistry) -> None:
        problem_type = registry.require("field_dynamics.integral_curve_problem3d")
        solve_curve = registry.require("field_dynamics.solve_integral_curve")

        def solve_bundle(
            problem: IntegralCurveBundleProblem3D,
        ) -> IntegralCurveBundleSolution3D:
            curves: list[CurveSolution3D] = []

            reverse_field = VectorField3D(
                evaluator=lambda position: problem.field.evaluate(position) * -1.0,
                name=f"{problem.field.name}.reversed",
                output_unit=problem.field.output_unit,
            )

            for seed_index, seed in enumerate(problem.seeds):
                forward = solve_curve(
                    problem_type(
                        field=problem.field,
                        initial_position=seed,
                        mode=problem.mode,
                        name=f"{problem.name}.seed_{seed_index}.forward",
                    ),
                    end_parameter=problem.parameter_length,
                    steps=problem.steps_per_direction,
                )

                if not problem.bidirectional:
                    curves.append(forward)
                    continue

                backward = solve_curve(
                    problem_type(
                        field=reverse_field,
                        initial_position=seed,
                        mode=problem.mode,
                        name=f"{problem.name}.seed_{seed_index}.backward",
                    ),
                    end_parameter=problem.parameter_length,
                    steps=problem.steps_per_direction,
                )
                negative_parameters = tuple(
                    -value for value in reversed(backward.parameters[1:])
                )
                negative_positions = tuple(reversed(backward.positions[1:]))
                curves.append(
                    CurveSolution3D(
                        parameters=negative_parameters + forward.parameters,
                        positions=negative_positions + forward.positions,
                        name=f"{problem.name}.seed_{seed_index}",
                    )
                )

            return IntegralCurveBundleSolution3D(
                curves=tuple(curves),
                name=problem.name,
            )

        registry.register_semantic_type(
            "field_dynamics.integral_curve_bundle_problem3d",
            IntegralCurveBundleProblem3D,
        )
        registry.register_semantic_type(
            "field_dynamics.integral_curve_bundle_solution3d",
            IntegralCurveBundleSolution3D,
        )
        registry.provide(
            "field_dynamics.integral_curve_bundle_problem3d",
            IntegralCurveBundleProblem3D,
        )
        registry.provide(
            "field_dynamics.solve_integral_curve_bundle3d",
            solve_bundle,
        )
        registry.register_visualization(
            IntegralCurveBundleSolution3D,
            compile_integral_curve_bundle_scene,
        )
