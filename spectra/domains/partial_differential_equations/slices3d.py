from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from spectra.domains.partial_differential_equations.domain2d import (
    ScalarPDESolution2D,
    UniformGrid2D,
)
from spectra.domains.partial_differential_equations.domain3d import ScalarPDESolution3D
from spectra.domains.registry import DomainDependency, DomainRegistry


SliceAxis3D = Literal["x", "y", "z"]


@dataclass(frozen=True, slots=True)
class ScalarPDESliceView3D:
    solution: ScalarPDESolution3D
    axis: SliceAxis3D
    index: int
    name: str | None = None

    def __post_init__(self) -> None:
        if self.axis not in {"x", "y", "z"}:
            raise ValueError("3D PDE slice axis must be x, y, or z")
        count = {
            "x": self.solution.grid.x.count,
            "y": self.solution.grid.y.count,
            "z": self.solution.grid.z.count,
        }[self.axis]
        if not 0 <= self.index < count:
            raise IndexError("3D PDE slice index out of range")


def slice_solution_3d(view: ScalarPDESliceView3D) -> ScalarPDESolution2D:
    source = view.solution
    grid3d = source.grid

    if view.axis == "z":
        grid2d = UniformGrid2D(grid3d.x, grid3d.y)

        def extract(state):
            return tuple(
                state[grid3d.flat_index(x_index, y_index, view.index)]
                for y_index in range(grid3d.y.count)
                for x_index in range(grid3d.x.count)
            )

    elif view.axis == "y":
        grid2d = UniformGrid2D(grid3d.x, grid3d.z)

        def extract(state):
            return tuple(
                state[grid3d.flat_index(x_index, view.index, z_index)]
                for z_index in range(grid3d.z.count)
                for x_index in range(grid3d.x.count)
            )

    else:
        grid2d = UniformGrid2D(grid3d.y, grid3d.z)

        def extract(state):
            return tuple(
                state[grid3d.flat_index(view.index, y_index, z_index)]
                for z_index in range(grid3d.z.count)
                for y_index in range(grid3d.y.count)
            )

    return ScalarPDESolution2D(
        grid=grid2d,
        times=source.times,
        states=tuple(extract(state) for state in source.states),
        name=view.name or f"{source.name}.{view.axis}_slice_{view.index}",
    )


class PDESlices3DDomain:
    name = "partial_differential_equations.slices3d"
    version = "1"
    dependencies = (
        DomainDependency("pde.scalar_solution3d"),
        DomainDependency("pde.uniform_grid2d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        from spectra.domains.partial_differential_equations.visualization2d import (
            compile_scalar_pde_solution_2d_scene,
        )

        def compile_view(view: ScalarPDESliceView3D):
            return compile_scalar_pde_solution_2d_scene(slice_solution_3d(view))

        registry.register_semantic_type("pde.scalar_slice_view3d", ScalarPDESliceView3D)
        registry.provide("pde.scalar_slice_view3d", ScalarPDESliceView3D)
        registry.provide("pde.slice_solution_3d", slice_solution_3d)
        registry.register_visualization(ScalarPDESliceView3D, compile_view)
