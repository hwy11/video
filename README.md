# 自动化语音驱动视频生成器 (Automated Audio-Driven Video Generator)

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 项目概要 (Overview)

本项目是一个高效的自动化视频内容创作工具。它能够接收一个预先生成的语音文件（例如TTS）和一组图片，通过先进的语音识别技术精确分析语音内容，最终生成一个图片与语音句子完全同步、包含动态效果、转场和字幕的专业视频。

它旨在将繁琐的视频剪辑工作流自动化，特别适用于需要快速、批量生产信息类、解说类或产品介绍视频的场景。

## 核心功能 (Key Features)

- **🔊 精准句级同步**: 采用 [faster-whisper](https://github.com/guillaumekln/faster-whisper) (OpenAI Whisper 的优化版) 进行语音分析，能够获取每个句子的精确开始和结束时间戳，实现视觉与听觉的完美对齐。
- 🖼️ **动态视觉效果**: 自动为静态图片应用“Ken Burns Effect”（平移与缩放），让静态画面生动起来。
- ✨ **自动转场**: 在图片切换之间平滑地应用交叉淡入（Crossfade）等转场效果，提升视频的流畅度和观感。
- ✍️ **同步字幕生成**: 根据语音识别结果，自动生成与语音内容和时间完全同步的字幕。
- ⚙️ **高度可配置**: 所有的核心参数，包括文件路径、视频分辨率、视觉效果、转场时长和字幕样式，都通过一个独立的 `config.yaml` 文件进行管理，无需修改任何代码即可调整视频风格。

## 工作流程 (How It Works)

本系统采用模块化的流水线架构，整个流程清晰可控：

```mermaid
graph TD
    A[1. 输入资源: 语音文件 + 图片] --> B{2. 语音分析模块 (ASR)};
    B --> C[3. 生成媒体时间轴 (Timeline)];
    C --> D{4. 视觉片段生成};
    C --> E{5. 字幕对象生成};
    D & E --> F{6. 合成与渲染模块};
    F --> G[7. 输出最终视频];
```

1. **加载资源与配置**: 程序首先读取 `config.yaml` 文件和指定的资源（音频、图片）。
2. **语音分析**: 使用 `faster-whisper` 模型对音频文件进行处理，提取出包含精确时间戳的句子文本。
3. **构建时间轴**: 将语音分析结果与图片列表进行映射，生成一个核心的“媒体时间轴”数据结构，它定义了视频中每个片段的所有信息。
4. **生成视觉与字幕**: 程序遍历时间轴，为每个片段独立生成带动态效果的视频剪辑（VideoClip）和带样式的字幕剪辑（TextClip）。
5. **最终合成**: 将所有视频剪辑拼接并应用转场，然后将字幕层叠加，最后附上原始音频，渲染输出最终的视频文件。

## 技术栈 (Technology Stack)

- **核心语言**: Python 3.9+
- **视频处理**: MoviePy
- **语音识别**: faster-whisper
- **配置管理**: PyYAML
- **系统依赖**: FFmpeg (MoviePy 需要)

## 安装与设置 (Installation & Setup)

### 1. 克隆本仓库

```bash
git clone [你的仓库地址]
cd [你的项目目录]
```

### 2. 安装系统依赖 (Ubuntu 22.04)

```bash
sudo apt update
sudo apt install ffmpeg python3-venv
```

### 3. 创建虚拟环境并安装依赖

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` 文件内容如下：

```
moviepy
faster-whisper
pyyaml
```

## 目录结构 (Directory Structure)

```
/your_project_name/
|-- main.py
|-- config.yaml
|-- requirements.txt
|-- README.md
|-- /assets/
|   |-- /images/
|   |-- audio.mp3
|-- /output/
```

## 配置说明 (`config.yaml`)

这是控制整个视频生成过程的核心文件。

```yaml
# ---------------- 文件路径配置 ----------------
input_audio: "assets/audio.mp3"
image_folder: "assets/images/"
output_file: "output/final_video.mp4"

# ---------------- 视频基础设置 ----------------
resolution: [1920, 1080]
fps: 30

# ---------------- 视觉效果配置 ----------------
ken_burns_effect:
  enabled: true
  zoom_factor: 1.15

transition:
  type: "fade"
  duration_sec: 0.5

# ---------------- 字幕样式配置 ----------------
subtitle_style:
  enabled: true
  font: "Arial-Bold"
  fontsize: 72
  color: "white"
  stroke_color: "black"
  stroke_width: 2
  position: ["center", "bottom"]

# ---------------- ASR 模型配置 ----------------
whisper_model:
  size: "base"
  device: "cpu"
  compute_type: "int8"  # 推理精度，可选值: float16, int8 等
  language: "auto"      # 识别语言，不填则自动检测
  beam_size: 5          # beam search 宽度，越大越准但越慢
```

## 使用方法 (Usage)

1. 准备资源：将 TTS 音频文件放入 `assets/`，并将图片按顺序命名后放入 `assets/images/`。
2. 修改配置：根据需要编辑 `config.yaml`。
3. 运行脚本：

```bash
python main.py
```

4. 查看结果：生成的视频将保存在 `output/` 目录中。

## 贡献 (Contributing)

欢迎提交问题 (Issues) 和合并请求 (Pull Requests)。如果你有新的功能想法或改进建议，请随时提出。

## 许可证 (License)

本项目采用 [MIT License](https://opensource.org/licenses/MIT) 授权。
