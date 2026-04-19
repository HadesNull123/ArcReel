"""
script_models.py - 剧本数据模型

使用 Pydantic 定义剧本的数据结构，用于：
1. Gemini API 的 response_schema（Structured Outputs）
2. 输出验证
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

# ============ 枚举类型定义 ============

ShotType = Literal[
    "Extreme Close-up",
    "Close-up",
    "Medium Close-up",
    "Medium Shot",
    "Medium Long Shot",
    "Long Shot",
    "Extreme Long Shot",
    "Over-the-shoulder",
    "Point-of-view",
]

CameraMotion = Literal[
    "Static",
    "Dolly In",
    "Dolly Out",
    "Pan",
    "Tracking",
    "Boom/Crane",
    "Orbit",
    "Snap Zoom",
    "Handheld Shake",
    "Steadicam",
]

TransitionType = Literal[
    "cut",
    "fade",
    "dissolve",
    "wipe",
    "match_cut",
]


class Dialogue(BaseModel):
    """对话条目"""

    speaker: str = Field(description="Speaker name")
    line: str = Field(description="Dialogue content")


class Composition(BaseModel):
    """构图信息"""

    shot_type: ShotType = Field(description="Shot type")
    lighting: str = Field(description="Lighting description, including light source, direction, and atmosphere")
    ambiance: str = Field(description="Overall ambiance, matching the emotional tone")


class ImagePrompt(BaseModel):
    """分镜图生成 Prompt"""

    scene: str = Field(description="Scene description: character position, expression, action, and environmental details")
    composition: Composition = Field(description="Composition info")


class VideoPrompt(BaseModel):
    """视频生成 Prompt"""

    action: str = Field(description="Action description: specific character actions in this segment")
    camera_motion: CameraMotion = Field(description="Camera motion")
    ambiance_audio: str = Field(description="Ambient audio: describe only in-scene sounds, NO BGM")
    dialogue: list[Dialogue] = Field(default_factory=list, description="List of dialogues, fill ONLY if the original text contains quoted dialogues")


class GeneratedAssets(BaseModel):
    """生成资源状态（初始化为空）"""

    storyboard_image: str | None = Field(default=None, description="Storyboard image path")
    storyboard_last_image: str | None = Field(default=None, description="Storyboard last frame path")
    grid_id: str | None = Field(default=None, description="Associated grid generation ID")
    grid_cell_index: int | None = Field(default=None, description="Cell index in the grid")
    video_clip: str | None = Field(default=None, description="Video clip path")
    video_uri: str | None = Field(default=None, description="Video URI")
    status: Literal["pending", "storyboard_ready", "completed"] = Field(default="pending", description="Generation status")


# ============ 说书模式（Narration） ============


class NarrationSegment(BaseModel):
    """说书模式的片段"""

    segment_id: str = Field(description="Segment ID, format E{episode}S{sequence} or E{episode}S{sequence}_{subsequence}")
    episode: int = Field(description="Episode number")
    duration_seconds: int = Field(ge=1, le=60, description="Segment duration (seconds)")
    segment_break: bool = Field(default=False, description="Whether this is a scene break")
    novel_text: str = Field(description="Original novel text (MUST be kept exactly as-is, used for narration dubbing)")
    characters_in_segment: list[str] = Field(description="List of character names appearing in the segment")
    scenes: list[str] = Field(default_factory=list, description="List of scene names appearing in the segment")
    props: list[str] = Field(default_factory=list, description="List of prop names appearing in the segment")
    image_prompt: ImagePrompt = Field(description="Image generation prompt")
    video_prompt: VideoPrompt = Field(description="Video generation prompt")
    transition_to_next: TransitionType = Field(default="cut", description="Transition type")
    note: str | None = Field(default=None, description="User note (not used for generation)")
    generated_assets: GeneratedAssets = Field(default_factory=GeneratedAssets, description="Generated assets status")


class NovelInfo(BaseModel):
    """小说来源信息"""

    title: str = Field(description="Novel title")
    chapter: str = Field(description="Chapter name")


class NarrationEpisodeScript(BaseModel):
    """说书模式剧集脚本"""

    episode: int = Field(description="Episode number")
    title: str = Field(description="Episode title")
    content_mode: Literal["narration"] = Field(default="narration", description="Content mode")
    duration_seconds: int = Field(default=0, description="Total duration (seconds)")
    summary: str = Field(description="Episode summary")
    novel: NovelInfo = Field(description="Novel source info")
    segments: list[NarrationSegment] = Field(description="List of segments")


# ============ 剧集动画模式（Drama） ============


class DramaScene(BaseModel):
    """剧集动画模式的场景"""

    scene_id: str = Field(description="Scene ID, format E{episode}S{sequence} or E{episode}S{sequence}_{subsequence}")
    duration_seconds: int = Field(default=8, ge=1, le=60, description="Scene duration (seconds)")
    segment_break: bool = Field(default=False, description="Whether this is a scene break")
    scene_type: str = Field(default="剧情", description="Scene type")
    characters_in_scene: list[str] = Field(description="List of character names appearing in the segment")
    scenes: list[str] = Field(default_factory=list, description="List of scene names appearing in the segment")
    props: list[str] = Field(default_factory=list, description="List of prop names appearing in the segment")
    image_prompt: ImagePrompt = Field(description="Image generation prompt")
    video_prompt: VideoPrompt = Field(description="Video generation prompt")
    transition_to_next: TransitionType = Field(default="cut", description="Transition type")
    note: str | None = Field(default=None, description="User note (not used for generation)")
    generated_assets: GeneratedAssets = Field(default_factory=GeneratedAssets, description="Generated assets status")


class DramaEpisodeScript(BaseModel):
    """剧集动画模式剧集脚本"""

    episode: int = Field(description="Episode number")
    title: str = Field(description="Episode title")
    content_mode: Literal["drama"] = Field(default="drama", description="Content mode")
    duration_seconds: int = Field(default=0, description="Total duration (seconds)")
    summary: str = Field(description="Episode summary")
    novel: NovelInfo = Field(description="Novel source info")
    scenes: list[DramaScene] = Field(description="List of scenes")


# ============ 参考生视频模式（Reference Video） ============


class Shot(BaseModel):
    """参考视频单元内的一个镜头。"""

    duration: int = Field(ge=1, le=15, description="Shot duration (seconds)")
    text: str = Field(description="Shot description, can contain @character/@scene/@prop references")


class ReferenceResource(BaseModel):
    """参考图引用——只存名称 + 类型，具体路径从 project.json 对应 bucket 读时解析。"""

    type: Literal["character", "scene", "prop"] = Field(description="Referenced resource type")
    name: str = Field(description="Character/scene/prop name, must be registered in the corresponding project.json bucket")


class ReferenceVideoUnit(BaseModel):
    """参考视频单元——一个视频文件的最小生成粒度。"""

    unit_id: str = Field(description="Format E{episode}U{sequence}")
    shots: list[Shot] = Field(min_length=1, max_length=4, description="1-4 shots")
    references: list[ReferenceResource] = Field(
        default_factory=list,
        description="Determines [Image N] numbering in order",
    )
    duration_seconds: int = Field(description="Derived field: sum of all shot durations")
    duration_override: bool = Field(default=False, description="Stop auto-derivation when true")
    transition_to_next: TransitionType = Field(default="cut", description="Transition type")
    note: str | None = Field(default=None, description="User note")
    generated_assets: GeneratedAssets = Field(default_factory=GeneratedAssets, description="Generated assets status")

    @model_validator(mode="after")
    def _check_duration_consistency(self) -> "ReferenceVideoUnit":
        if not self.duration_override:
            expected = sum(s.duration for s in self.shots)
            if self.duration_seconds != expected:
                raise ValueError(
                    f"duration_seconds ({self.duration_seconds}) 与 shots 总时长 ({expected}) 不符；"
                    "如需手动指定请置 duration_override=True"
                )
        return self


class ReferenceVideoScript(BaseModel):
    """参考生视频模式剧集脚本。"""

    episode: int = Field(description="Episode number")
    title: str = Field(description="Episode title")
    content_mode: Literal["reference_video"] = Field(default="reference_video", description="Content mode")
    duration_seconds: int = Field(default=0, description="Total duration (seconds)")
    summary: str = Field(description="Episode summary")
    novel: NovelInfo = Field(description="Novel source info")
    video_units: list[ReferenceVideoUnit] = Field(description="List of video units")
