"""Command line entry point for the automated video generator."""
import yaml

from video_generator.asr import transcribe_audio
from video_generator.timeline import build_timeline
from video_generator.visual import create_video_clips
from video_generator.subtitle import create_subtitle_clips
from video_generator.render import render_video


def main() -> None:
    """Load configuration and run the generation pipeline."""
    with open("config.yaml", "r", encoding="utf-8") as cfg:
        config = yaml.safe_load(cfg)

    segments = transcribe_audio(config["input_audio"], config["whisper_model"])
    timeline = build_timeline(segments, config["image_folder"])
    video_clips = create_video_clips(timeline, config)
    subtitle_clips = create_subtitle_clips(timeline, config)
    render_video(video_clips, subtitle_clips, config)


if __name__ == "__main__":
    main()
