from __future__ import annotations

from dataclasses import dataclass
import math
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
    playback_duration: float | None = None,
) -> float:
    """Map Blender transport frames to Spectra scientific time.

    ``duration`` is always the authoritative Spectra/scientific Timeline duration.
    ``playback_duration`` is optional presentation transport time. When omitted,
    the historical 1 Blender second == 1 scientific second behavior is preserved.

    A separate playback duration lets nanosecond Maxwell evolution or very slow
    scientific processes be shown over a human-readable video duration without
    changing, resampling, or relabeling the scientific Timeline itself.
    """
    if not math.isfinite(fps) or fps <= 0.0:
        raise ValueError("fps must be finite and positive")
    if not math.isfinite(duration) or duration < 0.0:
        raise ValueError("duration must be a finite non-negative value")
    if playback_duration is not None:
        if not math.isfinite(playback_duration):
            raise ValueError("playback_duration must be finite")
        if duration > 0.0 and playback_duration <= 0.0:
            raise ValueError("playback_duration must be positive for an animated Scene")
        if duration == 0.0 and playback_duration < 0.0:
            raise ValueError("playback_duration cannot be negative")

    if duration == 0.0:
        return 0.0

    transport_duration = duration if playback_duration is None else playback_duration
    presentation_seconds = (int(frame) - int(start_frame)) / float(fps)
    if transport_duration <= 0.0:
        return 0.0
    normalized = presentation_seconds / transport_duration
    return min(max(normalized * duration, 0.0), float(duration))


@dataclass
class BlenderTimelineController:
    """Bridge Blender playback controls to an engine-owned Spectra Timeline.

    Blender never evaluates scientific animation itself. Its frame counter is a
    transport signal. Every frame change is converted to engine time, then the
    source Scene is sampled by BackendSession and the resulting static snapshot
    is incrementally applied to native Blender objects.

    ``playback_duration`` belongs to presentation/transport. ``duration`` remains
    the scientific Timeline duration and is never rewritten to make an animation
    visually slower or faster.

    The new field is deliberately appended after the legacy constructor fields so
    older positional construction keeps its historical argument order. Product
    code should still prefer ``bind()``.
    """

    session: BackendSession[IncrementalBlenderHandle]
    fps: float
    start_frame: int
    handler: FrameHandler
    bound: bool = True
    playback_duration: float | None = None

    @classmethod
    def bind(
        cls,
        scene: Scene,
        *,
        fps: float = 30.0,
        start_frame: int = 1,
        playback_duration: float | None = None,
        set_blender_frame_range: bool = True,
        backend: IncrementalBlenderBackend | None = None,
    ) -> "BlenderTimelineController":
        if not math.isfinite(fps) or fps <= 0.0:
            raise ValueError("fps must be finite and positive")
        scientific_duration = scene.timeline.duration
        if playback_duration is None:
            transport_duration = scientific_duration
        else:
            if not math.isfinite(playback_duration):
                raise ValueError("playback_duration must be finite")
            if scientific_duration > 0.0 and playback_duration <= 0.0:
                raise ValueError("playback_duration must be positive for an animated Scene")
            if scientific_duration == 0.0 and playback_duration < 0.0:
                raise ValueError("playback_duration cannot be negative")
            transport_duration = float(playback_duration)

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
            playback_duration=transport_duration,
        )
        controller_holder["controller"] = controller

        handlers = bpy.app.handlers.frame_change_post
        if on_frame_change not in handlers:
            handlers.append(on_frame_change)

        if set_blender_frame_range:
            native_scene = bpy.context.scene
            native_scene.frame_start = int(start_frame)
            frame_count = max(0, int(round(transport_duration * fps)))
            native_scene.frame_end = int(start_frame) + frame_count
            if hasattr(native_scene.render, "fps"):
                whole_fps = max(1, int(round(fps)))
                native_scene.render.fps = whole_fps
                if hasattr(native_scene.render, "fps_base"):
                    native_scene.render.fps_base = whole_fps / float(fps)

        return controller

    @property
    def duration(self) -> float:
        """Authoritative Spectra/scientific Timeline duration."""
        return self.session.source_scene.timeline.duration

    @property
    def transport_duration(self) -> float:
        """Human-facing playback duration, defaulting to historical 1:1 time."""
        return self.duration if self.playback_duration is None else self.playback_duration

    @property
    def end_frame(self) -> int:
        return self.start_frame + max(0, int(round(self.transport_duration * self.fps)))

    def seek_frame(self, frame: int) -> Scene:
        if not self.bound:
            raise RuntimeError("Blender timeline controller is closed")
        time = frame_to_engine_time(
            frame,
            start_frame=self.start_frame,
            fps=self.fps,
            duration=self.duration,
            playback_duration=self.playback_duration,
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
