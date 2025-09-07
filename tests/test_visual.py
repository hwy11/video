import base64

from video_generator import visual as visual_module


PNG_DATA = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAAAAAClX0ZFAAAADUlEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
)


class DummyClip:
    def __init__(self, path):
        self.path = path
        self.duration = 0
        self.size = (0, 0)
        self.applied_resize = None

    def set_duration(self, d):
        self.duration = d
        return self

    def fx(self, func, resize_func):
        self.applied_resize = resize_func
        return func(self)

    def resize(self, newsize=None):
        self.size = newsize
        return self


class DummyVFX:
    @staticmethod
    def resize(clip):
        return clip


def test_create_video_clips_returns_clips(tmp_path, monkeypatch):
    img_path = tmp_path / "img.png"
    img_path.write_bytes(PNG_DATA)
    monkeypatch.setattr(visual_module, "ImageClip", lambda path: DummyClip(path))
    monkeypatch.setattr(visual_module, "vfx", DummyVFX)

    timeline = [{"image_path": str(img_path), "duration_sec": 2}]
    config = {"ken_burns_effect": {"enabled": False}, "resolution": [100, 100]}
    clips = visual_module.create_video_clips(timeline, config)
    assert len(clips) == 1
    clip = clips[0]
    assert clip.duration == 2
    assert clip.size == (100, 100)
