"""ASR module for transcribing audio into timed segments."""
from typing import List, Dict


def transcribe_audio(audio_path: str, model_config: Dict) -> List[Dict]:
    """Transcribe audio using faster-whisper and return timed segments.

    Args:
        audio_path: Path to the input audio file.
        model_config: Dictionary containing model options such as size and device.

    Returns:
        A list of dictionaries where each item represents a spoken sentence with
        its start and end timestamps.
    """
    raise NotImplementedError("ASR transcription not implemented.")
