"""测试视觉效果模块 (visual.py)"""
import base64

from video_generator import visual as visual_module


# --- 模拟对象 (Dummy Class) ---
# 创建一个虚拟的 ImageClip 类来模拟 moviepy.editor.ImageClip
# 它只包含被测试代码所用到的方法，如 set_duration, fx, resize
class DummyImageClip:
    """一个用于测试的虚拟 ImageClip 类。"""
    def __init__(self, path):
        self.path = path
        self.duration = None
        self.effects = []
        self.size = None
        print(f"  [模拟] 已为路径创建 ImageClip: {path}")

    def set_duration(self, d):
        self.duration = d
        print(f"  [模拟] 已设置持续时间: {d}")
        return self

    def fx(self, func, *args, **kwargs):
        # 记录应用的特效，方便后续验证
        self.effects.append(func.__name__)
        print(f"  [模拟] 已应用特效: {func.__name__}")
        # 这里直接返回 self，因为我们不测试特效的实际效果
        return func(self, *args, **kwargs)

    def resize(self, newsize=None):
        self.size = newsize
        print(f"  [模拟] 已调整尺寸为: {newsize}")
        return self

# 模拟 moviepy.vfx 模块
class DummyVFX:
    """一个用于测试的虚拟 vfx 模块。"""
    def resize(self, clip, resize_func):
        # 在这里我们不关心具体的缩放逻辑，只需模拟调用即可
        # 实际的缩放效果由 resize_func 定义，我们不执行它
        print("  [模拟] vfx.resize 已被调用。")
        return clip


PNG_DATA = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAAAAAClX0ZFAAAADUlEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
)


def test_create_video_clips(monkeypatch):
    """
    测试视频片段的创建流程。
    - GIVEN: 一个时间轴和包含视觉效果配置的字典
    - WHEN: 调用 create_video_clips 函数
    - THEN: 应返回一个包含正确配置的虚拟 Clip 对象的列表
    """
    # --- 1. 安排 (Arrange) ---
    # 使用 monkeypatch 将真实的 moviepy 模块替换为我们的模拟对象
    monkeypatch.setattr(visual_module, "ImageClip", DummyImageClip)
    monkeypatch.setattr(visual_module, "vfx", DummyVFX())

    # 准备输入的时间轴数据
    timeline = [
        {"image_path": "img1.jpg", "duration_sec": 2.0},
        {"image_path": "img2.jpg", "duration_sec": 3.0},
    ]
    # 准备配置，启用 Ken Burns 特效并设置分辨率
    config = {
        "ken_burns_effect": {"enabled": True, "zoom_factor": 1.1},
        "resolution": [1920, 1080],
    }

    print("\n--- 运行: test_create_video_clips ---")
    print(f"输入时间轴: {timeline}")
    print(f"输入配置: {config}")

    # --- 2. 执行 (Act) ---
    clips = visual_module.create_video_clips(timeline, config)
    print("--- 执行细节 ---")
    for i, clip in enumerate(clips):
        print(f"  片段 {i+1} 详情:")
        print(f"    - 路径: {clip.path}")
        print(f"    - 持续时间: {clip.duration}s")
        print(f"    - 应用的特效: {clip.effects}")
        print(f"    - 最终尺寸: {clip.size}")
    print("-------------------------")

    # --- 3. 断言 (Assert) ---
    assert len(clips) == 2

    # 验证第一个片段
    clip1 = clips[0]
    assert clip1.path == "img1.jpg"
    assert clip1.duration == 2.0
    assert "resize" in clip1.effects  # Ken Burns 特效是通过 vfx.resize 实现的
    assert clip1.size == (1920, 1080)

    # 验证第二个片段
    clip2 = clips[1]
    assert clip2.path == "img2.jpg"
    assert clip2.duration == 3.0
    assert "resize" in clip2.effects
    assert clip2.size == (1920, 1080)
