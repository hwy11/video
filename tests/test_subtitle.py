from video_generator import subtitle as subtitle_module


class DummyTextClip:
    def __init__(self, text, **kwargs):
        self.text = text
        self.kwargs = kwargs
        self.start = None
        self.duration = None
        self.position = None

    def set_start(self, s):
        self.start = s
        return self

    def set_duration(self, d):
        self.duration = d
        return self

    def set_position(self, pos):
        self.position = pos
        return self


def test_create_subtitle_clips(monkeypatch):
    monkeypatch.setattr(subtitle_module, "TextClip", DummyTextClip)
    timeline = [{"sentence": "hello", "start_sec": 0, "end_sec": 1}]
    config = {"subtitle_style": {"enabled": True, "position": ("center", "bottom")}}
    clips = subtitle_module.create_subtitle_clips(timeline, config)
    assert len(clips) == 1
    clip = clips[0]
    assert clip.text == "hello"
    assert clip.start == 0
    assert clip.duration == 1
    assert clip.position == ("center", "bottom")
