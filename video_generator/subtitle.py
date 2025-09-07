"""Subtitle clip generation."""
from typing import List, Dict

try:  # pragma: no cover
    from moviepy.editor import TextClip
except Exception:  # ImportError if dependency missing
    TextClip = None


def create_subtitle_clips(timeline: List[Dict], config: Dict):
    """Create subtitle clips based on the media timeline.

    Returns a list of ``moviepy`` ``TextClip`` objects positioned and styled
    according to ``config``. If subtitles are disabled in ``config`` an empty
    list is returned.
    """
    if TextClip is None:
        raise RuntimeError("moviepy is not installed")

    style = config.get("subtitle_style", {})
    if not style.get("enabled", True):
        return []

    clips = []
    for entry in timeline:
        clip = TextClip(
            entry["sentence"],
            font=style.get("font"),
            fontsize=style.get("fontsize", 24),
            color=style.get("color", "white"),
            stroke_color=style.get("stroke_color"),
            stroke_width=style.get("stroke_width", 0),
        )
        clip = clip.set_start(entry["start_sec"]).set_duration(entry["end_sec"] - entry["start_sec"]).set_position(
            tuple(style.get("position", ("center", "bottom")))
        )
        clips.append(clip)
    return clips
