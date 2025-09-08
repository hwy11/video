import types
from video_generator import asr


class DummySegment(types.SimpleNamespace):
    """Simple namespace to emulate whisper segments."""


class DummyModel:
    def __init__(self, size, device, compute_type):
        self.init_args = {"size": size, "device": device, "compute_type": compute_type}

    def transcribe(self, audio_path, **kwargs):
        self.transcribe_args = {"audio_path": audio_path, **kwargs}
        seg1 = DummySegment(text="hello", start=0.0, end=1.0)
        seg2 = DummySegment(text="world", start=1.0, end=2.0)
        return [seg1, seg2], None


def test_transcribe_audio(monkeypatch, tmp_path):
    audio = tmp_path / "dummy.wav"
    audio.write_bytes(b"00")

    dummy_model = DummyModel("tiny", "cpu", "int8")
    monkeypatch.setattr(asr, "WhisperModel", lambda *args, **kwargs: dummy_model)

    segments = asr.transcribe_audio(
        str(audio),
        {"size": "tiny", "device": "cpu", "compute_type": "int8", "language": "en", "beam_size": 5},
    )

    assert dummy_model.init_args == {"size": "tiny", "device": "cpu", "compute_type": "int8"}
    assert dummy_model.transcribe_args["language"] == "en"
    assert dummy_model.transcribe_args["beam_size"] == 5
    assert segments == [
        {"sentence": "hello", "start_sec": 0.0, "end_sec": 1.0, "duration_sec": 1.0},
        {"sentence": "world", "start_sec": 1.0, "end_sec": 2.0, "duration_sec": 1.0},
    ]
