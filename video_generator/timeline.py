"""Media timeline construction utilities."""
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
import re
from collections import Counter


def build_timeline(segments: List[Dict], image_folder: str) -> List[Dict]:
    """Map speech segments to images and build the media timeline.

    Images are read from ``image_folder`` and sorted alphabetically. Each
    segment is paired with an image in order, producing a timeline entry
    containing the sentence, timestamps and image path.

    If there are more segments than images, images are reused in a cycle.
    """
    images = sorted(Path(image_folder).glob("*"))
    if not images:
        raise FileNotFoundError("No images found in image folder")

    timeline: List[Dict] = []
    for idx, seg in enumerate(segments):
        image_path = str(images[idx % len(images)])
        timeline.append(
            {
                "sentence": seg["sentence"],
                "start_sec": seg["start_sec"],
                "end_sec": seg["end_sec"],
                "duration_sec": seg["end_sec"] - seg["start_sec"],
                "image_path": image_path,
            }
        )
    return timeline


def _round_robin_timeline(segments: List[Dict], images: List[Path]) -> List[Dict]:
    timeline: List[Dict] = []
    for idx, seg in enumerate(segments):
        image_path = str(images[idx % len(images)])
        timeline.append(
            {
                "sentence": seg["sentence"],
                "start_sec": seg["start_sec"],
                "end_sec": seg["end_sec"],
                "duration_sec": seg["end_sec"] - seg["start_sec"],
                "image_path": image_path,
            }
        )
    return timeline


