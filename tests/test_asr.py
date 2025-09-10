"""测试语音识别模块 (asr.py)"""
import types
import math
from video_generator import asr

# --- 模拟对象 (Dummy Classes) ---


class DummySegment(types.SimpleNamespace):
    """一个简单的命名空间，用于模拟 faster-whisper 返回的 Segment 对象。"""


class DummyModel:
    """一个虚拟的 WhisperModel 类，用于模拟真实的 ASR 模型。"""

    def __init__(self, model_size_or_path, device, compute_type):
        print(f"\n  [模拟] WhisperModel 初始化中...")
        print(f"    - 模型尺寸: {model_size_or_path}")
        print(f"    - 设备: {device}")
        print(f"    - 计算类型: {compute_type}")
        self.init_args = {
            "size": model_size_or_path,
            "device": device,
            "compute_type": compute_type,
        }
        self.transcribe_args = {}

    def transcribe(self, audio, **kwargs):
        print("  [模拟] 调用 transcribe 方法...")
        print(f"    - 音频路径: {audio}")
        print(f"    - 其他参数: {kwargs}")
        self.transcribe_args = {"audio_path": audio, **kwargs}

        # 返回固定的、模拟的识别结果
        seg1 = DummySegment(text="你好", start=0.0, end=1.5)
        seg2 = DummySegment(text="世界", start=1.8, end=2.9)
        print("  [模拟] 返回两个识别出的片段。")
        return [seg1, seg2], "dummy_info"  # 第二个返回值是 info 对象，这里用字符串模拟


def test_transcribe_audio(monkeypatch, tmp_path):
    """
    测试音频转录功能的流程。
    - GIVEN: 一个虚拟的音频文件和 ASR 配置
    - WHEN: 调用 transcribe_audio 函数
    - THEN: 应正确初始化模型，使用正确参数调用 transcribe 方法，并返回处理后的片段
    """
    # --- 1. 安排 (Arrange) ---
    # 创建一个临时的虚拟音频文件
    audio_path = tmp_path / "dummy.wav"
    audio_path.write_bytes(b"dummy_audio_data")

    # 准备 ASR 模型配置 (注意：这里是完整的顶层配置)
    config = {
        "whisper_model": {
            "size": "tiny",
            "device": "cpu",
            "compute_type": "int8",
            "language": "zh",
            "beam_size": 5,
        }
    }

    # 我们需要捕获创建的实例以供后续断言
    model_instance_holder = []

    def dummy_model_factory(model_size_or_path, device="cpu", compute_type="int8"):
        """
        模拟 WhisperModel 的构造函数。
        它接收一个位置参数（模型尺寸）和多个关键字参数。
        """
        print(f"\n  [模拟] WhisperModel 工厂被调用...")
        print(f"    - 位置参数 (模型尺寸): {model_size_or_path}")
        print(f"    - 关键字参数 (设备): {device}")
        print(f"    - 关键字参数 (计算类型): {compute_type}")
        model = DummyModel(model_size_or_path, device, compute_type)
        model_instance_holder.append(model)
        return model

    monkeypatch.setattr(asr, "WhisperModel", dummy_model_factory)

    print("\n--- 运行: test_transcribe_audio ---")
    print(f"输入音频路径: {audio_path}")
    print(f"输入配置: {config}")

    # --- 2. 执行 (Act) ---
    segments = asr.transcribe_audio(str(audio_path), config)
    print(f"\n输出处理后的片段: {segments}")

    # --- 3. 断言 (Assert) ---
    print("\n--- 断言 ---")

    # 从 holder 中获取模型实例
    assert len(model_instance_holder) == 1, "应只创建一个模型实例"
    dummy_model = model_instance_holder[0]

    # 验证模型初始化参数
    print("正在验证模型初始化参数...")
    expected_init_args = {"size": "tiny", "device": "cpu", "compute_type": "int8"}
    assert dummy_model.init_args == expected_init_args

    # 验证 transcribe 方法的调用参数
    print("正在验证 transcribe 方法调用参数...")
    assert dummy_model.transcribe_args["language"] == "zh"
    assert dummy_model.transcribe_args["beam_size"] == 5

    # 验证输出的片段是否被正确处理
    print("正在验证输出片段的格式...")
    expected_segments = [
        {"sentence": "你好", "start_sec": 0.0, "end_sec": 1.5, "duration_sec": 1.5},
        {"sentence": "世界", "start_sec": 1.8, "end_sec": 2.9, "duration_sec": 1.1},
    ]

    assert len(segments) == len(
        expected_segments
    ), f"片段数量不匹配! 预期: {len(expected_segments)}, 实际: {len(segments)}"
    for i, seg in enumerate(segments):
        exp_seg = expected_segments[i]
        assert seg["sentence"] == exp_seg["sentence"]
        assert math.isclose(seg["start_sec"], exp_seg["start_sec"])
        assert math.isclose(seg["end_sec"], exp_seg["end_sec"])
        assert math.isclose(seg["duration_sec"], exp_seg["duration_sec"])

    print("所有断言通过。")
    print("------------------")
