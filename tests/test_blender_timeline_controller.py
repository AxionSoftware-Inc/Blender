import pytest

from spectra.backends import frame_to_engine_time


def test_frame_to_engine_time_maps_and_clamps_transport_frames() -> None:
    assert frame_to_engine_time(1, start_frame=1, fps=30.0, duration=2.0) == pytest.approx(0.0)
    assert frame_to_engine_time(31, start_frame=1, fps=30.0, duration=2.0) == pytest.approx(1.0)
    assert frame_to_engine_time(61, start_frame=1, fps=30.0, duration=2.0) == pytest.approx(2.0)
    assert frame_to_engine_time(-100, start_frame=1, fps=30.0, duration=2.0) == pytest.approx(0.0)
    assert frame_to_engine_time(500, start_frame=1, fps=30.0, duration=2.0) == pytest.approx(2.0)


def test_frame_to_engine_time_validates_transport_parameters() -> None:
    with pytest.raises(ValueError, match="fps"):
        frame_to_engine_time(1, start_frame=1, fps=0.0, duration=1.0)
    with pytest.raises(ValueError, match="duration"):
        frame_to_engine_time(1, start_frame=1, fps=30.0, duration=-1.0)
