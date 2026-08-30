from __future__ import annotations

from dataclasses import dataclass

from .animation import Timeline, get_property_path, replace_property_path
from .primitives import Group, Primitive


@dataclass(frozen=True, slots=True)
class Scene:
    primitives: tuple[Primitive, ...] = ()
    timeline: Timeline = Timeline()

    def __post_init__(self) -> None:
        ids = [primitive.id for primitive in self.primitives]
        if len(ids) != len(set(ids)):
            raise ValueError("Primitive ids must be unique within a Scene")

        primitive_by_id = {primitive.id: primitive for primitive in self.primitives}
        self._validate_groups(primitive_by_id)
        self._validate_timeline(primitive_by_id)

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

                # Apply every keyframe value to a temporary immutable primitive so
                # primitive/dataclass invariants (opacity, trim, scale, etc.) are
                # validated before a backend ever sees the scene.
                replace_property_path(primitive, track.property_path, value)

    def get(self, primitive_id: str) -> Primitive:
        for primitive in self.primitives:
            if primitive.id == primitive_id:
                return primitive
        raise KeyError(primitive_id)

    def sample(self, time: float) -> "Scene":
        """Evaluate the engine-owned timeline into a static renderer-neutral Scene."""
        if not self.timeline.tracks:
            return self

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
        )
