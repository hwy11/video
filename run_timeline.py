"""CLI to build media timeline from ASR segments and an images folder.

Usage examples:

  Regular round-robin mapping:
    python -m video.run_timeline \
      --segments-json video/asr_result_20250910_223252.json \
      --images-dir video/video_generator/shot_video \
      --out video/file_timeline/asr_result_20250910_223252_timeline.json

  Semantic grouping with Zhipu LLM (requires zai-sdk and ZHIPU_API_KEY):
    ZHIPU_API_KEY=your_key_here \
    python -m video.run_timeline \
      --segments-json video/asr_result_20250910_223252.json \
      --images-dir video/video_generator/shot_video \
      --out video/file_timeline/asr_result_20250910_223252_timeline.json \
      --semantic
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Dict, Optional

from video.video_generator.timeline import (
    build_timeline,
    build_timeline_semantic,
    build_timeline_greedy,
)


def load_segments(p: Path) -> List[Dict]:
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    # Fallbacks: accept {"segments": [...]} or {"result": {"segments": [...]}}
    if isinstance(data, dict):
        if isinstance(data.get("segments"), list):
            return data["segments"]
        result = data.get("result")
        if isinstance(result, dict) and isinstance(result.get("segments"), list):
            return result["segments"]
    raise ValueError("Unsupported JSON structure for segments")


def load_env_file(env_path: Optional[Path]) -> None:
    """Minimal .env loader: KEY=VALUE pairs, ignores comments and blanks.

    Only sets variables not already present in the environment to avoid
    overriding explicit user settings.
    """
    import os

    if env_path is None:
        return
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def main() -> None:
    ap = argparse.ArgumentParser(description="Build timeline from ASR segments and images")
    ap.add_argument("--segments-json", required=True, help="Path to ASR result JSON file")
    ap.add_argument("--images-dir", required=True, help="Directory containing images")
    ap.add_argument("--out", required=True, help="Output JSON path for timeline")
    ap.add_argument("--semantic", action="store_true", help="Use semantic grouping via Zhipu LLM")
    ap.add_argument("--greedy", action="store_true", help="Use greedy similarity mapping (no AI)")
    ap.add_argument("--api-key", default=None, help="Zhipu API key (optional; otherwise env is used)")
    ap.add_argument("--model", default="glm-4.5", help="Zhipu model name (default: glm-4.5)")
    ap.add_argument(
        "--env",
        default=None,
        help="Path to .env file with ZHIPU_API_KEY; if omitted, auto-detect",
    )
    ap.add_argument("--sim-threshold", type=float, default=0.5, help="Similarity threshold for --greedy (0-1)")
    ap.add_argument("--ngram", type=int, default=2, help="Char n-gram for --greedy (2 or 3 recommended)")
    ap.add_argument("--group-context", type=int, default=3, help="Recent sentences to represent a group")
    ap.add_argument("--debug", action="store_true", help="Print debug info (LLM output, similarities)")
    ap.add_argument("--strict", action="store_true", help="LLM-only mode: no fallback; raise on errors")
    ap.add_argument("--noncontiguous", action="store_true", help="Allow non-contiguous clustering (may revisit groups)")
    ap.add_argument("--alloc-all", action="store_true", help="Use all images by proportional allocation across spans")
    ap.add_argument("--alloc-metric", choices=["duration", "count"], default="duration", help="Image allocation metric for --semantic")
    args = ap.parse_args()

    seg_path = Path(args.segments_json)
    img_dir = Path(args.images_dir)
    out_path = Path(args.out)

    # Load .env if specified or discover common locations
    env_path: Optional[Path]
    if args.env:
        env_path = Path(args.env)
    else:
        # Try common locations without failing if missing
        candidates = [
            Path(".env"),
            Path("video/.env"),
            Path("ROMA/.env"),
        ]
        env_path = next((p for p in candidates if p.exists()), None)
    load_env_file(env_path)

    segments = load_segments(seg_path)

    mode = "round-robin"
    if args.greedy:
        mode = "greedy"
        timeline = build_timeline_greedy(
            segments,
            str(img_dir),
            threshold=args.sim_threshold,
            ngram=args.ngram,
            group_context=args.group_context,
            debug=args.debug,
        )
    elif args.semantic:
        import os
        mode = "semantic"
        key = args.api_key or os.getenv("ZHIPU_API_KEY")
        try:
            timeline = build_timeline_semantic(
                segments,
                str(img_dir),
                api_key=key,
                model=args.model,
                debug=args.debug,
                strict=args.strict,
                contiguous=not args.noncontiguous,
                allocation_metric=args.alloc_metric,
            )
        except Exception as e:
            if args.strict:
                raise
            print(f"[warn] semantic mapping failed ({e}); falling back to round-robin.")
            mode = "round-robin (fallback)"
            timeline = build_timeline(segments, str(img_dir))
    else:
        timeline = build_timeline(segments, str(img_dir))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {len(timeline)} entries to {out_path} using {mode} mapping.")


if __name__ == "__main__":
    main()
