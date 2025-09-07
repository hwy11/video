"""Final video composition and rendering."""

from typing import List

try:  # pragma: no cover
    from moviepy.editor import AudioFileClip, CompositeVideoClip, concatenate_videoclips
except Exception:  # ImportError if dependency missing
    AudioFileClip = None
    CompositeVideoClip = None
    concatenate_videoclips = None


def render_video(video_clips: List, subtitle_clips: List, config):
    """Compose the video, overlay subtitles and render the final output.

    Parameters
    ----------
    video_clips:
        List of processed visual clips.
    subtitle_clips:
        List of subtitle overlays.
    config:
        Global configuration dictionary.
    """
    if not all([AudioFileClip, CompositeVideoClip, concatenate_videoclips]):
        raise RuntimeError("moviepy is not installed")

    audio = AudioFileClip(config["input_audio"])
    base_video = concatenate_videoclips(video_clips)
    final = CompositeVideoClip([base_video] + subtitle_clips).set_audio(audio)
    final.write_videofile(
        config["output_file"],
        fps=config.get("fps", 24),
        codec="libx264",
        audio_codec="aac",
    )
