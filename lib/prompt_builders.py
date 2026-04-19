"""
统一的图像生成 Prompt 构建函数

所有 Prompt 模板集中在此文件管理，确保 WebUI 和 Skill 使用相同的逻辑。

模块职责:
- 角色设计图 Prompt 构建
- 场景设计图 Prompt 构建
- 道具设计图 Prompt 构建
- 分镜图 Prompt 后缀

使用方:
- server/routers/generate.py
- agent_runtime_profile/.claude/skills/generate-assets/
"""


def build_character_prompt(name: str, description: str, style: str = "", style_description: str = "") -> str:
    """
    构建角色设计图 Prompt

    遵循 nano-banana 最佳实践：使用叙事性段落描述，而非关键词列表。

    Args:
        name: 角色名称
        description: 角色外貌描述（应为叙事性段落）
        style: 项目风格
        style_description: AI 分析的风格描述

    Returns:
        完整的 Prompt 字符串
    """
    style_part = f"，{style}" if style else ""

    # 构建风格前缀
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
    构建道具设计图 Prompt

    使用三视图构图：正面全视图、45度侧视图、细节特写。

    Args:
        name: 道具名称
        description: 道具描述
        style: 项目风格
        style_description: AI 分析的风格描述

    Returns:
        完整的 Prompt 字符串
    """
    style_suffix = f"，{style}" if style else ""

    # 构建风格前缀
    style_prefix = ""
    if style_description:
        style_prefix = f"Visual style: {style_description}\n\n"

    return f"""{style_prefix}A professional prop design reference image{style_suffix}.

Multi-angle display of the prop "{name}". {description}

Three views arranged horizontally on a pure light gray background: full front view on the left, 45-degree side view in the middle to show three-dimensionality, and key detail close-up on the right. Soft and even studio lighting, high-definition texture, accurate colors."""


def build_scene_prompt(name: str, description: str, style: str = "", style_description: str = "") -> str:
    """
    构建场景设计图 Prompt

    使用 3/4 主画面 + 右下角细节特写的构图，强调空间结构与氛围。

    Args:
        name: 场景名称
        description: 场景描述
        style: 项目风格
        style_description: AI 分析的风格描述

    Returns:
        完整的 Prompt 字符串
    """
    style_suffix = f"，{style}" if style else ""

    # 构建风格前缀
    style_prefix = ""
    if style_description:
        style_prefix = f"Visual style: {style_description}\n\n"

    return f"""{style_prefix}A professional scene design reference image{style_suffix}.

Visual reference for the iconic scene "{name}". {description}

The main image occupies three-quarters of the area showing the overall appearance and atmosphere of the environment, with a small image in the lower right corner for detail close-ups. Soft natural lighting."""


def build_storyboard_suffix(content_mode: str = "narration", *, aspect_ratio: str | None = None) -> str:
    """
    获取分镜图 Prompt 后缀

    优先使用 aspect_ratio 参数；若未传，按 content_mode 推导（向后兼容）。
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
    构建风格描述 Prompt 片段

    合并 style（用户手动填写）和 style_description（AI 分析生成）。

    Args:
        project_data: project.json 数据

    Returns:
        风格描述字符串，用于拼接到生成 Prompt 中
    """
    parts = []

    # 基础风格标签
    style = project_data.get("style", "")
    if style:
        parts.append(f"Style: {style}")

    # AI 分析的风格描述
    style_description = project_data.get("style_description", "")
    if style_description:
        parts.append(f"Visual style: {style_description}")

    return "\n".join(parts)
