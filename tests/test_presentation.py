from __future__ import annotations

import pytest

from spectra.core.primitives import Point, Polyline
from spectra.core.scene import Scene
from spectra.core.types import Vec3
from spectra.presentation import staggered_reveal


def test_staggered_reveal_is_domain_neutral() -> None:
    scene = Scene(
        primitives=(
            Polyline(
                id="curve",
                points=(Vec3(0.0, 0.0, 0.0), Vec3(1.0, 1.0, 0.0)),
            ),
            Point(id="marker", position=Vec3(1.0, 1.0, 0.0)),
        )
    )

    animated = staggered_reveal(scene, item_duration=1.0, stagger=0.5)

    start = animated.sample(0.0)
    assert start.get("curve").trim_end == pytest.approx(0.0)
    assert start.get("marker").opacity == pytest.approx(0.0)

    halfway = animated.sample(0.5)
    assert halfway.get("curve").trim_end == pytest.approx(0.5)
    assert halfway.get("marker").opacity == pytest.approx(0.0)

    finished = animated.sample(animated.timeline.duration)
    assert finished.get("curve").trim_end == pytest.approx(1.0)
    assert finished.get("marker").opacity == pytest.approx(1.0)
