from __future__ import annotations

import json
from typing import Any

from .animation import Keyframe, Timeline, Track
from .primitives import Group, Point, Polyline, Primitive, Region, Surface, TextLabel, VectorGlyph
from .scene import Scene
from .types import Color, Vec2, Vec3


SCENE_SCHEMA = "spectra.scene"
SCENE_SCHEMA_VERSION = 1


class SceneSerializationError(ValueError):
    pass


def _vec3_to_data(value: Vec3) -> list[float]:
    return [value.x, value.y, value.z]


def _vec3_from_data(value: Any) -> Vec3:
    if not isinstance(value, list) or len(value) != 3:
        raise SceneSerializationError("expected a three-component vector")
    return Vec3(float(value[0]), float(value[1]), float(value[2]))


def _color_to_data(value: Color) -> list[float]:
    return [value.r, value.g, value.b, value.a]


def _color_from_data(value: Any) -> Color:
    if not isinstance(value, list) or len(value) != 4:
        raise SceneSerializationError("expected a four-component color")
    return Color(*(float(component) for component in value))


def _encode_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Vec2):
        return {"$type": "vec2", "value": [value.x, value.y]}
    if isinstance(value, Vec3):
        return {"$type": "vec3", "value": _vec3_to_data(value)}
    if isinstance(value, Color):
        return {"$type": "color", "value": _color_to_data(value)}
    if isinstance(value, tuple):
        return {"$type": "tuple", "items": [_encode_value(item) for item in value]}
    if isinstance(value, list):
        return [_encode_value(item) for item in value]
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise SceneSerializationError("serialized dictionaries require string keys")
        return {key: _encode_value(item) for key, item in value.items()}
    raise SceneSerializationError(f"unsupported animation value type: {type(value).__qualname__}")


def _decode_value(value: Any) -> Any:
    if not isinstance(value, (dict, list)):
        return value
    if isinstance(value, list):
        return [_decode_value(item) for item in value]

    marker = value.get("$type")
    if marker == "vec2":
        raw = value.get("value")
        if not isinstance(raw, list) or len(raw) != 2:
            raise SceneSerializationError("invalid vec2 value")
        return Vec2(float(raw[0]), float(raw[1]))
    if marker == "vec3":
        return _vec3_from_data(value.get("value"))
    if marker == "color":
        return _color_from_data(value.get("value"))
    if marker == "tuple":
        items = value.get("items")
        if not isinstance(items, list):
            raise SceneSerializationError("invalid tuple value")
        return tuple(_decode_value(item) for item in items)
    if marker is not None:
        raise SceneSerializationError(f"unknown serialized value type: {marker}")
    return {key: _decode_value(item) for key, item in value.items()}


def primitive_to_data(primitive: Primitive) -> dict[str, Any]:
    common = {
        "id": primitive.id,
        "kind": primitive.kind,
        "visible": primitive.visible,
    }
    if isinstance(primitive, Point):
        return common | {
            "position": _vec3_to_data(primitive.position),
            "radius": primitive.radius,
            "color": _color_to_data(primitive.color),
        }
    if isinstance(primitive, Polyline):
        return common | {
            "points": [_vec3_to_data(point) for point in primitive.points],
            "width": primitive.width,
            "color": _color_to_data(primitive.color),
            "closed": primitive.closed,
        }
    if isinstance(primitive, Surface):
        return common | {
            "vertices": [_vec3_to_data(vertex) for vertex in primitive.vertices],
            "triangles": [list(triangle) for triangle in primitive.triangles],
            "color": _color_to_data(primitive.color),
        }
    if isinstance(primitive, Region):
        return common | {
            "boundary": [_vec3_to_data(point) for point in primitive.boundary],
            "color": _color_to_data(primitive.color),
        }
    if isinstance(primitive, VectorGlyph):
        return common | {
            "origin": _vec3_to_data(primitive.origin),
            "vector": _vec3_to_data(primitive.vector),
            "color": _color_to_data(primitive.color),
        }
    if isinstance(primitive, TextLabel):
        return common | {
            "text": primitive.text,
            "position": _vec3_to_data(primitive.position),
            "size": primitive.size,
            "color": _color_to_data(primitive.color),
        }
    if isinstance(primitive, Group):
        return common | {"children": list(primitive.children)}
    raise SceneSerializationError(f"unsupported primitive type: {type(primitive).__qualname__}")


