from __future__ import annotations

import json
from typing import Any

from .animation import Keyframe, Timeline, Track
from .coordinates import CoordinateFrame3D, WORLD_FRAME
from .primitives import Camera, Group, Point, Polyline, Primitive, Region, Surface, TextLabel, VectorGlyph
from .scene import Scene
from .transforms import Quaternion, Transform3D
from .types import Color, Vec2, Vec3


SCENE_SCHEMA = "spectra.scene"
SCENE_SCHEMA_VERSION = 2
SUPPORTED_SCENE_SCHEMA_VERSIONS = {1, 2}


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


def _quaternion_to_data(value: Quaternion) -> list[float]:
    return [value.w, value.x, value.y, value.z]


def _quaternion_from_data(value: Any) -> Quaternion:
    if not isinstance(value, list) or len(value) != 4:
        raise SceneSerializationError("expected a four-component quaternion")
    return Quaternion(*(float(component) for component in value))


def _transform_to_data(value: Transform3D) -> dict[str, Any]:
    return {
        "translation": _vec3_to_data(value.translation),
        "rotation": _quaternion_to_data(value.rotation),
        "scale": _vec3_to_data(value.scale),
    }


def _transform_from_data(value: Any) -> Transform3D:
    if value is None:
        return Transform3D()
    if not isinstance(value, dict):
        raise SceneSerializationError("primitive transform must be an object")
    return Transform3D(
        translation=_vec3_from_data(value.get("translation", [0.0, 0.0, 0.0])),
        rotation=_quaternion_from_data(value.get("rotation", [1.0, 0.0, 0.0, 0.0])),
        scale=_vec3_from_data(value.get("scale", [1.0, 1.0, 1.0])),
    )


def _frame_to_data(frame: CoordinateFrame3D) -> dict[str, Any]:
    return {
        "origin": _vec3_to_data(frame.origin),
        "basis_x": _vec3_to_data(frame.basis_x),
        "basis_y": _vec3_to_data(frame.basis_y),
        "basis_z": _vec3_to_data(frame.basis_z),
    }


def _frame_from_data(value: Any) -> CoordinateFrame3D:
    if value is None:
        return WORLD_FRAME
    if not isinstance(value, dict):
        raise SceneSerializationError("scene frame must be an object")
    return CoordinateFrame3D(
        origin=_vec3_from_data(value.get("origin", [0.0, 0.0, 0.0])),
        basis_x=_vec3_from_data(value.get("basis_x", [1.0, 0.0, 0.0])),
        basis_y=_vec3_from_data(value.get("basis_y", [0.0, 1.0, 0.0])),
        basis_z=_vec3_from_data(value.get("basis_z", [0.0, 0.0, 1.0])),
    )


def _encode_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Vec2):
        return {"$type": "vec2", "value": [value.x, value.y]}
    if isinstance(value, Vec3):
        return {"$type": "vec3", "value": _vec3_to_data(value)}
    if isinstance(value, Color):
        return {"$type": "color", "value": _color_to_data(value)}
    if isinstance(value, Quaternion):
        return {"$type": "quaternion", "value": _quaternion_to_data(value)}
    if isinstance(value, Transform3D):
        return {"$type": "transform3d", "value": _transform_to_data(value)}
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
    if marker == "quaternion":
        return _quaternion_from_data(value.get("value"))
    if marker == "transform3d":
        return _transform_from_data(value.get("value"))
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
        "opacity": primitive.opacity,
        "transform": _transform_to_data(primitive.transform),
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
            "trim_start": primitive.trim_start,
            "trim_end": primitive.trim_end,
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
    if isinstance(primitive, Camera):
        return common | {
            "projection": primitive.projection,
            "fov_y_radians": primitive.fov_y_radians,
            "orthographic_scale": primitive.orthographic_scale,
            "near_clip": primitive.near_clip,
            "far_clip": primitive.far_clip,
        }
    raise SceneSerializationError(f"unsupported primitive type: {type(primitive).__qualname__}")


def _primitive_common(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(data["id"]),
        "visible": bool(data.get("visible", True)),
        "opacity": float(data.get("opacity", 1.0)),
        "transform": _transform_from_data(data.get("transform")),
    }


