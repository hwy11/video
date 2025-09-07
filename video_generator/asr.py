"""ASR module for transcribing audio into timed segments."""
from typing import List, Dict

try:  # pragma: no cover - handled in tests via monkeypatch
    from faster_whisper import WhisperModel
except Exception:  # ImportError if dependency missing
    WhisperModel = None


def transcribe_audio(audio_path: str, model_config: Dict) -> List[Dict]:
    """Transcribe ``audio_path`` using ``faster-whisper``.

    Parameters
    ----------
    audio_path:
        Path to the input audio file.
    model_config:
        Dictionary containing model options such as model ``size`` and ``device``.

    Returns
    -------
    list of dict
        Each item represents a spoken sentence with its text and start/end
        timestamps in seconds.
    """
    if WhisperModel is None:
        raise RuntimeError("faster-whisper is not installed")
    model = WhisperModel(
        model_config.get("size", "base"),
        device=model_config.get("device", "cpu"),
        compute_type=model_config.get("compute_type", "int8"),
    )
    segments, _ = model.transcribe(audio_path, word_timestamps=False)
    return [
        {
            "sentence": seg.text.strip(),
            "start_sec": seg.start,
            "end_sec": seg.end,
            "duration_sec": seg.end - seg.start,
        }
        for seg in segments
    ]
