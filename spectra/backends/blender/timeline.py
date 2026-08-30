from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from spectra.backends.driver import BackendSession
from spectra.core.scene import Scene

from .incremental import IncrementalBlenderBackend, IncrementalBlenderHandle
from .backend import _require_blender


FrameHandler = Callable[..., None]


def frame_to_engine_time(
    frame: int,
    *,
    start_frame: int,
    fps: float,
    duration: float,
) -> float:
    """Map a Blender/UI frame to Spectra engine time and clamp to the timeline."""
    if fps <= 0.0:
        raise ValueError("fps must be positive")
    if duration < 0.0:
        raise ValueError("duration cannot be negative")
    seconds = (int(frame) - int(start_frame)) / float(fps)
    return min(max(seconds, 0.0), float(duration))


@dataclass
class BlenderTimelineController:
    """Bridge Blender playback controls to an engine-owned Spectra Timeline.

    Blender never evaluates scientific animation itself. Its frame counter is a
    transport signal. Every frame change is converted to engine time, then the
    source Scene is sampled by BackendSession and the resulting static snapshot
    is incrementally applied to native Blender objects.
    """

    session: BackendSession[IncrementalBlenderHandle]
    fps: float
    start_frame: int
    handler: FrameHandler
    bound: bool = True

    @classmethod
    def bind(
        cls,
        scene: Scene,
        *,
        fps: float = 30.0,
        start_frame: int = 1,
        set_blender_frame_range: bool = True,
        backend: IncrementalBlenderBackend | None = None,
    ) -> "BlenderTimelineController":
        if fps <= 0.0:
            raise ValueError("fps must be positive")
        bpy, _ = _require_blender()
        renderer = backend or IncrementalBlenderBackend()
        session = BackendSession.open(renderer, scene)

        controller_holder: dict[str, BlenderTimelineController] = {}

        def on_frame_change(native_scene: Any, _depsgraph: Any = None) -> None:
            controller = controller_holder.get("controller")
            if controller is None or not controller.bound:
                return
            controller.seek_frame(int(native_scene.frame_current))

        controller = cls(
            session=session,
            fps=float(fps),
            start_frame=int(start_frame),
            handler=on_frame_change,
        )
        controller_holder["controller"] = controller

        handlers = bpy.app.handlers.frame_change_post
        if on_frame_change not in handlers:
            handlers.append(on_frame_change)

        if set_blender_frame_range:
            native_scene = bpy.context.scene
            native_scene.frame_start = int(start_frame)
            duration = scene.timeline.duration
            frame_count = max(0, int(round(duration * fps)))
            native_scene.frame_end = int(start_frame) + frame_count
            if hasattr(native_scene.render, "fps"):
                whole_fps = max(1, int(round(fps)))
                native_scene.render.fps = whole_fps
                if hasattr(native_scene.render, "fps_base"):
                    native_scene.render.fps_base = whole_fps / float(fps)

        return controller

    @property
    def duration(self) -> float:
        return self.session.source_scene.timeline.duration

    @property
    def end_frame(self) -> int:
        return self.start_frame + max(0, int(round(self.duration * self.fps)))

    def seek_frame(self, frame: int) -> Scene:
        if not self.bound:
            raise RuntimeError("Blender timeline controller is closed")
        time = frame_to_engine_time(
            frame,
            start_frame=self.start_frame,
            fps=self.fps,
            duration=self.duration,
        )
        return self.session.seek(time)

    def seek_time(self, time: float) -> Scene:
        if not self.bound:
            raise RuntimeError("Blender timeline controller is closed")
        return self.session.seek(time)

    def close(self) -> None:
        if not self.bound:
            return
        bpy, _ = _require_blender()
        handlers = bpy.app.handlers.frame_change_post
        if self.handler in handlers:
            handlers.remove(self.handler)
        self.session.close()
        self.bound = False
