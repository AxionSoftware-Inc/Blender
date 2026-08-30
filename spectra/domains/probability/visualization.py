from __future__ import annotations

from spectra.core.primitives import Polyline, TextLabel
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.probability.domain import DiscreteDistribution


def compile_distribution_scene(
    distribution: DiscreteDistribution,
    *,
    baseline: float = 0.0,
) -> Scene:
    primitives = []
    for index, outcome in enumerate(distribution.outcomes):
        x = outcome.value
        y = outcome.probability
        primitives.append(
            Polyline(
                id=f"probability.stem.{index}",
                points=(Vec3(x, baseline, 0.0), Vec3(x, y, 0.0)),
                width=0.035,
                color=Color(0.45, 0.75, 1.0, 1.0),
            )
        )
        primitives.append(
            TextLabel(
                id=f"probability.label.{index}",
                text=f"p={y:.4g}",
                position=Vec3(x, y, 0.0),
                size=0.7,
            )
        )
    return Scene(primitives=tuple(primitives))
