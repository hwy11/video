"""Video clip generation and visual effects."""
from typing import List, Dict

try:  # pragma: no cover
    from moviepy.editor import ImageClip, vfx
except Exception:  # ImportError if dependency missing
    ImageClip = None
    vfx = None


def create_video_clips(timeline: List[Dict], config: Dict):
    """Create ``moviepy`` clips for each timeline entry.

    A simple Ken Burns style zoom is applied when enabled in ``config``. The
    resulting clips are resized to the desired resolution and have durations
    matching their corresponding timeline entries.
    """
    if ImageClip is None or vfx is None:
        raise RuntimeError("moviepy is not installed")

    clips = []
    kb_cfg = config.get("ken_burns_effect", {})
    zoom_factor = kb_cfg.get("zoom_factor", 1.0)
    resolution = tuple(config.get("resolution", [])) or None
    for entry in timeline:
        clip = ImageClip(entry["image_path"]).set_duration(entry["duration_sec"])
        if kb_cfg.get("enabled", False):
            clip = clip.fx(
                vfx.resize,
                lambda t: 1 + (zoom_factor - 1) * (t / entry["duration_sec"]),
            )
        if resolution:
            clip = clip.resize(newsize=resolution)
        clips.append(clip)
    return clips
