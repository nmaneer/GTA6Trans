from gta6sub.config import _merge
from gta6sub.ocr import join_lines, normalize
from gta6sub.stabilizer import SubtitleStabilizer


def box(x, y, w=100, h=20):
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]


def test_join_lines_orders_rows_and_filters_conf():
    results = [
        (box(200, 50), "the car.", 0.9),
        (box(0, 10), "LUCIA: Get in", 0.95),
        (box(0, 50), "and start", 0.9),
        (box(0, 90), "x#", 0.2),
    ]
    assert join_lines(results, 0.6) == "LUCIA: Get in and start the car."


def test_normalize_spacing():
    assert normalize("Hey  ,  you !") == "Hey, you!"


def test_stabilizer_waits_and_dedupes():
    s = SubtitleStabilizer(stable_frames=2)
    assert s.feed("Where's the money") is None
    assert s.feed("Where's the money?") == "Where's the money?"
    assert s.feed("Where's the money?") is None          # still on screen
    assert s.feed("Wheres the rnoney?") is None          # OCR noise, same line
    assert s.feed("Drive, drive!") is None
    assert s.feed("Drive, drive!") == "Drive, drive!"


def test_stabilizer_repeat_after_clear():
    s = SubtitleStabilizer(stable_frames=1)
    assert s.feed("Go!!") == "Go!!"
    assert s.feed("") is None
    assert s.feed("Go!!") == "Go!!"


def test_merge_config():
    out = _merge({"a": {"b": 1, "c": 2}}, {"a": {"c": 3}})
    assert out == {"a": {"b": 1, "c": 3}}
