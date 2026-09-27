from core.models import Segment


def test_segment_duration():
    segment = Segment(2.0, 5.5, "你好", "Xin chào")
    assert segment.duration == 3.5


def test_segment_min_duration():
    segment = Segment(5.0, 5.0, "x")
    assert segment.duration == 0.05
