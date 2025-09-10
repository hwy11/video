"""ASR module for transcribing audio into timed segments."""
from pathlib import Path
from typing import List, Dict

try:  # pragma: no cover - handled in tests via monkeypatch
    from faster_whisper import WhisperModel
except Exception:  # ImportError if dependency missing
    WhisperModel = None


def transcribe_audio(audio_path: str, config: Dict) -> List[Dict]:
    """Transcribe ``audio_path`` using ``faster-whisper``.

    Parameters
    ----------
    audio_path:
        Path to the input audio file.
    config:
        The full application configuration dictionary. Model options are
        expected under the ``whisper_model`` key.

    Returns
    -------
    list of dict
        Each item represents a spoken sentence with its text and start/end
        timestamps in seconds.
    """
    if WhisperModel is None:
        raise RuntimeError("faster-whisper is not installed")

    audio_path_obj = Path(audio_path)
    if not audio_path_obj.is_file():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # 从主配置中提取模型相关的子配置
    model_config = config.get("whisper_model", {})

    model = WhisperModel(
        model_config.get("size", "large"),
        device=model_config.get("device", "cpu"),
        compute_type=model_config.get("compute_type", "int8"),
    )

    transcribe_kwargs = {
        "word_timestamps": False,
        "temperature": model_config.get("temperature", 0.0),
        "patience": model_config.get("patience", 1.2),
    }
    for key in ("language", "beam_size", "task"):
        if key in model_config:
            transcribe_kwargs[key] = model_config[key]

    segments, _ = model.transcribe(str(audio_path_obj), **transcribe_kwargs)
    return [
        {
            "sentence": seg.text.strip(),
            "start_sec": seg.start,
            "end_sec": seg.end,
            "duration_sec": seg.end - seg.start,
        }
        for seg in segments
    ]
