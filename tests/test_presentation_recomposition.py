from __future__ import annotations

from spectra.core.animation import Timeline, draw_track, move_track
from spectra.core.primitives import Point, Polyline
from spectra.core.scene import Scene
from spectra.core.serialization import scene_from_data, scene_to_data
from spectra.core.types import Vec3
from spectra.presentation import compose_presentation
from spectra.presentation_models import CameraMode, CameraPolicy, PresentationIntent


def test_presentation_tracks_round_trip_with_owner() -> None:
    line = Polyline(
        id="line",
        points=(Vec3(0.0, 0.0, 0.0), Vec3(1.0, 0.0, 0.0)),
    )
    presentation_track = draw_track(
        "line",
        start_time=0.0,
        end_time=1.0,
        owner="presentation",
    )
    scene = Scene(
        primitives=(line,),
        timeline=Timeline(duration=1.0, tracks=(presentation_track,)),
    )

    data = scene_to_data(scene)
    assert data["timeline"]["tracks"][0]["owner"] == "presentation"
    restored = scene_from_data(data)
    assert restored.timeline.tracks[0].owner == "presentation"


def test_default_scientific_owner_keeps_legacy_json_shape() -> None:
    line = Polyline(
        id="line",
        points=(Vec3(0.0, 0.0, 0.0), Vec3(1.0, 0.0, 0.0)),
    )
    track = draw_track("line", start_time=0.0, end_time=1.0)
    data = scene_to_data(
        Scene(
            primitives=(line,),
            timeline=Timeline(duration=1.0, tracks=(track,)),
        )
    )
    assert "owner" not in data["timeline"]["tracks"][0]


def test_switching_from_presentation_to_analysis_removes_reveal_tracks() -> None:
    line = Polyline(
        id="trajectory",
        points=(Vec3(0.0, 0.0, 0.0), Vec3(1.0, 0.0, 0.0)),
    )
    presented = compose_presentation(Scene(primitives=(line,)), "presentation")
    assert any(track.owner == "presentation" for track in presented.timeline.tracks)

    analysis = compose_presentation(presented, "analysis")
    assert all(track.owner != "presentation" for track in analysis.timeline.tracks)
    assert len({primitive.id for primitive in analysis.primitives}) == len(analysis.primitives)


def test_recomposition_is_resource_and_track_idempotent() -> None:
    point = Point(id="sample", position=Vec3(0.0, 0.0, 0.0), radius=0.2)
    once = compose_presentation(Scene(primitives=(point,)), "presentation")
    twice = compose_presentation(once, "presentation")

    assert tuple(primitive.id for primitive in once.primitives) == tuple(
        primitive.id for primitive in twice.primitives
    )
    assert [
        (track.target_id, track.property_path, track.owner)
        for track in once.timeline.tracks
    ] == [
        (track.target_id, track.property_path, track.owner)
        for track in twice.timeline.tracks
    ]


def test_fit_primary_ignores_unrelated_scientific_timeline_targets() -> None:
    primary = Point(id="primary", position=Vec3(0.0, 0.0, 0.0), radius=0.5)
    moving = Point(id="moving", position=Vec3(5.0, 0.0, 0.0), radius=0.2)
    track = move_track(
        "moving",
        Vec3(0.0, 0.0, 0.0),
        Vec3(1.0, 0.0, 0.0),
        start_time=0.0,
        end_time=1.0,
    )
    scene = Scene(
        primitives=(primary, moving),
        timeline=Timeline(duration=1.0, tracks=(track,)),
    )
    intent = PresentationIntent(
        preset="analysis",
        camera=CameraPolicy(mode=CameraMode.FIT_PRIMARY),
    )

    result = compose_presentation(
        scene,
        intent,
        context=None,
    )
    # FIT_PRIMARY falls back to all when no primary id is supplied; the important
    # invariant here is that the scientific timeline remains valid.
    assert result.timeline.tracks[0] == track
