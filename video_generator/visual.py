"""Video clip generation and visual effects."""
from typing import List, Dict, Tuple, Optional
import random

try:  # pragma: no cover
    from moviepy.editor import ImageClip, CompositeVideoClip, VideoClip
except Exception:  # ImportError if dependency missing
    ImageClip = None
    CompositeVideoClip = None
    VideoClip = None


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

    # Slide-in configuration (fast by default)
    slide_cfg = config.get("slide_in", {})
    slide_enabled = slide_cfg.get("enabled", True)
    slide_ratio = float(slide_cfg.get("ratio", 0.25))
    slide_ratio = max(0.05, min(slide_ratio, 1.0))
    direction_cfg = slide_cfg.get("direction", "random")  # left/right/top/bottom/random
    if isinstance(direction_cfg, str):
        direction_cfg = direction_cfg.lower()
    seed = slide_cfg.get("seed")
    if seed is not None:
        random.seed(int(seed))

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

        # Compute allowed offsets so the frame is always fully covered
        iw, ih = img.size
        min_x, max_x = out_w - iw, 0
        min_y, max_y = out_h - ih, 0

        # Choose direction per clip
        if slide_enabled:
            if direction_cfg == "random":
                direction = random.choice(["left", "right", "top", "bottom"])  # noqa: S311
            else:
                direction = direction_cfg
        else:
            direction = "none"

        if direction == "left":
            start_x, end_x = min_x, 0
            start_y, end_y = "center", "center"
        elif direction == "right":
            start_x, end_x = 0, min_x
            start_y, end_y = "center", "center"
        elif direction == "top":
            start_x, end_x = "center", "center"
            start_y, end_y = min_y, 0
        elif direction == "bottom":
            start_x, end_x = "center", "center"
            start_y, end_y = 0, min_y
        else:
            start_x = end_x = "center"
            start_y = end_y = "center"

        move_duration = duration * slide_ratio

        def lerp(a, b, p):
            return a + (b - a) * p

        def pos_func(t):
            if move_duration <= 0:
                p = 1.0
            else:
                p = min(max(t / move_duration, 0.0), 1.0)
                # ease-out for snappier feel
                p = 1 - (1 - p) * (1 - p)

            if start_x == "center":
                x = "center"
            else:
                x = lerp(start_x, end_x, p)
            if start_y == "center":
                y = "center"
            else:
                y = lerp(start_y, end_y, p)
            return (x, y)

        composed = (
            CompositeVideoClip([img.set_position(pos_func)], size=(out_w, out_h))
            .set_duration(duration)
        )

        clips.append(composed)

        # Close the underlying ImageClip as it's now embedded in composed
        img.close()

    return clips


def venetian_blinds_transition(
    clip_out,
    clip_in,
    duration: float = 0.6,
    blinds: int = 10,
    orientation: str = "vertical",
):
    """Create a venetian blinds transition from clip_out to clip_in.

    This returns a CompositeVideoClip of `duration` where `clip_in` is revealed
    in multiple stripes. Both clips must have the same size.

    - orientation="vertical": open left→right in vertical stripes
    - orientation="horizontal": open top→bottom in horizontal stripes
    """
    if VideoClip is None:
        raise RuntimeError("moviepy is not installed")

    w, h = clip_out.size
    assert clip_in.size == (w, h), "Transition clips must have equal size"

    a = clip_out.subclip(max(0, clip_out.duration - duration), clip_out.duration)
    b = clip_in.subclip(0, min(duration, clip_in.duration))

    def make_frame(t):
        p = np.clip(t / max(duration, 1e-6), 0.0, 1.0)
        mask = np.zeros((h, w), dtype=float)
        if orientation == "horizontal":
            # Reveal rows
            for i in range(blinds):
                y0 = int(i * h / blinds)
                y1 = int(y0 + p * h / blinds)
                mask[y0:y1, :] = 1.0
        else:
            # Reveal columns
            for i in range(blinds):
                x0 = int(i * w / blinds)
                x1 = int(x0 + p * w / blinds)
                mask[:, x0:x1] = 1.0
        return mask

    m = VideoClip(make_frame=make_frame, ismask=True, duration=duration)
    b_masked = b.set_mask(m)
    return CompositeVideoClip([a, b_masked], size=(w, h)).set_duration(duration)