def primitive_from_data(data: dict[str, Any]) -> Primitive:
    try:
        kind = str(data["kind"])
        common = _primitive_common(data)
    except KeyError as exc:
        raise SceneSerializationError(f"primitive missing field: {exc.args[0]}") from exc

    if kind == "point":
        return Point(
            **common,
            position=_vec3_from_data(data["position"]),
            radius=float(data.get("radius", 0.05)),
            color=_color_from_data(data["color"]),
        )
    if kind == "polyline":
        return Polyline(
            **common,
            points=tuple(_vec3_from_data(point) for point in data["points"]),
            width=float(data.get("width", 0.02)),
            color=_color_from_data(data["color"]),
            closed=bool(data.get("closed", False)),
            trim_start=float(data.get("trim_start", 0.0)),
            trim_end=float(data.get("trim_end", 1.0)),
        )
    if kind == "surface":
        return Surface(
            **common,
            vertices=tuple(_vec3_from_data(vertex) for vertex in data["vertices"]),
            triangles=tuple(tuple(int(index) for index in triangle) for triangle in data["triangles"]),
            color=_color_from_data(data["color"]),
        )
    if kind == "region":
        return Region(
            **common,
            boundary=tuple(_vec3_from_data(point) for point in data["boundary"]),
            color=_color_from_data(data["color"]),
        )
    if kind == "vector_glyph":
        return VectorGlyph(
            **common,
            origin=_vec3_from_data(data["origin"]),
            vector=_vec3_from_data(data["vector"]),
            color=_color_from_data(data["color"]),
        )
    if kind == "text":
        return TextLabel(
            **common,
            text=str(data.get("text", "")),
            position=_vec3_from_data(data["position"]),
            size=float(data.get("size", 1.0)),
            color=_color_from_data(data["color"]),
        )
    if kind == "group":
        children = data.get("children", [])
        if not isinstance(children, list):
            raise SceneSerializationError("group children must be a list")
        return Group(**common, children=tuple(str(child) for child in children))
    if kind == "camera":
        return Camera(
            **common,
            projection=str(data.get("projection", "perspective")),  # type: ignore[arg-type]
            fov_y_radians=float(data.get("fov_y_radians", 0.8726646259971648)),
            orthographic_scale=float(data.get("orthographic_scale", 10.0)),
            near_clip=float(data.get("near_clip", 0.01)),
            far_clip=float(data.get("far_clip", 10000.0)),
        )
    raise SceneSerializationError(f"unknown primitive kind: {kind}")


def timeline_to_data(timeline: Timeline) -> dict[str, Any]:
    return {
        "duration": timeline.duration,
        "tracks": [
            {
                "target_id": track.target_id,
                "property_path": track.property_path,
                "keyframes": [
                    {
                        "time": keyframe.time,
                        "value": _encode_value(keyframe.value),
                        "interpolation": keyframe.interpolation,
                    }
                    for keyframe in track.keyframes
                ],
            }
            for track in timeline.tracks
        ],
    }


def timeline_from_data(data: dict[str, Any]) -> Timeline:
    tracks = []
    for track_data in data.get("tracks", []):
        keyframes = []
        for keyframe in track_data.get("keyframes", []):
            decoded = _decode_value(keyframe.get("value"))
            default_interpolation = "step" if isinstance(decoded, bool) else "linear"
            keyframes.append(
                Keyframe(
                    float(keyframe["time"]),
                    decoded,
                    str(keyframe.get("interpolation", default_interpolation)),  # type: ignore[arg-type]
                )
            )
        tracks.append(
            Track(
                target_id=str(track_data["target_id"]),
                property_path=str(track_data["property_path"]),
                keyframes=tuple(keyframes),
            )
        )
    return Timeline(duration=float(data.get("duration", 0.0)), tracks=tuple(tracks))


def scene_to_data(scene: Scene) -> dict[str, Any]:
    return {
        "schema": SCENE_SCHEMA,
        "version": SCENE_SCHEMA_VERSION,
        "frame": _frame_to_data(scene.frame),
        "active_camera_id": scene.active_camera_id,
        "primitives": [primitive_to_data(primitive) for primitive in scene.primitives],
        "timeline": timeline_to_data(scene.timeline),
    }


def scene_from_data(data: dict[str, Any]) -> Scene:
    if data.get("schema") != SCENE_SCHEMA:
        raise SceneSerializationError("not a Spectra scene document")
    version = data.get("version")
    if version not in SUPPORTED_SCENE_SCHEMA_VERSIONS:
        raise SceneSerializationError(f"unsupported Spectra scene version: {version}")
    primitives = data.get("primitives", [])
    if not isinstance(primitives, list):
        raise SceneSerializationError("scene primitives must be a list")
    timeline = data.get("timeline", {})
    if not isinstance(timeline, dict):
        raise SceneSerializationError("scene timeline must be an object")
    active_camera_id = data.get("active_camera_id")
    if active_camera_id is not None:
        active_camera_id = str(active_camera_id)
    return Scene(
        primitives=tuple(primitive_from_data(primitive) for primitive in primitives),
        timeline=timeline_from_data(timeline),
        frame=_frame_from_data(data.get("frame")),
        active_camera_id=active_camera_id,
    )


def scene_to_json(scene: Scene, *, indent: int | None = 2) -> str:
    return json.dumps(scene_to_data(scene), indent=indent, sort_keys=True)


def scene_from_json(payload: str) -> Scene:
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise SceneSerializationError("scene JSON root must be an object")
    return scene_from_data(data)
