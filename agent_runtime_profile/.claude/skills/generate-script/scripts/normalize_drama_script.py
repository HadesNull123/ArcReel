#!/usr/bin/env python3
"""
normalize_drama_script.py - Use Gemini Pro to generate a normalized script

Convert the source/ novel text into a normalized script in Markdown format (step1_normalized_script.md)
for generate_script.py to consume.

Usage:
    python normalize_drama_script.py --episode <N>
    python normalize_drama_script.py --episode <N> --source <file>
    python normalize_drama_script.py --episode <N> --dry-run
"""

import argparse
import sys
from pathlib import Path

# 允许从仓库任意工作目录直接运行该脚本
PROJECT_ROOT = Path(__file__).resolve().parents[4]  # .claude/skills/generate-script/scripts -> repo root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import asyncio

from lib.project_manager import ProjectManager
from lib.text_backends.base import TextGenerationRequest, TextTaskType
from lib.text_backends.factory import create_text_backend_for_task


def build_normalize_prompt(
    novel_text: str,
    project_overview: dict,
    style: str,
    characters: dict,
    scenes: dict,
    props: dict,
) -> str:
    """Build the prompt for normalized script generation"""

    char_list = "\n".join(f"- {name}" for name in characters.keys()) or "(None)"
    scene_list = "\n".join(f"- {name}" for name in scenes.keys()) or "(None)"
    prop_list = "\n".join(f"- {name}" for name in props.keys()) or "(None)"

    return f"""Your task is to adapt the original novel text into a structured storyboard scene table (Markdown format) for subsequent AI video generation.

## Project Information

<overview>
{project_overview.get("synopsis", "")}

Genre: {project_overview.get("genre", "")}
Core Theme: {project_overview.get("theme", "")}
World Setting: {project_overview.get("world_setting", "")}
</overview>

<style>
{style}
</style>

<characters>
{char_list}
</characters>

<scenes>
{scene_list}
</scenes>

<props>
{prop_list}
</props>

## Original Novel

<novel>
{novel_text}
</novel>

## Output Requirements

Adapt the novel into a scene list using the following Markdown table format:

| Scene ID | Scene Description | Duration | Scene Type | segment_break |
|---------|---------|------|---------|---------------|
| E{{N}}S01 | Detailed scene description... | 8 | Plot | Yes |
| E{{N}}S02 | Detailed scene description... | 8 | Dialogue | No |

Rules:
- Scene ID format: E{{Episode Number}}S{{Two-digit sequence}} (e.g., E1S01, E1S02)
- Scene Description: Adapted scripted description, including character actions, dialogue, and environment, suitable for visual presentation
- Duration: 4, 6, or 8 seconds (default is 8 seconds, simple shots can use 4 or 6 seconds)
- Scene Type: Plot, Action, Dialogue, Transition, B-Roll
- segment_break: Mark "Yes" for scene transition points, mark "No" for the same continuous scene
- Each scene should be an independent visual shot that can be completed within the specified duration
- Avoid having multiple different actions or camera switches in a single scene

Only output the Markdown table, do not include any other explanatory text.
"""


def main():
    parser = argparse.ArgumentParser(
        description="Use Gemini Pro to generate normalized script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s --episode 1
    %(prog)s --episode 1 --source source/chapter1.txt
    %(prog)s --episode 1 --dry-run
        """,
    )

    parser.add_argument("--episode", "-e", type=int, required=True, help="Episode number")
    parser.add_argument(
        "--source",
        "-s",
        type=str,
        default=None,
        help="Specify source novel file path (defaults to reading all files in source/ dir)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Only show Prompt, do not call API")

    args = parser.parse_args()

    pm, project_name = ProjectManager.from_cwd()
    project_path = pm.get_project_path(project_name)
    project = pm.load_project(project_name)

    if args.source:
        source_path = (project_path / args.source).resolve()
        if not source_path.is_relative_to(project_path.resolve()):
            print(f"❌ Path is outside project directory: {source_path}")
            sys.exit(1)
        if not source_path.exists():
            print(f"❌ Source file not found: {source_path}")
            sys.exit(1)
        novel_text = source_path.read_text(encoding="utf-8")
    else:
        source_dir = project_path / "source"
        if not source_dir.exists() or not any(source_dir.iterdir()):
            print(f"❌ source/ directory is empty or does not exist: {source_dir}")
            sys.exit(1)
        texts = []
        for f in sorted(source_dir.iterdir()):
            if f.suffix in (".txt", ".md", ".text"):
                texts.append(f.read_text(encoding="utf-8"))
        novel_text = "\n\n".join(texts)

    if not novel_text.strip():
        print("❌ Source novel is empty")
        sys.exit(1)

    # 构建 Prompt
    prompt = build_normalize_prompt(
        novel_text=novel_text,
        project_overview=project.get("overview", {}),
        style=project.get("style", ""),
        characters=project.get("characters", {}),
        scenes=project.get("scenes", {}),
        props=project.get("props", {}),
    )

    if args.dry_run:
        print("=" * 60)
        print("DRY RUN - The following Prompt will be sent to Gemini:")
        print("=" * 60)
        print(prompt)
        print("=" * 60)
        print(f"\nPrompt length: {len(prompt)} characters")
        return

    async def _run():
        backend = await create_text_backend_for_task(TextTaskType.SCRIPT)
        print(f"Generating normalized script using {backend.model}...")
        result = await backend.generate(TextGenerationRequest(prompt=prompt, max_output_tokens=16000))
        return result.text

    response = asyncio.run(_run())

    drafts_dir = project_path / "drafts" / f"episode_{args.episode}"
    drafts_dir.mkdir(parents=True, exist_ok=True)

    step1_path = drafts_dir / "step1_normalized_script.md"
    step1_path.write_text(response.strip(), encoding="utf-8")
    print(f"✅ Normalized script saved: {step1_path}")

    lines = [
        line
        for line in response.split("\n")
        if line.strip().startswith("|") and "Scene ID" not in line and "---" not in line
    ]
    scene_count = len(lines)
    print(f"\n📊 Generation stats: {scene_count} scenes")


if __name__ == "__main__":
    main()
