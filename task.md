# 项目任务列表

## 已完成
- 搭建项目结构及核心模块（`asr`、`timeline`、`visual`、`subtitle`、`render`）。
- 编写中英双语 README，介绍目标、环境配置和工作流程。
- 添加 `config.yaml`、`requirements.txt` 以及基础入口脚本 `main.py`。

## 待办
- 使用 `faster-whisper` 实现 `transcribe_audio`，获取句级时间戳。
- 在 `build_timeline` 中将 ASR 段落映射到图片。
- 在 `create_video_clips` 中生成 Ken Burns 风格的视频片段。
- 在 `create_subtitle_clips` 中创建与时间线同步的字幕片段。
- 在 `render_video` 中合成视频、叠加字幕、附加音频并渲染输出。
- 添加单元测试和示例资源。
- 随着功能稳定完善文档和使用说明。
