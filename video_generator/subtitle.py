"""Subtitle clip generation."""
from typing import List, Dict


def create_subtitle_clips(timeline: List[Dict], config: Dict):
    """Create subtitle clips based on the media timeline.

    Returns a list of ``moviepy`` ``TextClip`` objects positioned and styled
    according to ``config``.
    """
    raise NotImplementedError("Subtitle creation not implemented.")
