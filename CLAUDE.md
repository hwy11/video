# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an automated audio-driven video generator that creates synchronized videos from audio files and images. The system uses speech recognition to analyze audio content, then generates videos with precise timing, visual effects, transitions, and subtitles.

## Architecture

The system follows a modular pipeline architecture with the following core components:

- **ASR Module** (`video_generator/asr.py`): Uses faster-whisper to transcribe audio into timed segments
- **Timeline Module** (`video_generator/timeline.py`): Maps speech segments to images and builds media timeline
- **Visual Module** (`video_generator/visual.py`): Creates video clips with Ken Burns effects and transitions
- **Subtitle Module** (`video_generator/subtitle.py`): Generates synchronized subtitle clips
- **Render Module** (`video_generator/render.py`): Composes final video with all elements

## Development Commands

### Running the Application
```bash
python3 main.py
```

### Running Tests
```bash
python3 -m pytest tests/
```

### Running Individual Tests
```bash
python3 -m pytest tests/test_specific_module.py
python3 -m pytest tests/test_specific_module.py::test_function_name
```

### Running Tests with Verbosity
```bash
python3 -m pytest tests/ -v
```

## Key Files

- `main.py`: Entry point that orchestrates the pipeline
- `config.yaml`: Core configuration file controlling all aspects of video generation
- `video_generator/`: Main package containing all modules
- `tests/`: Test suite with comprehensive coverage
- `run_asr_standalone.py`: Standalone ASR testing script

## Configuration

The entire system is controlled through `config.yaml` with sections for:
- File paths (audio input, image folder, output)
- Video settings (resolution, FPS)
- Visual effects (Ken Burns effect, transitions)
- Subtitle styling
- ASR model parameters

## Dependencies

Core dependencies are managed via `requirements.txt`:
- `moviepy`: Video processing and composition
- `faster-whisper`: Speech recognition
- `pyyaml`: Configuration file parsing
- `pytest`: Testing framework

## Testing Approach

The project uses pytest with comprehensive test coverage for all modules. Tests include:
- Unit tests for individual functions
- Integration tests for pipeline components
- Mocking for external dependencies (moviepy, faster-whisper)
- Configuration validation tests

## Standalone ASR Tool

The `run_asr_standalone.py` script allows independent testing of the ASR functionality without running the full video generation pipeline.

## Important Notes

- The project requires FFmpeg to be installed system-wide for MoviePy functionality
- All external dependencies are wrapped in try/except blocks to handle missing imports gracefully
- The timeline module handles image cycling when there are more segments than images
- The system supports multiple languages through the Whisper model configuration