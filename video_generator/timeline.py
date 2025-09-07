"""Media timeline construction utilities."""
from pathlib import Path
from typing import List, Dict


def build_timeline(segments: List[Dict], image_folder: str) -> List[Dict]:
    """Map speech segments to images and build media timeline.

    Images are read from ``image_folder`` and sorted alphabetically. Each
    segment is paired with an image in order, producing a timeline entry
    containing the sentence, timestamps and image path.
    """
    raise NotImplementedError("Timeline building not implemented.")