def primitive_from_data(data: dict[str, Any]) -> Primitive:
    try:
        primitive_id = str(data["id"])
        kind = str(data["kind"])
    except KeyError as exc:
        raise SceneSerializationError(f"primitive missing field: {exc.args[0]}") from exc
    visible = bool(data.get("visible", True))

    if kind == "point":
        return Point(
            id=primitive_id,
            visible=visible,
            position=_vec3_from_data(data["position"]),
            radius=float(data.get("radius", 0.05)),
            color=_color_from_data(data["color"]),
        )
    if kind == "polyline":
        return Polyline(
            id=primitive_id,
            visible=visible,
            points=tuple(_vec3_from_data(point) for point in data["points"]),
            width=float(data.get("width", 0.02)),
            color=_color_from_data(data["color"]),
            closed=bool(data.get("closed", False)),
        )
    if kind == "surface":
        return Surface(
            id=primitive_id,
            visible=visible,
            vertices=tuple(_vec3_from_data(vertex) for vertex in data["vertices"]),
            triangles=tuple(tuple(int(index) for index in triangle) for triangle in data["triangles"]),
            color=_color_from_data(data["color"]),
        )
    if kind == "region":
        return Region(
            id=primitive_id,
            visible=visible,
            boundary=tuple(_vec3_from_data(point) for point in data["boundary"]),
            color=_color_from_data(data["color"]),
        )
    if kind == "vector_glyph":
        return VectorGlyph(
            id=primitive_id,
            visible=visible,
            origin=_vec3_from_data(data["origin"]),
            vector=_vec3_from_data(data["vector"]),
            color=_color_from_data(data["color"]),
        )
    if kind == "text":
        return TextLabel(
            id=primitive_id,
            visible=visible,
            text=str(data.get("text", "")),
            position=_vec3_from_data(data["position"]),
            size=float(data.get("size", 1.0)),
            color=_color_from_data(data["color"]),
        )
    if kind == "group":
        children = data.get("children", [])
        if not isinstance(children, list):
            raise SceneSerializationError("group children must be a list")
        return Group(id=primitive_id, visible=visible, children=tuple(str(child) for child in children))
    raise SceneSerializationError(f"unknown primitive kind: {kind}")


def timeline_to_data(timeline: Timeline) -> dict[str, Any]:
    return {
        "duration": timeline.duration,
        "tracks": [
            {
                "target_id": track.target_id,
                "property_path": track.property_path,
                "keyframes": [
                    {"time": keyframe.time, "value": _encode_value(keyframe.value)}
                    for keyframe in track.keyframes
                ],
            }
            for track in timeline.tracks
        ],
    }


def timeline_from_data(data: dict[str, Any]) -> Timeline:
    tracks = []
    for track_data in data.get("tracks", []):
        keyframes = tuple(
            Keyframe(float(keyframe["time"]), _decode_value(keyframe.get("value")))
            for keyframe in track_data.get("keyframes", [])
        )
        tracks.append(
            Track(
                target_id=str(track_data["target_id"]),
                property_path=str(track_data["property_path"]),
                keyframes=keyframes,
            )
        )
    return Timeline(duration=float(data.get("duration", 0.0)), tracks=tuple(tracks))


def scene_to_data(scene: Scene) -> dict[str, Any]:
    return {
        "schema": SCENE_SCHEMA,
        "version": SCENE_SCHEMA_VERSION,
        "primitives": [primitive_to_data(primitive) for primitive in scene.primitives],
        "timeline": timeline_to_data(scene.timeline),
    }


def scene_from_data(data: dict[str, Any]) -> Scene:
    if data.get("schema") != SCENE_SCHEMA:
        raise SceneSerializationError("not a Spectra scene document")
    if data.get("version") != SCENE_SCHEMA_VERSION:
        raise SceneSerializationError(
            f"unsupported Spectra scene version: {data.get('version')}"
        )
    primitives = data.get("primitives", [])
    if not isinstance(primitives, list):
        raise SceneSerializationError("scene primitives must be a list")
    timeline = data.get("timeline", {})
    if not isinstance(timeline, dict):
        raise SceneSerializationError("scene timeline must be an object")
    return Scene(
        primitives=tuple(primitive_from_data(primitive) for primitive in primitives),
        timeline=timeline_from_data(timeline),
    )


def scene_to_json(scene: Scene, *, indent: int | None = 2) -> str:
    return json.dumps(scene_to_data(scene), indent=indent, sort_keys=True)


def scene_from_json(payload: str) -> Scene:
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise SceneSerializationError("scene JSON root must be an object")
    return scene_from_data(data)
