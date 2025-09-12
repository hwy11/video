"""Video clip generation and visual effects."""
from typing import List, Dict, Tuple, Optional

try:  # pragma: no cover
    from moviepy.editor import ImageClip, CompositeVideoClip
except Exception:  # ImportError if dependency missing
    ImageClip = None
    CompositeVideoClip = None


def _compute_output_resolution(
    timeline: List[Dict], configured: Optional[Tuple[int, int]]
) -> Tuple[int, int]:
    """Return the output resolution.

    Preference order: configured resolution -> first image size.
    """
    if configured and len(configured) == 2:
        return int(configured[0]), int(configured[1])

    # Fallback to the first image's size to keep consistency
    first_path = timeline[0]["image_path"]
    tmp = ImageClip(first_path)
    w, h = tmp.size
    tmp.close()  # free resources ASAP
    return int(w), int(h)


def create_video_clips(timeline: List[Dict], config: Dict):
    """Create moviepy clips for each timeline entry.

    Fixes garbled output by ensuring a constant output frame size using
    ``CompositeVideoClip``. Implements the desired effect: scale to 1.3x and
    slide in from the left for each image.
    """
    if ImageClip is None or CompositeVideoClip is None:
        raise RuntimeError("moviepy is not installed")

    kb_cfg = config.get("ken_burns_effect", {})
    zoom_factor = float(kb_cfg.get("zoom_factor", 1.3))
    # Determine the output resolution once
    configured_res = config.get("resolution")
    out_w, out_h = _compute_output_resolution(timeline, tuple(configured_res) if configured_res else None)

    clips = []

    for entry in timeline:
        duration = float(entry["duration_sec"]) or 0.001  # avoid zero duration

        img = ImageClip(entry["image_path"]).set_duration(duration)

        # Resize image to cover output frame while preserving aspect ratio
        src_w, src_h = img.size
        cover_scale = max(out_w / src_w, out_h / src_h)
        img = img.resize(cover_scale * zoom_factor)

        # Final composition with constant frame size
        # Slide in from left: x goes from -out_w -> 0 over clip duration
        def pos_func(t):
            progress = min(max(t / duration, 0.0), 1.0)
            x = -out_w + progress * out_w
            return (x, "center")

        composed = (
            CompositeVideoClip([img.set_position(pos_func)], size=(out_w, out_h))
            .set_duration(duration)
        )

        clips.append(composed)

        # Close the underlying ImageClip as it's now embedded in composed
        img.close()

    return clips
