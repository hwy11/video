import pprint
import argparse
import json
import os
from datetime import datetime
from typing import Any, Dict, List

from video_generator.asr import transcribe_audio

try:
    from opencc import OpenCC  # 可选依赖：简繁转换
except Exception:  # pragma: no cover
    OpenCC = None


def build_app_config(model_path: str, device: str, compute_type: str, language: str, beam_size: int) -> Dict[str, Any]:
    return {
        "whisper_model": {
            "size": model_path,
            "device": device,
            "compute_type": compute_type,
            "language": language,
            "beam_size": beam_size,
        }
    }


def auto_compute_type(device: str, user_specified: str) -> str:
    if user_specified:
        return user_specified
    # 简单的自动选择逻辑
    if device == "cuda":
        return "float16"
    return "int8"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="独立调用 ASR 模块进行语音识别")
    parser.add_argument("--audio", default="./assets/images/tts.wav", help="输入音频文件路径")
    parser.add_argument("--model-path", default="large", help="本地模型路径或模型名")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="推理设备")
    parser.add_argument("--compute-type", default="int8", help="计算精度，留空则自动选择")
    parser.add_argument("--language", default="zh", help="语种，如 zh/en，None 则自动检测")
    parser.add_argument("--beam-size", type=int, default=12, help="Beam size")
    parser.add_argument("--out", default=None, help="结果写入 JSON 文件路径；默认写入到 ./asr_result_时间戳.json")
    # 后处理参数
    parser.add_argument(
        "--zh-convert",
        choices=["none", "s", "t"],
        default="s",
        help="中文转换：none=不转换, s=转为简体, t=转为繁体",
    )
    parser.add_argument(
        "--merge-short-max-chars",
        type=int,
        default=4,
        help="将长度≤该值的短句与相邻句合并（中文“字”计数的近似）",
    )
    return parser.parse_args()


def main():
    print("--- 开始独立运行 ASR 语音识别模块 ---")
    args = parse_args()

    # 路径与依赖检查
    if not os.path.exists(args.audio):
        print(f"\n[错误] 音频文件未找到，请检查路径: {args.audio}")
        return

    compute_type = auto_compute_type(args.device, args.compute_type)
    app_config = build_app_config(
        model_path=args.model_path,
        device=args.device,
        compute_type=compute_type,
        language=args.language if args.language.lower() != "none" else None,
        beam_size=args.beam_size,
    )

    print(f"\n[配置] 模型: {app_config['whisper_model']['size']}")
    print(f"[配置] 设备: {app_config['whisper_model']['device']} | 精度: {app_config['whisper_model']['compute_type']}")
    print(f"[文件] 识别音频: {args.audio}")

    try:
        print("\n[处理] 正在进行语音识别，请稍候...")
        segments = transcribe_audio(args.audio, app_config)

        # 后处理：中文转换 + 短句合并
        segments = postprocess_segments(
            segments,
            zh_convert=args.zh_convert,
            merge_short_max_chars=args.merge_short_max_chars,
        )

        print("\n--- 识别完成 ---")
        preview = segments[:5] if isinstance(segments, list) else segments
        print("识别出的语音片段（最多前5条）:")
        pprint.pprint(preview)

        # 结果保存
        out_path = args.out or f"./asr_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(segments, f, ensure_ascii=False, indent=2)
        print(f"\n[输出] 完整结果已写入: {out_path}")

    except FileNotFoundError:
        print(f"\n[错误] 音频文件未找到，请检查路径: {args.audio}")
    except RuntimeError as e:
        print(f"\n[错误] 运行时错误: {e}")
        print("请确认是否已安装 'faster-whisper' 以及模型路径可用。")
    except Exception as e:
        print(f"\n[错误] 未知错误: {e}")
# ============== 后处理工具函数 ==============
def _get_converter(mode: str):
    if OpenCC is None:
        return None
    if mode == "s":
        return OpenCC("t2s")
    if mode == "t":
        return OpenCC("s2t")
    return None


def _maybe_convert(text: str, converter) -> str:
    if not text:
        return text
    if converter is None:
        return text
    return converter.convert(text)


def _pick_text(seg: dict) -> str:
    primary = seg.get("text")
    if primary and isinstance(primary, str) and primary.strip():
        return primary
    secondary = seg.get("sentence")
    if secondary and isinstance(secondary, str):
        return secondary
    return ""


def _merge_short(segments: List[dict], max_chars: int) -> List[dict]:
    if not isinstance(segments, list) or not segments:
        return segments
    result: List[dict] = []
    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not result:
            # 同步保存到 text 与 sentence，保证下游兼容
            first = {**seg, "text": text, "sentence": text}
            result.append(first)
            continue
        if len(text) <= max_chars:
            # 将短句并入前一句（直接拼接，不加分隔符）
            prev_text = result[-1].get("text", "")
            merged_text = prev_text + text
            result[-1]["text"] = merged_text
            result[-1]["sentence"] = merged_text
            # 更新时间边界（兼容不同字段名）
            for end_key in ("end", "end_sec"):
                if end_key in seg:
                    result[-1][end_key] = seg[end_key]
        else:
            result.append({**seg, "text": text, "sentence": text})
    return result


def postprocess_segments(
    segments: Any,
    zh_convert: str = "s",
    merge_short_max_chars: int = 4,
) -> Any:
    """对 ASR 返回的段落进行后处理：中文简繁转换 + 短句合并。

    期望输入：list[{"text": str, "start": float, "end": float, ...}]，若不是列表将原样返回。
    """
    if not isinstance(segments, list):
        return segments

    converter = _get_converter(zh_convert)

    # 先统一选择文本字段（text 或 sentence），做去空白与简繁转换
    normalized: List[dict] = []
    for seg in segments:
        new_seg = dict(seg)
        chosen = _pick_text(new_seg)
        new_text = (chosen or "").strip()
        new_text = _maybe_convert(new_text, converter)
        # 同步更新两个字段，保证使用者无论读哪一个都一致
        new_seg["text"] = new_text
        new_seg["sentence"] = new_text
        normalized.append(new_seg)

    if merge_short_max_chars is not None and merge_short_max_chars >= 0:
        normalized = _merge_short(normalized, merge_short_max_chars)

    return normalized


if __name__ == "__main__":
    main()