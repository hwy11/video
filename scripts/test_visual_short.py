import os
import json
import yaml
from moviepy.editor import concatenate_videoclips
from video_generator.visual import create_video_clips


def main():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    with open('file_timeline/asr_result_20250910_224927_timeline.json', 'r', encoding='utf-8') as f:
        timeline = json.load(f)

    for e in timeline:
        e['image_path'] = e['image_path'].replace('video/video_generator/', 'video_generator/')

    short = timeline[:5]
    print('Entries:', len(short))

    clips = create_video_clips(short, config)
    final = concatenate_videoclips(clips, method='compose')

    out = 'visual_test_short.mp4'
    final.write_videofile(
        out,
        fps=config.get('fps', 30),
        codec='libx264',
        audio=False,
        ffmpeg_params=['-crf', '22', '-pix_fmt', 'yuv420p'],
    )

    print(out, '->', os.path.getsize(out), 'bytes')


if __name__ == '__main__':
    main()

