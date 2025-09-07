from pathlib import Path
import base64

from video_generator.timeline import build_timeline


PNG_DATA = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGNgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII="
)


def test_build_timeline_maps_segments_to_images(tmp_path):
    for i in range(2):
        (tmp_path / f"{i}.png").write_bytes(PNG_DATA)
    segments = [
        {"sentence": "a", "start_sec": 0, "end_sec": 1},
        {"sentence": "b", "start_sec": 1, "end_sec": 2},
    ]
    timeline = build_timeline(segments, str(tmp_path))
    assert len(timeline) == 2
    assert Path(timeline[0]["image_path"]).name == "0.png"
    assert Path(timeline[1]["image_path"]).name == "1.png"
    assert timeline[0]["duration_sec"] == 1
