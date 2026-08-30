from __future__ import annotations

from spectra.core.primitives import Region, TextLabel
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.statistics.domain import Histogram


def compile_histogram_scene(histogram: Histogram) -> Scene:
    primitives = []
    for index, bin_ in enumerate(histogram.bins):
        height = bin_.count / histogram.total_count
        primitives.append(
            Region(
                id=f"statistics.histogram.bin.{index}",
                boundary=(
                    Vec3(bin_.left, 0.0, 0.0),
                    Vec3(bin_.right, 0.0, 0.0),
                    Vec3(bin_.right, height, 0.0),
                    Vec3(bin_.left, height, 0.0),
                ),
                color=Color(0.55, 0.8, 1.0, 0.55),
            )
        )
        primitives.append(
            TextLabel(
                id=f"statistics.histogram.label.{index}",
                text=f"n={bin_.count}",
                position=Vec3((bin_.left + bin_.right) * 0.5, height, 0.0),
                size=0.65,
            )
        )
    return Scene(primitives=tuple(primitives))
