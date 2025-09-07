"""Media timeline construction utilities."""
from pathlib import Path
from typing import List, Dict


def build_timeline(segments: List[Dict], image_folder: str) -> List[Dict]:
    """Map speech segments to images and build the media timeline.

    Images are read from ``image_folder`` and sorted alphabetically. Each
    segment is paired with an image in order, producing a timeline entry
    containing the sentence, timestamps and image path.

    If there are more segments than images, images are reused in a cycle.
    """
    images = sorted(Path(image_folder).glob("*"))
    if not images:
        raise FileNotFoundError("No images found in image folder")

    timeline: List[Dict] = []
    for idx, seg in enumerate(segments):
        image_path = str(images[idx % len(images)])
        timeline.append(
            {
                "sentence": seg["sentence"],
                "start_sec": seg["start_sec"],
                "end_sec": seg["end_sec"],
                "duration_sec": seg["end_sec"] - seg["start_sec"],
                "image_path": image_path,
            }
        )
    return timeline
