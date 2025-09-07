# 测试使用说明 (Test Usage)

本目录包含项目各核心模块的单元测试，使用 [pytest](https://docs.pytest.org/) 运行。

## 运行全部测试

```bash
pytest
```

## 运行单个测试文件

```bash
pytest tests/test_asr.py
```

## 测试文件简介

- `test_asr.py`：测试语音转写模块。
- `test_timeline.py`：测试时间轴构建。
- `test_visual.py`：测试视觉片段生成。
- `test_subtitle.py`：测试字幕生成。
- `test_render.py`：测试最终渲染逻辑。

所有测试共享的夹具位于 `conftest.py`。
