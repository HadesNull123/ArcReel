"""Grid prompt builder for grid-image-to-video feature."""

from __future__ import annotations

from math import gcd


def _extract_image_desc(scene: dict) -> str:
    """Extract image description from a scene.

    If image_prompt is a dict, join scene + composition fields.
    If string, return as-is.
    """
    image_prompt = scene.get("image_prompt", "")
    if isinstance(image_prompt, dict):
        parts = []
        scene_text = image_prompt.get("scene", "")
        if scene_text:
            parts.append(scene_text)
        composition = image_prompt.get("composition", {})
        if isinstance(composition, dict):
            comp_parts = [f"{k}: {v}" for k, v in composition.items() if v]
            if comp_parts:
                parts.append(", ".join(comp_parts))
        return "; ".join(parts) if parts else ""
    return str(image_prompt)


def _extract_action(scene: dict) -> str:
    """Extract closing action from video_prompt.

    If dict, return action field. If string, return as-is.
    """
    video_prompt = scene.get("video_prompt", "")
    if isinstance(video_prompt, dict):
        return str(video_prompt.get("action", ""))
    return str(video_prompt)


def _compute_panel_aspect(grid_aspect_ratio: str, rows: int, cols: int) -> str:
    """Calculate the aspect ratio of a single cell from the overall grid aspect ratio.

    Example: grid 4:3, 3 rows 2 cols -> panel (4/2):(3/3) = 2:1
    """
    gw, gh = (int(x) for x in grid_aspect_ratio.split(":"))
    pw = gw * rows
    ph = gh * cols
    g = gcd(pw, ph)
    return f"{pw // g}:{ph // g}"


def build_grid_prompt(
    *,
    scenes: list[dict],
    id_field: str,
    rows: int,
    cols: int,
    style: str,
    aspect_ratio: str = "16:9",
    grid_aspect_ratio: str | None = None,
    reference_image_mapping: dict[str, str] | None = None,
    target_language: str = "English",
) -> str:
    """Assemble a grid image generation prompt with first-last frame chain structure.

    Args:
        scenes: List of scene dicts with image_prompt and video_prompt fields.
        id_field: Key in each scene dict for the scene ID.
        rows: Number of rows in the grid.
        cols: Number of columns in the grid.
        style: Style description for the grid.
        aspect_ratio: Aspect ratio for each cell (default "16:9").
        grid_aspect_ratio: Overall aspect ratio for the entire grid.
        reference_image_mapping: Optional mapping of image labels to character names.
        target_language: The language the AI should output the prompt text in.

    Returns:
        Assembled prompt string.
    """
    total = rows * cols
    n_scenes = len(scenes)

    n_content = n_scenes

    effective_grid_ar = grid_aspect_ratio or aspect_ratio
    panel_ar = _compute_panel_aspect(effective_grid_ar, rows, cols)

    lines: list[str] = []

    # Header
    lines.append(
        f"You are a professional storyboard artist. Please strictly generate a {rows}x{cols} grid layout image containing exactly {total} equally sized panels."
    )
    lines.append("")

    # Layout requirements
    lines.append("【Layout Requirements】")
    lines.append(f"- Exactly {rows} rows and {cols} columns, {total} panels in total. Reading order: Left to Right, Top to Bottom.")
    lines.append(f"- Overall image aspect ratio: {effective_grid_ar}")
    lines.append(f"- Each panel's aspect ratio: {panel_ar}. All panels must be exactly the same size.")
    lines.append("- Panels must be tightly packed with NO borders, NO gaps, and NO white space between them.")
    lines.append("- Do NOT merge panels, omit panels, or misalign panels.")
    lines.append("- All panels must maintain consistent character appearance, lighting, and color grading style.")
    lines.append("")

    # Frame chain rhythm
    lines.append("【Frame Chain Rhythm】")
    lines.append("This grid uses a chained first-to-last frame structure:")
    lines.append("- Panel 0 is the opening frame of the first scene.")
    lines.append(f"- Panels 1 to {n_content - 1} are transition frames between adjacent scenes (The end of the previous scene = The start of the next scene).")
    lines.append("- Adjacent panels should depict a natural transition and continuation of action.")
    lines.append("")

    # Reference images (optional)
    if reference_image_mapping:
        lines.append("【Reference Image Mapping】")
        for label, character in reference_image_mapping.items():
            lines.append(f"- {label}: {character}")
        lines.append("")

    # Cell contents
    lines.append("【Panel Content】")
    lines.append(f"CRITICAL: Write all the detailed panel descriptions in {target_language}.")
    lines.append("")

    for cell_idx in range(total):
        row_num = cell_idx // cols + 1
        col_num = cell_idx % cols + 1
        position = f"row {row_num} col {col_num}"

        if cell_idx == 0:
            # First scene opening
            scene = scenes[0]
            scene_id = scene.get(id_field, "")
            image_desc = _extract_image_desc(scene)
            lines.append(f"Panel {cell_idx} ({position}) — {scene_id} Opening:")
            lines.append(f"  {image_desc}")

        elif cell_idx < n_scenes:
            # Transition between scenes[cell_idx-1] and scenes[cell_idx]
            prev_scene = scenes[cell_idx - 1]
            next_scene = scenes[cell_idx]
            prev_scene_id = prev_scene.get(id_field, "")
            next_scene_id = next_scene.get(id_field, "")
            prev_action = _extract_action(prev_scene)
            next_image_desc = _extract_image_desc(next_scene)
            lines.append(f"Panel {cell_idx} ({position}) — Transition from {prev_scene_id} to {next_scene_id}:")
            lines.append(f"  Action from previous scene: {prev_action}, seamlessly transitioning into: {next_image_desc}")

        else:
            # Placeholder
            lines.append(f"Panel {cell_idx} ({position}) — Placeholder:")
            lines.append("  Solid gray background, completely empty with no content.")

    lines.append("")

    # Style requirements
    lines.append("【Style Requirements】")
    lines.append(style)
    lines.append("")

    # Negative constraints
    lines.append("【Negative Prompts (MUST AVOID)】")
    lines.append("DO NOT include any of the following elements:")
    lines.append("- Text, subtitles, labels, titles, numbers, or timestamps.")
    lines.append("- Watermarks, logos, or signatures.")
    lines.append("- White borders, black borders, thick borders, or decorative frames.")
    lines.append("- Divider lines, gaps, spacing, white space, padding, or margin between panels.")
    lines.append("- Solid white background or solid color bars.")
    lines.append("- Merged panels, missing panels, or misaligned panels.")
    lines.append("- A continuous panoramic image (un-paneled) or a single large image.")
    lines.append("- Blurriness, low resolution, or noise.")
    lines.append("- Collage feel or unnatural montage stitching.")
    lines.append("- Inconsistent panel sizes or aspect ratios.")

    return "\n".join(lines)