def build_timeline_semantic(
    segments: List[Dict],
    image_folder: str,
    *,
    api_key: Optional[str] = None,
    model: str = "glm-4.5",
    debug: bool = False,
    strict: bool = False,
    contiguous: bool = True,
    allocate_all_images: bool = True,
    allocation_metric: str = "duration",  # or "count"
) -> List[Dict]:
    """AI-assisted mapping of speech segments to images by semantic grouping.

    This groups semantically similar sentences so they share the same image.
    It uses Zhipu's chat model via ``zai-sdk`` to cluster sentences into at
    most ``len(images)`` groups and assigns each group to an image.

    Notes
    -----
    - Non-breaking: this is an alternative to ``build_timeline``.
    - Fallback: if the AI call/import/parse fails, falls back to round-robin.
    - Auth: reads API key from ``api_key`` argument or ``ZHIPU_API_KEY`` env.
    """
    images = sorted(Path(image_folder).glob("*"))
    if not images:
        raise FileNotFoundError("No images found in image folder")

    if not segments:
        return []

    max_groups = min(len(images), len(segments))

    # Lazy import to keep tests working when SDK isn't installed
    try:
        from zai import ZhipuAiClient  # type: ignore
    except Exception:
        # SDK unavailable; graceful fallback
        if debug:
            print("[semantic] zai-sdk not installed.")
        if strict:
            raise RuntimeError("zai-sdk not installed; cannot run LLM semantic mapping in strict mode")
        return _round_robin_timeline(segments, images)

    api_key = api_key or os.getenv("ZHIPU_API_KEY")
    if not api_key:
        # No credentials provided; graceful fallback
        if debug:
            print("[semantic] ZHIPU_API_KEY missing.")
        if strict:
            raise RuntimeError("ZHIPU_API_KEY missing; cannot run LLM semantic mapping in strict mode")
        return _round_robin_timeline(segments, images)

    client = ZhipuAiClient(api_key=api_key)

    payload = {
        "sentences": [
            {"index": i, "text": s.get("sentence", "")} for i, s in enumerate(segments)
        ],
        "max_groups": max_groups,
    }

    if contiguous:
        system_prompt = (
            "你是一个严格的JSON时间轴分段器。根据输入的句子（按时间排序），"
            "将相邻且语义相近的句子合并为连续的段（span）。要求：\n"
            "- 每个组(groups中的子数组)必须是按原顺序的连续索引段，例如 [3,4,5]。\n"
            "- 组与组之间连接起来应覆盖所有索引，且不重复、不打乱顺序（整体为 [0,1,2,...,N-1] 的分段）。\n"
            "- 段数不超过 max_groups，能合并就合并，但不要跨越明显话题边界。\n"
            "只输出严格 JSON：\n"
            "{""groups"": [[int,...],[...]], ""group_tags"": [string,...]}\n"
            "- group_tags 为可选，长度与组数一致，用<=12字给每段起标签，便于调试。\n"
            "- 只输出 JSON，不要任何额外文字。"
        )
    else:
        system_prompt = (
            "你是一个严格的JSON分组器。根据输入的句子列表，按语义相近聚类到"
            "不超过 max_groups 个组中，并在保证相似性的前提下尽量减少组数（能合并就合并）。"
            "只输出严格的 JSON，结构如下：\n"
            "{""groups"": [[int, int, ...], ...], ""group_tags"": [string, ...]}\n"
            "说明：\n"
            "- groups: 每个子数组为一个组，元素是句子的 index。必须覆盖所有 index 且不重复。\n"
            "- 组数不超过 max_groups。\n"
            "- group_tags: 可选，长度与组数一致，给出每个组的简短标签(<=12个字)，便于调试与解释。\n"
            "- 只输出 JSON，不要任何额外文字。"
        )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            temperature=0.0,
        )
        content = resp.choices[0].message.content  # type: ignore[attr-defined]
    except Exception:
        # Network/auth/model errors → fallback
        if debug:
            print("[semantic] API call failed.")
        if strict:
            raise RuntimeError("LLM API call failed in strict mode")
        return _round_robin_timeline(segments, images)

    # Parse and validate groups
    try:
        if debug:
            print("[semantic] request payload (first 5):", json.dumps(payload["sentences"][:5], ensure_ascii=False))
            preview = content if isinstance(content, str) else str(content)
            if len(preview) > 800:
                preview = preview[:800] + " ...<truncated>"
            print("[semantic] raw model output:", preview)
        data = json.loads(content)
        groups = data.get("groups")
        if not isinstance(groups, list) or not groups:
            raise ValueError("invalid groups")

        # Validation and index->group mapping
        index_to_group: Dict[int, int] = {}
        flat: List[int] = []
        for g_idx, g in enumerate(groups):
            if not isinstance(g, list) or not g:
                raise ValueError("group must be non-empty list")
            # Each index must be int within range
            for idx in g:
                if not isinstance(idx, int):
                    raise ValueError("index must be int")
                if idx < 0 or idx >= len(segments):
                    raise ValueError("index out of range")
            flat.extend(g)
            for idx in g:
                if idx in index_to_group:
                    raise ValueError("duplicate index")
                index_to_group[idx] = g_idx

        # Coverage check
        if len(index_to_group) != len(segments):
            raise ValueError("not all indices covered")

        # Contiguity/order check (enforce monotonic, non-reversing images by spans)
        if contiguous:
            # groups must concatenate to [0,1,2,...,N-1]
            if flat != list(range(len(segments))):
                raise ValueError("groups must be consecutive spans covering all indices in order")

        # Optional group tags for debugging/explainability
        group_tags = data.get("group_tags") if isinstance(data, dict) else None
        if debug and isinstance(group_tags, list):
            print("[semantic] group_tags:", group_tags)

    except Exception:
        # Any parsing/validation issue → fallback
        if debug:
            print("[semantic] parse/validate failed.")
        if strict:
            raise RuntimeError("LLM output parse/validate failed in strict mode")
        return _round_robin_timeline(segments, images)

    # Assign images along the timeline in a non-reversing manner.
    # If allocate_all_images is True and we have more images than groups, we
    # distribute multiple images per group proportionally (by duration or count)
    # so that every image is used exactly once in order.
    N_images = len(images)

    # Compute contiguous groups order by first index appearance
    seen_groups_in_order: List[int] = []
    first_seen: Dict[int, int] = {}
    for idx in range(len(segments)):
        g_idx = index_to_group[idx]
        if g_idx not in first_seen:
            first_seen[g_idx] = idx
            seen_groups_in_order.append(g_idx)

    G = len(seen_groups_in_order)

    # Helper to compute per-group weight
    def group_weight(g_idx: int) -> float:
        if allocation_metric == "count":
            return float(len(groups[g_idx]))
        # default: duration
        w = 0.0
        for idx in groups[g_idx]:
            seg = segments[idx]
            w += float(seg["end_sec"] - seg["start_sec"])
        return max(w, 1e-9)

    if not allocate_all_images or N_images <= G:
        # One image per group (some images may be unused if N_images > G)
        group_to_image: Dict[int, str] = {}
        for i, g_idx in enumerate(seen_groups_in_order):
            group_to_image[g_idx] = str(images[i % N_images])
        if debug:
            sizes = {g_idx: len(groups[g_idx]) if isinstance(groups[g_idx], list) else 0 for g_idx in seen_groups_in_order}
            print("[semantic] groups in order:", seen_groups_in_order)
            print("[semantic] sizes:", sizes)

        timeline: List[Dict] = []
        for idx, seg in enumerate(segments):
            g_idx = index_to_group[idx]
            timeline.append(
                {
                    "sentence": seg["sentence"],
                    "start_sec": seg["start_sec"],
                    "end_sec": seg["end_sec"],
                    "duration_sec": seg["end_sec"] - seg["start_sec"],
                    "image_path": group_to_image[g_idx],
                }
            )
        return timeline

    # Proportional allocation: allocate all images across groups
    weights = [group_weight(g_idx) for g_idx in seen_groups_in_order]
    total_w = sum(weights) if sum(weights) > 0 else float(G)
    raw_alloc = [w * N_images / total_w for w in weights]
    base_alloc = [int(x) for x in raw_alloc]

    # Ensure at least 1 per group
    base_alloc = [max(1, x) for x in base_alloc]
    assigned = sum(base_alloc)
    # Adjust to match exactly N_images via largest remainders
    if assigned < N_images:
        remainders = [(i, raw_alloc[i] - (base_alloc[i] - 1)) for i in range(G)]  # bias towards groups with larger raw
        # Correct calculation: remainders should be raw - base
        remainders = [(i, raw_alloc[i] - int(raw_alloc[i])) for i in range(G)]
        remainders.sort(key=lambda x: x[1], reverse=True)
        for i in range(N_images - assigned):
            base_alloc[remainders[i % G][0]] += 1
    elif assigned > N_images:
        # Need to reduce counts, remove from smallest remainders first but keep >=1
        remainders = [(i, raw_alloc[i] - int(raw_alloc[i])) for i in range(G)]
        remainders.sort(key=lambda x: x[1])  # smallest first
        to_remove = assigned - N_images
        j = 0
        while to_remove > 0 and j < len(remainders):
            idx_g = remainders[j][0]
            if base_alloc[idx_g] > 1:
                base_alloc[idx_g] -= 1
                to_remove -= 1
            else:
                j += 1

    if debug:
        print("[semantic] proportional image allocation per group:")
        print("  order:", seen_groups_in_order)
        print("  weights:", weights)
        print("  alloc:", base_alloc, "sum=", sum(base_alloc), "images=", N_images)

    # Build a per-segment image assignment using sub-span split inside each group
    # Prepare the image iterator in order
    image_iter: List[str] = [str(p) for p in images]
    img_ptr = 0

    timeline: List[Dict] = []
    for g_pos, g_idx in enumerate(seen_groups_in_order):
        k = base_alloc[g_pos]  # images for this group
        seg_indices = groups[g_idx]
        # Compute per-segment durations
        durs = [float(segments[i]["end_sec"] - segments[i]["start_sec"]) for i in seg_indices]
        total_d = sum(durs)
        if total_d <= 0:
            # fallback to equal by count
            total_d = float(len(seg_indices))
            durs = [1.0 for _ in seg_indices]

        # Determine thresholds for k subspans
        targets = [total_d * (t + 1) / k for t in range(k)]
        cur = 0.0
        t_idx = 0
        current_image = image_iter[img_ptr % N_images]
        img_ptr += 1

        for local_idx, seg_i in enumerate(seg_indices):
            cur += durs[local_idx]
            # Append with current image
            seg = segments[seg_i]
            timeline.append(
                {
                    "sentence": seg["sentence"],
                    "start_sec": seg["start_sec"],
                    "end_sec": seg["end_sec"],
                    "duration_sec": seg["end_sec"] - seg["start_sec"],
                    "image_path": current_image,
                }
            )
            # If we've reached the target for this subspan and have more images for this group, advance image
            if t_idx < k - 1 and cur >= targets[t_idx]:
                current_image = image_iter[img_ptr % N_images]
                img_ptr += 1
                t_idx += 1

    return timeline


