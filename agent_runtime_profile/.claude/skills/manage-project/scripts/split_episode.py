#!/usr/bin/env python3
"""
split_episode.py - Execute episode splitting

Uses target word count + anchor text to locate the split point, splitting the novel into episode_N.txt and _remaining.txt.
The target word count narrows the search window, and the anchor text precisely locates the point.

Usage:
    # Dry run (preview only)
    python split_episode.py --source source/novel.txt --episode 1 --target 1000 --anchor "He turned and left." --dry-run

    # Actual execution
    python split_episode.py --source source/novel.txt --episode 1 --target 1000 --anchor "He turned and left."
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _text_utils import find_char_offset


def find_anchor_near_target(text: str, anchor: str, target_offset: int, window: int = 500) -> list[int]:
    """Find anchor text within the window near the target offset, returning a list of matched end offsets (sorted by distance)."""
    search_start = max(0, target_offset - window)
    search_end = min(len(text), target_offset + window)
    search_region = text[search_start:search_end]

    positions = []
    start = 0
    while True:
        idx = search_region.find(anchor, start)
        if idx == -1:
            break
        abs_pos = search_start + idx + len(anchor)  # 锚点末尾的绝对偏移
        positions.append(abs_pos)
        start = idx + 1

    # 按距离 target_offset 排序
    positions.sort(key=lambda p: abs(p - target_offset))
    return positions


def main():
    parser = argparse.ArgumentParser(description="Execute episode splitting")
    parser.add_argument("--source", required=True, help="Source file path")
    parser.add_argument("--episode", required=True, type=int, help="Episode number")
    parser.add_argument("--target", required=True, type=int, help="Target word count (must match the --target of peek)")
    parser.add_argument("--anchor", required=True, help="Text fragment before the split point (10-20 characters)")
    parser.add_argument("--context", default=500, type=int, help="Search window size (default 500 characters)")
    parser.add_argument("--dry-run", action="store_true", help="Only show split preview, do not write file")
    args = parser.parse_args()

    source_path = Path(args.source).resolve()
    if not source_path.is_relative_to(Path.cwd().resolve()):
        print(f"Error: Source file path is outside the current project directory: {source_path}", file=sys.stderr)
        sys.exit(1)
    if not source_path.exists():
        print(f"Error: Source file does not exist: {source_path}", file=sys.stderr)
        sys.exit(1)

    text = source_path.read_text(encoding="utf-8")

    # 用目标字数计算大致偏移位置
    target_offset = find_char_offset(text, args.target)

    # 在目标偏移附近搜索锚点
    positions = find_anchor_near_target(text, args.anchor, target_offset, window=args.context)

    if len(positions) == 0:
        print(
            f'Error: Could not find anchor text "{args.anchor}" near target word count {args.target} (±{args.context} char window)',
            file=sys.stderr,
        )
        sys.exit(1)

    if len(positions) > 1:
        print(
            f"Warning: Anchor text matched {len(positions)} places within the window. Using the closest match to the target.",
            file=sys.stderr,
        )
        for i, pos in enumerate(positions):
            ctx_start = max(0, pos - len(args.anchor) - 10)
            ctx_end = min(len(text), pos + 10)
            distance = abs(pos - target_offset)
            marker = " ← Selected" if i == 0 else ""
            print(f"  Match {i + 1} (Distance {distance}): ...{text[ctx_start:ctx_end]}...{marker}", file=sys.stderr)

    split_pos = positions[0]
    part_before = text[:split_pos]
    part_after = text[split_pos:]

    preview_len = 50
    before_preview = part_before[-preview_len:] if len(part_before) > preview_len else part_before
    after_preview = part_after[:preview_len] if len(part_after) > preview_len else part_after

    print(f"Target Word Count: {args.target}, Target Offset: {target_offset}")
    print(f"Split Position: at character {split_pos}")
    print(f"End of First Part: ...{before_preview}")
    print(f"Start of Second Part: {after_preview}...")
    print(f"First Part Length: {len(part_before)} characters")
    print(f"Second Part Length: {len(part_after)} characters")

    if args.dry_run:
        print("\n[Dry Run] No files were written. Remove --dry-run to execute if correct.")
        return

    output_dir = source_path.parent
    episode_file = output_dir / f"episode_{args.episode}.txt"
    remaining_file = output_dir / "_remaining.txt"

    episode_file.write_text(part_before, encoding="utf-8")
    remaining_file.write_text(part_after, encoding="utf-8")

    print("\nGenerated:")
    print(f"  {episode_file} ({len(part_before)} characters)")
    print(f"  {remaining_file} ({len(part_after)} characters)")
    print(f"  Original file unmodified: {source_path}")


if __name__ == "__main__":
    main()
