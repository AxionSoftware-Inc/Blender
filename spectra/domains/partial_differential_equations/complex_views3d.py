from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from spectra.domains.partial_differential_equations.complex3d import ComplexPDESolution3D
from spectra.domains.partial_differential_equations.domain3d import ScalarPDESolution3D
from spectra.domains.registry import DomainDependency, DomainRegistry


ComplexViewComponent3D = Literal["real", "imaginary", "magnitude", "magnitude_squared"]
SliceAxis3D = Literal["x", "y", "z"]


@dataclass(frozen=True, slots=True)
class ComplexPDESliceView3D:
    solution: ComplexPDESolution3D
    axis: SliceAxis3D
    index: int
    component: ComplexViewComponent3D = "magnitude_squared"
    name: str | None = None

    def __post_init__(self) -> None:
        if self.axis not in {"x", "y", "z"}:
            raise ValueError("complex 3D PDE slice axis must be x, y, or z")
        if self.component not in {"real", "imaginary", "magnitude", "magnitude_squared"}:
            raise ValueError(f"unknown complex 3D view component: {self.component}")
        count = {
            "x": self.solution.grid.x.count,
            "y": self.solution.grid.y.count,
            "z": self.solution.grid.z.count,
        }[self.axis]
        if not 0 <= self.index < count:
            raise IndexError("complex 3D PDE slice index out of range")


def _component(value: complex, component: ComplexViewComponent3D) -> float:
    sample = complex(value)
    if component == "real":
        return float(sample.real)
    if component == "imaginary":
        return float(sample.imag)
    if component == "magnitude":
        return float(abs(sample))
    if component == "magnitude_squared":
        return float(abs(sample) ** 2)
    raise ValueError(f"unknown complex 3D view component: {component}")


def scalar_solution_from_complex_view(view: ComplexPDESliceView3D) -> ScalarPDESolution3D:
    return ScalarPDESolution3D(
        grid=view.solution.grid,
        times=view.solution.times,
        states=tuple(
            tuple(_component(value, view.component) for value in state)
            for state in view.solution.states
        ),
        name=view.name or f"{view.solution.name}.{view.component}",
    )


class ComplexPDEViews3DDomain:
    name = "partial_differential_equations.complex_views3d"
    version = "1"
    dependencies = (
        DomainDependency("pde.complex.solution3d"),
        DomainDependency("pde.scalar_slice_view3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        slice_view_type = registry.require("pde.scalar_slice_view3d")

        def compile_view(view: ComplexPDESliceView3D):
            scalar_solution = scalar_solution_from_complex_view(view)
            return registry.compile_scene(
                slice_view_type(
                    solution=scalar_solution,
                    axis=view.axis,
                    index=view.index,
                    name=view.name or f"{scalar_solution.name}.{view.axis}_slice_{view.index}",
                )
            )

        registry.register_semantic_type("pde.complex.slice_view3d", ComplexPDESliceView3D)
        registry.provide("pde.complex.slice_view3d", ComplexPDESliceView3D)
        registry.provide(
            "pde.complex.scalar_solution_from_view3d",
            scalar_solution_from_complex_view,
        )
        registry.register_visualization(ComplexPDESliceView3D, compile_view)
