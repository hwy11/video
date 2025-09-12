"""Standalone script to test visual module with timeline JSON file."""
import json
import yaml
from video_generator.visual import create_video_clips

try:
    from moviepy.editor import concatenate_videoclips
except Exception:
    concatenate_videoclips = None


def main():
    """Load timeline from JSON and create video with visual effects."""
    # Load config
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    # Load timeline from JSON file
    timeline_file = "file_timeline/asr_result_20250910_224927_timeline.json"
    with open(timeline_file, "r", encoding="utf-8") as f:
        timeline = json.load(f)
    
    # Fix image paths in timeline
    for entry in timeline:
        # Convert absolute paths to relative paths from project root
        entry["image_path"] = entry["image_path"].replace("video/video_generator/", "video_generator/")
    
    print(f"Loaded {len(timeline)} timeline entries from {timeline_file}")
    
    # Create video clips with visual effects
    print("Creating video clips with Ken Burns effect...")
    clips = create_video_clips(timeline, config)
    
    print(f"Created {len(clips)} video clips")
    
    if concatenate_videoclips is None:
        raise RuntimeError("moviepy is not installed")
    
    # Concatenate all clips
    print("Concatenating clips...")
    final_video = concatenate_videoclips(clips)
    
    # Set output filename
    output_path = "visual_test_output.mp4"
    
    # Write video file
    print(f"Writing video to {output_path}...")
    final_video.write_videofile(
        output_path,
        fps=config.get("fps", 24),
        codec='libx264',
        audio_codec='aac'
    )
    
    print(f"Video successfully created: {output_path}")


if __name__ == "__main__":
    main()