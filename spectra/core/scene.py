from __future__ import annotations

from dataclasses import dataclass

from .animation import Timeline, get_property_path, replace_property_path
from .coordinates import CoordinateFrame3D, WORLD_FRAME
from .materials import Material
from .primitives import Camera, Group, Primitive


@dataclass(frozen=True, slots=True)
class Scene:
    primitives: tuple[Primitive, ...] = ()
    timeline: Timeline = Timeline()
    frame: CoordinateFrame3D = WORLD_FRAME
    active_camera_id: str | None = None
    materials: tuple[Material, ...] = ()

    def __post_init__(self) -> None:
        ids = [primitive.id for primitive in self.primitives]
        if len(ids) != len(set(ids)):
            raise ValueError("Primitive ids must be unique within a Scene")

        material_ids = [material.id for material in self.materials]
        if len(material_ids) != len(set(material_ids)):
            raise ValueError("Material ids must be unique within a Scene")

        primitive_by_id = {primitive.id: primitive for primitive in self.primitives}
        material_by_id = {material.id: material for material in self.materials}
        self._validate_material_references(material_by_id)
        self._validate_groups(primitive_by_id)
        self._validate_camera(primitive_by_id)
        self._validate_timeline(primitive_by_id)

    def _validate_material_references(self, material_by_id: dict[str, Material]) -> None:
        for primitive in self.primitives:
            if primitive.material_id is not None and primitive.material_id not in material_by_id:
                raise ValueError(
                    f"Primitive '{primitive.id}' references unknown material "
                    f"'{primitive.material_id}'"
                )

    def _validate_groups(self, primitive_by_id: dict[str, Primitive]) -> None:
        groups = {
            primitive.id: primitive
            for primitive in self.primitives
            if isinstance(primitive, Group)
        }
        for group in groups.values():
            if len(group.children) != len(set(group.children)):
                raise ValueError(f"Group '{group.id}' contains duplicate child ids")
            for child_id in group.children:
                if child_id not in primitive_by_id:
                    raise ValueError(
                        f"Group '{group.id}' references unknown primitive '{child_id}'"
                    )
                if child_id == group.id:
                    raise ValueError(f"Group '{group.id}' cannot contain itself")

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(group_id: str) -> None:
            if group_id in visited:
                return
            if group_id in visiting:
                raise ValueError("Scene group hierarchy contains a cycle")
            visiting.add(group_id)
            for child_id in groups[group_id].children:
                if child_id in groups:
                    visit(child_id)
            visiting.remove(group_id)
            visited.add(group_id)

        for group_id in groups:
            visit(group_id)

    def _validate_camera(self, primitive_by_id: dict[str, Primitive]) -> None:
        if self.active_camera_id is None:
            return
        try:
            camera = primitive_by_id[self.active_camera_id]
        except KeyError as exc:
            raise ValueError(
                f"active camera references unknown primitive '{self.active_camera_id}'"
            ) from exc
        if not isinstance(camera, Camera):
            raise ValueError("active_camera_id must reference a Camera primitive")

    def _validate_timeline(self, primitive_by_id: dict[str, Primitive]) -> None:
        for track in self.timeline.tracks:
            try:
                primitive = primitive_by_id[track.target_id]
            except KeyError as exc:
                raise ValueError(
                    f"Animation track references unknown primitive '{track.target_id}'"
                ) from exc

            current_value = get_property_path(primitive, track.property_path)
            for keyframe in track.keyframes:
                value = keyframe.value
                if isinstance(current_value, bool):
                    if not isinstance(value, bool):
                        raise TypeError(
                            f"Animation value for {track.target_id}.{track.property_path} must be bool"
                        )
                    if keyframe is not track.keyframes[-1] and keyframe.interpolation != "step":
                        raise TypeError("boolean animation requires step interpolation")
                elif isinstance(current_value, float):
                    if isinstance(value, bool) or not isinstance(value, (int, float)):
                        raise TypeError(
                            f"Animation value for {track.target_id}.{track.property_path} must be numeric"
                        )
                elif not isinstance(value, type(current_value)):
                    raise TypeError(
                        f"Animation value type mismatch for {track.target_id}.{track.property_path}: "
                        f"expected {type(current_value).__qualname__}, got {type(value).__qualname__}"
                    )

                replace_property_path(primitive, track.property_path, value)

    def get(self, primitive_id: str) -> Primitive:
        for primitive in self.primitives:
            if primitive.id == primitive_id:
                return primitive
        raise KeyError(primitive_id)

    def material(self, material_id: str) -> Material:
        for material in self.materials:
            if material.id == material_id:
                return material
        raise KeyError(material_id)

    def active_camera(self) -> Camera | None:
        if self.active_camera_id is None:
            return None
        camera = self.get(self.active_camera_id)
        assert isinstance(camera, Camera)
        return camera

    def sample(self, time: float) -> "Scene":
        """Evaluate the engine-owned timeline into a static renderer-neutral Scene."""
        if not self.timeline.tracks:
            if self.timeline.duration == 0.0:
                return self
            return Scene(
                primitives=self.primitives,
                timeline=Timeline(),
                frame=self.frame,
                active_camera_id=self.active_camera_id,
                materials=self.materials,
            )

        updates = self.timeline.evaluate(time)
        primitive_by_id = {primitive.id: primitive for primitive in self.primitives}
        for (target_id, property_path), value in updates.items():
            primitive_by_id[target_id] = replace_property_path(
                primitive_by_id[target_id],
                property_path,
                value,
            )

        return Scene(
            primitives=tuple(primitive_by_id[primitive.id] for primitive in self.primitives),
            timeline=Timeline(),
            frame=self.frame,
            active_camera_id=self.active_camera_id,
            materials=self.materials,
        )
