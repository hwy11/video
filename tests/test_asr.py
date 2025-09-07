import types
from video_generator import asr

class DummySegment(types.SimpleNamespace):
    pass

class DummyModel:
    def transcribe(self, audio_path, word_timestamps=False):
        seg1 = DummySegment(text="hello", start=0.0, end=1.0)
        seg2 = DummySegment(text="world", start=1.0, end=2.0)
        return [seg1, seg2], None

def test_transcribe_audio(monkeypatch):
    monkeypatch.setattr(asr, "WhisperModel", lambda *args, **kwargs: DummyModel())
    segments = asr.transcribe_audio("dummy.wav", {"size": "tiny", "device": "cpu"})
    assert segments == [
        {"sentence": "hello", "start_sec": 0.0, "end_sec": 1.0, "duration_sec": 1.0},
        {"sentence": "world", "start_sec": 1.0, "end_sec": 2.0, "duration_sec": 1.0},
    ]