# --- Greedy similarity-based assignment (no external AI required) ---

_PUNCT_WS = set("\t\n\r ,.?!:;，。？！：；、（）()[]{}'\"\-—_·`~@#$%^&*+=|/\\<>")


def _normalize_text(s: str) -> str:
    return "".join(ch for ch in s.strip() if ch not in _PUNCT_WS)


def _char_ngrams(s: str, n: int = 2) -> Counter:
    s = _normalize_text(s)
    if len(s) < n:
        return Counter({s: 1}) if s else Counter()
    return Counter(s[i : i + n] for i in range(len(s) - n + 1))


def _cosine_sim(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    inter = set(a) & set(b)
    dot = sum(a[k] * b[k] for k in inter)
    na = sum(v * v for v in a.values()) ** 0.5
    nb = sum(v * v for v in b.values()) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def build_timeline_greedy(
    segments: List[Dict],
    image_folder: str,
    *,
    threshold: float = 0.5,
    ngram: int = 2,
    group_context: int = 3,
    debug: bool = False,
) -> List[Dict]:
    """Greedy, online assignment: reuse same image if text is similar.

    Rules
    -----
    - Iterate sentences in time order.
    - If current sentence is similar (>= threshold) to the recent context of the
      last-used group, keep using that group's image.
    - Else, if there are unused images left, advance to the next new image and
      start a new group.
    - Else, pick the most similar existing group; if all similarities are below
      threshold, fall back to the most recently used group.

    Parameters
    ----------
    threshold: float in [0,1]
        Similarity cutoff for staying in the same group.
    ngram: int
        Character n-gram size (2 or 3 recommended for Chinese-like text).
    group_context: int
        Use up to this many most recent sentences in a group as its context.
    """
    images = sorted(Path(image_folder).glob("*"))
    if not images:
        raise FileNotFoundError("No images found in image folder")
    if not segments:
        return []

    # Groups: list of dicts with sentences history and assigned image
    groups: List[Dict] = []
    group_image_index: List[int] = []  # index into images
    last_group_idx: Optional[int] = None
    next_image_idx = 0

    # Helper to compute group context ngram counter
    def group_vector(g_idx: int) -> Counter:
        texts = groups[g_idx]["sentences"][-group_context:]
        cnt = Counter()
        for t in texts:
            cnt += _char_ngrams(t, n=ngram)
        return cnt

    # Cached vectors for efficiency
    group_vec_cache: Dict[int, Counter] = {}

    timeline: List[Dict] = []
    for i, seg in enumerate(segments):
        text = seg.get("sentence", "")
        vec = _char_ngrams(text, n=ngram)

        chosen_group: Optional[int] = None

        if last_group_idx is not None:
            # Try to keep the same group if sufficiently similar
            gv = group_vec_cache.get(last_group_idx)
            if gv is None:
                gv = group_vector(last_group_idx)
                group_vec_cache[last_group_idx] = gv
            sim_last = _cosine_sim(vec, gv)
            if debug:
                print(f"[greedy] #{i} sim to last group {last_group_idx}: {sim_last:.3f}")
            if sim_last >= threshold:
                chosen_group = last_group_idx

        if chosen_group is None:
            # If not similar to last group, either open a new group (new image)
            # or pick the most similar among existing groups
            if next_image_idx < len(images):
                # Start a new group with a fresh image
                chosen_group = len(groups)
                groups.append({"sentences": [text]})
                group_image_index.append(next_image_idx)
                group_vec_cache[chosen_group] = _char_ngrams(text, n=ngram)
                next_image_idx += 1
            else:
                # Compare to all existing groups; pick the best match
                best_idx = None
                best_sim = -1.0
                for g_idx in range(len(groups)):
                    gv = group_vec_cache.get(g_idx)
                    if gv is None:
                        gv = group_vector(g_idx)
                        group_vec_cache[g_idx] = gv
                    sim = _cosine_sim(vec, gv)
                    if debug:
                        print(f"[greedy] #{i} sim to group {g_idx}: {sim:.3f}")
                    if sim > best_sim:
                        best_sim = sim
                        best_idx = g_idx
                if best_idx is not None and best_sim >= threshold:
                    chosen_group = best_idx
                else:
                    # Fallback: stick with last group (topic drift but no clear match)
                    chosen_group = last_group_idx if last_group_idx is not None else 0

        # Update chosen group with current text
        if chosen_group < len(groups):
            # Existing group
            groups[chosen_group]["sentences"].append(text)
            # Update cache
            group_vec_cache[chosen_group] = group_vector(chosen_group)
        else:
            # This branch shouldn't happen due to logic above
            groups.append({"sentences": [text]})
            group_image_index.append(min(next_image_idx, len(images) - 1))
            group_vec_cache[chosen_group] = _char_ngrams(text, n=ngram)

        image_path = str(images[group_image_index[chosen_group]])
        if debug:
            print(f"[greedy] #{i} -> group {chosen_group}, image {image_path}")
        timeline.append(
            {
                "sentence": seg["sentence"],
                "start_sec": seg["start_sec"],
                "end_sec": seg["end_sec"],
                "duration_sec": seg["end_sec"] - seg["start_sec"],
                "image_path": image_path,
            }
        )
        last_group_idx = chosen_group

    return timeline
