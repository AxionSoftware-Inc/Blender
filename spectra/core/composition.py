from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from spectra.core.animation import Timeline, Track
from spectra.core.materials import Material
from spectra.core.primitives import Group, Primitive
from spectra.core.scene import Scene


def _qualified(namespace: str, identifier: str) -> str:
    if not namespace:
        raise ValueError("scene namespace cannot be empty")
    if not identifier:
        raise ValueError("scene identifier cannot be empty")
    return f"{namespace}/{identifier}"


def namespace_scene(scene: Scene, namespace: str) -> Scene:
    """Return a Scene whose primitive/material identifiers are namespaced.

    This lets independently-compiled scientific modules be composed without
    requiring them to coordinate local IDs in advance.
    """

    primitive_ids = {
        primitive.id: _qualified(namespace, primitive.id)
        for primitive in scene.primitives
    }
    material_ids = {
        material.id: _qualified(namespace, material.id)
        for material in scene.materials
    }

    primitives: list[Primitive] = []
    for primitive in scene.primitives:
        changes: dict[str, object] = {"id": primitive_ids[primitive.id]}
        if primitive.material_id is not None:
            changes["material_id"] = material_ids[primitive.material_id]
        if isinstance(primitive, Group):
            changes["children"] = tuple(primitive_ids[child] for child in primitive.children)
        primitives.append(replace(primitive, **changes))

    materials = tuple(
        replace(material, id=material_ids[material.id])
        for material in scene.materials
    )
    tracks = tuple(
        Track(
            target_id=primitive_ids[track.target_id],
            property_path=track.property_path,
            keyframes=track.keyframes,
        )
        for track in scene.timeline.tracks
    )
    active_camera_id = (
        primitive_ids[scene.active_camera_id]
        if scene.active_camera_id is not None
        else None
    )

    return Scene(
        primitives=tuple(primitives),
        timeline=Timeline(duration=scene.timeline.duration, tracks=tracks),
        frame=scene.frame,
        active_camera_id=active_camera_id,
        materials=materials,
    )


def compose_scenes(*scenes: Scene) -> Scene:
    """Compose independent Scenes that share one scientific coordinate frame."""
    if not scenes:
        return Scene()

    frame = scenes[0].frame
    if any(scene.frame != frame for scene in scenes[1:]):
        raise ValueError(
            "composed scenes must share the same CoordinateFrame3D; "
            "map them explicitly before composition"
        )

    primitives: list[Primitive] = []
    primitive_ids: set[str] = set()
    materials_by_id: dict[str, Material] = {}
    tracks = []
    duration = 0.0
    active_camera_id: str | None = None

    for scene in scenes:
        for primitive in scene.primitives:
            if primitive.id in primitive_ids:
                raise ValueError(
                    f"scene composition contains duplicate primitive id: {primitive.id}"
                )
            primitive_ids.add(primitive.id)
            primitives.append(primitive)

        for material in scene.materials:
            existing = materials_by_id.get(material.id)
            if existing is not None and existing != material:
                raise ValueError(
                    f"scene composition contains conflicting material id: {material.id}"
                )
            materials_by_id[material.id] = material

        tracks.extend(scene.timeline.tracks)
        duration = max(duration, scene.timeline.duration)

        if scene.active_camera_id is not None:
            if active_camera_id is not None and active_camera_id != scene.active_camera_id:
                raise ValueError("scene composition contains multiple active cameras")
            active_camera_id = scene.active_camera_id

    # Timeline constructor validates duplicate target/property tracks.
    timeline = Timeline(duration=duration, tracks=tuple(tracks))
    return Scene(
        primitives=tuple(primitives),
        timeline=timeline,
        frame=frame,
        active_camera_id=active_camera_id,
        materials=tuple(materials_by_id.values()),
    )


def compose_namespaced_scenes(
    scenes: Iterable[tuple[str, Scene]],
) -> Scene:
    """Namespace and compose a sequence of independently-authored Scenes."""
    return compose_scenes(*(namespace_scene(scene, namespace) for namespace, scene in scenes))
