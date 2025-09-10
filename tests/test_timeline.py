"""测试时间轴构建模块 (timeline.py)"""
import pytest
from video_generator import timeline as timeline_module


def test_build_timeline(tmp_path):
    """
    测试基本的时间轴构建功能。
    - GIVEN: 给定语音片段和包含图片的文件夹
    - WHEN: 调用 build_timeline 函数
    - THEN: 应返回一个正确映射了图片和语音的时间轴列表
    """
    # --- 1. 安排 (Arrange) ---
    # 创建一个临时目录，并在其中创建虚拟的图片文件
    d = tmp_path / "images"
    d.mkdir()
    (d / "img1.jpg").touch()
    (d / "img2.jpg").touch()

    # 准备输入的语音片段数据
    segments = [
        {"sentence": "Hello.", "start_sec": 0.5, "end_sec": 1.0},
        {"sentence": "World.", "start_sec": 1.2, "end_sec": 2.0},
    ]

    print("\n--- 运行: test_build_timeline ---")
    print(f"输入片段: {segments}")
    print(f"图片文件夹: {d}")

    # --- 2. 执行 (Act) ---
    # 调用被测试的函数
    timeline = timeline_module.build_timeline(segments, str(d))
    print(f"输出时间轴: {timeline}")

    # --- 3. 断言 (Assert) ---
    # 验证输出是否符合预期
    assert len(timeline) == 2
    assert timeline[0]["sentence"] == "Hello."
    assert timeline[0]["image_path"] == str(d / "img1.jpg")
    assert timeline[0]["duration_sec"] == 0.5
    assert timeline[1]["image_path"] == str(d / "img2.jpg")


def test_build_timeline_reuses_images(tmp_path):
    """
    测试当语音片段多于图片时，图片是否会被循环使用。
    - GIVEN: 3个语音片段，但只有2张图片
    - WHEN: 调用 build_timeline 函数
    - THEN: 第3个时间轴条目应重新使用第1张图片
    """
    # --- 1. 安排 (Arrange) ---
    d = tmp_path / "images"
    d.mkdir()
    (d / "img1.jpg").touch()
    (d / "img2.jpg").touch()

    segments = [
        {"sentence": "One", "start_sec": 0, "end_sec": 1},
        {"sentence": "Two", "start_sec": 1, "end_sec": 2},
        {"sentence": "Three", "start_sec": 2, "end_sec": 3},
    ]

    print("\n--- 运行: test_build_timeline_reuses_images ---")
    print(f"输入片段: {segments}")
    print(f"图片文件夹: {d}")

    # --- 2. 执行 (Act) ---
    timeline = timeline_module.build_timeline(segments, str(d))
    print(f"输出时间轴: {timeline}")

    # --- 3. 断言 (Assert) ---
    assert len(timeline) == 3
    assert timeline[0]["image_path"] == str(d / "img1.jpg")
    assert timeline[1]["image_path"] == str(d / "img2.jpg")
    # 验证第三个片段是否复用了第一张图
    assert timeline[2]["image_path"] == str(d / "img1.jpg")


def test_build_timeline_no_images(tmp_path):
    """
    测试当图片文件夹为空时，是否会按预期抛出异常。
    - GIVEN: 一个空的图片文件夹
    - WHEN: 调用 build_timeline 函数
    - THEN: 应该抛出 FileNotFoundError
    """
    # --- 1. 安排 (Arrange) ---
    d = tmp_path / "images"
    d.mkdir()  # 文件夹存在，但里面没有文件
    segments = [{"sentence": "Hello", "start_sec": 0, "end_sec": 1}]

    print("\n--- 运行: test_build_timeline_no_images ---")
    print(f"输入片段: {segments}")
    print(f"图片文件夹: {d} (为空)")

    # --- 2. 执行 (Act) & 3. 断言 (Assert) ---
    # 使用 pytest.raises 来捕获并验证是否抛出了预期的异常
    with pytest.raises(FileNotFoundError) as e:
        timeline_module.build_timeline(segments, str(d))
    
    print(f"成功捕获到预期的错误: {e.value}")
    assert "No images found" in str(e.value)
