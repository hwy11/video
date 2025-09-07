from video_generator import render as render_module


class DummyClip:
    def __init__(self):
        self.audio = None
        self.written = None

    def set_audio(self, audio):
        self.audio = audio
        return self

    def write_videofile(self, filename, fps, codec, audio_codec):
        self.written = filename


class DummyAudioClip:
    pass


def test_render_video(monkeypatch):
    video_clip = DummyClip()
    subtitle_clip = DummyClip()

    monkeypatch.setattr(
        render_module, "concatenate_videoclips", lambda clips: clips[0]
    )
    monkeypatch.setattr(
        render_module, "CompositeVideoClip", lambda clips: clips[0]
    )
    monkeypatch.setattr(
        render_module, "AudioFileClip", lambda path: DummyAudioClip()
    )

    render_module.render_video(
        [video_clip], [subtitle_clip], {"input_audio": "in.mp3", "output_file": "out.mp4", "fps": 24}
    )
    assert video_clip.audio is not None
    assert video_clip.written == "out.mp4"
