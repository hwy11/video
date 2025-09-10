"""测试字幕生成模块 (subtitle.py)"""
from video_generator import subtitle as subtitle_module


# --- 模拟对象 (Dummy Class) ---
# 创建一个虚拟的 TextClip 类来模拟 moviepy.editor.TextClip
class DummyTextClip:
    """一个用于测试的虚拟 TextClip 类。"""
    def __init__(self, text, **kwargs):
        self.text = text
        self.kwargs = kwargs
        self.start = None
        self.duration = None
        self.position = None
        print(f"\n  [模拟] 已创建文本片段，内容: '{text}'")
        print(f"    - 样式参数: {kwargs}")

    def set_start(self, s):
        self.start = s
        print(f"  [模拟] 已设置开始时间: {s}")
        return self

    def set_duration(self, d):
        self.duration = d
        print(f"  [模拟] 已设置持续时间: {d}")
        return self

    def set_position(self, pos):
        self.position = pos
        print(f"  [模拟] 已设置位置: {pos}")
        return self


def test_create_subtitle_clips(monkeypatch):
    """
    测试字幕片段的创建流程。
    - GIVEN: 一个时间轴和包含字幕样式的配置
    - WHEN: 调用 create_subtitle_clips 函数
    - THEN: 应返回一个包含正确文本、时长和位置的虚拟 TextClip 列表
    """
    # --- 1. 安排 (Arrange) ---
    # 使用 monkeypatch 将真实的 TextClip 替换为我们的模拟版本
    monkeypatch.setattr(subtitle_module, "TextClip", DummyTextClip)
    
    # 准备输入的时间轴数据
    timeline = [
        {"sentence": "Hello world", "start_sec": 0, "end_sec": 1.5},
        {"sentence": "This is a test", "start_sec": 1.8, "end_sec": 3.0},
    ]
    # 准备输入的配置
    config = {
        "subtitle_style": {
            "enabled": True, 
            "position": ("center", "bottom"),
            "fontsize": 60,
            "color": "yellow"
        }
    }

    print("\n--- 运行: test_create_subtitle_clips ---")
    print(f"输入时间轴: {timeline}")
    print(f"输入配置: {config}")

    # --- 2. 执行 (Act) ---
    clips = subtitle_module.create_subtitle_clips(timeline, config)

    # --- 3. 断言 (Assert) ---
    print("\n--- 断言 ---")
    assert len(clips) == 2, "应该创建两个字幕片段"

    # 验证第一个片段
    clip1 = clips[0]
    print(f"正在验证片段 1: 文本='{clip1.text}'")
    assert clip1.text == "Hello world"
    assert clip1.start == 0
    assert clip1.duration == 1.5
    assert clip1.position == ("center", "bottom")
    assert clip1.kwargs["fontsize"] == 60
    assert clip1.kwargs["color"] == "yellow"

    # 验证第二个片段
    clip2 = clips[1]
    print(f"正在验证片段 2: 文本='{clip2.text}'")
    assert clip2.text == "This is a test"
    assert clip2.start == 1.8
    assert clip2.duration == 1.2  # 3.0 - 1.8 = 1.2
    assert clip2.position == ("center", "bottom")
    print("------------------")

def test_create_subtitle_clips_disabled(monkeypatch):
    """
    测试当字幕在配置中被禁用时，函数是否返回空列表。
    - GIVEN: 一个时间轴和禁用字幕的配置
    - WHEN: 调用 create_subtitle_clips 函数
    - THEN: 应返回一个空列表
    """
    # --- 1. 安排 (Arrange) ---
    monkeypatch.setattr(subtitle_module, "TextClip", DummyTextClip)
    timeline = [{"sentence": "hello", "start_sec": 0, "end_sec": 1}]
    config = {"subtitle_style": {"enabled": False}} # 关键配置

    print("\n--- 运行: test_create_subtitle_clips_disabled ---")
    print(f"输入时间轴: {timeline}")
    print(f"输入配置: {config}")

    # --- 2. 执行 (Act) ---
    clips = subtitle_module.create_subtitle_clips(timeline, config)
    print(f"输出片段: {clips}")

    # --- 3. 断言 (Assert) ---
    assert clips == [], "当字幕被禁用时，应该返回空列表"
    print("------------------")
