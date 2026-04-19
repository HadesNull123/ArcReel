"""
Unified Image Generation Prompt Builder Functions

All Prompt templates are managed centrally in this file to ensure WebUI and Skills use the same logic.

Module responsibilities:
- Character design prompt building
- Scene design prompt building
- Prop design prompt building
- Storyboard prompt suffix

Used by:
- server/routers/generate.py
- agent_runtime_profile/.claude/skills/generate-assets/
"""


def build_character_prompt(name: str, description: str, style: str = "", style_description: str = "") -> str:
    """
    Build character design prompt

    Follows nano-banana best practices: uses narrative paragraph descriptions instead of keyword lists.

    Args:
        name: Character name
        description: Character appearance description (should be a narrative paragraph)
        style: Project style
        style_description: AI analyzed style description

    Returns:
        Complete Prompt string
    """
    style_part = f", {style}" if style else ""

    # Build style prefix
    style_prefix = ""
    if style_description:
        style_prefix = f"Visual style: {style_description}\n\n"

    return f"""{style_prefix}Character design reference image{style_part}.

Full-body portrait of "{name}".

{description}

Composition requirements: Single character full-body portrait, natural posture, facing the camera.
Background: Pure light gray, no decorative elements.
Lighting: Soft and even studio lighting, no strong shadows.
Image quality: High definition, clear details, accurate colors."""


def build_prop_prompt(name: str, description: str, style: str = "", style_description: str = "") -> str:
    """
    Build prop design prompt

    Uses three-view composition: full front view, 45-degree side view, detail close-up.

    Args:
        name: Prop name
        description: Prop description
        style: Project style
        style_description: AI analyzed style description

    Returns:
        Complete Prompt string
    """
    style_suffix = f", {style}" if style else ""

    # Build style prefix
    style_prefix = ""
    if style_description:
        style_prefix = f"Visual style: {style_description}\n\n"

    return f"""{style_prefix}A professional prop design reference image{style_suffix}.

Multi-angle display of the prop "{name}". {description}

Three views arranged horizontally on a pure light gray background: full front view on the left, 45-degree side view in the middle to show three-dimensionality, and key detail close-up on the right. Soft and even studio lighting, high-definition texture, accurate colors."""


def build_scene_prompt(name: str, description: str, style: str = "", style_description: str = "") -> str:
    """
    Build scene design prompt

    Uses 3/4 main image + bottom right detail close-up composition, emphasizing spatial structure and atmosphere.

    Args:
        name: Scene name
        description: Scene description
        style: Project style
        style_description: AI analyzed style description

    Returns:
        Complete Prompt string
    """
    style_suffix = f", {style}" if style else ""

    # Build style prefix
    style_prefix = ""
    if style_description:
        style_prefix = f"Visual style: {style_description}\n\n"

    return f"""{style_prefix}A professional scene design reference image{style_suffix}.

Visual reference for the iconic scene "{name}". {description}

The main image occupies three-quarters of the area showing the overall appearance and atmosphere of the environment, with a small image in the lower right corner for detail close-ups. Soft natural lighting."""


def build_storyboard_suffix(content_mode: str = "narration", *, aspect_ratio: str | None = None) -> str:
    """
    Get storyboard prompt suffix

    Prefers aspect_ratio parameter; if not passed, infers from content_mode (backward compatibility).
    """
    if aspect_ratio is None:
        ratio = "9:16" if content_mode == "narration" else "16:9"
    else:
        ratio = aspect_ratio
    if ratio == "9:16":
        return "Portrait composition."
    elif ratio == "16:9":
        return "Landscape composition."
    return ""


def build_style_prompt(project_data: dict) -> str:
    """
    Build style description prompt fragment

    Merges style (user manually entered) and style_description (AI analyzed generation).

    Args:
        project_data: project.json data

    Returns:
        Style description string, for appending to the generation Prompt
    """
    parts = []

    # Base style tag
    style = project_data.get("style", "")
    if style:
        parts.append(f"Style: {style}")

    # AI analyzed style description
    style_description = project_data.get("style_description", "")
    if style_description:
        parts.append(f"Visual style: {style_description}")

    return "\n".join(parts)
