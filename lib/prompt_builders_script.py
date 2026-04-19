"""
prompt_builders_script.py - Script Generation Prompt Builders

1. Use XML tags to separate context
2. Clear field descriptions and constraints
3. Restrict outputs using optional value lists
"""


def _format_character_names(characters: dict) -> str:
    """Format character list"""
    lines = []
    for name in characters.keys():
        lines.append(f"- {name}")
    return "\n".join(lines)


def _format_asset_names(assets: dict) -> str:
    """Format scene or prop list"""
    lines = []
    for name in assets.keys():
        lines.append(f"- {name}")
    return "\n".join(lines)


def _format_duration_constraint(supported_durations: list[int], default_duration: int | None) -> str:
    """Generate duration constraint description based on parameters."""
    durations_str = ", ".join(str(d) for d in supported_durations)
    if default_duration is not None:
        return f"Duration: Choose from [{durations_str}] seconds, default is {default_duration} seconds"
    return f"Duration: Choose from [{durations_str}] seconds, decide based on content pacing"


def _format_aspect_ratio_desc(aspect_ratio: str) -> str:
    """Return composition description based on aspect ratio."""
    if aspect_ratio == "9:16":
        return "Portrait composition"
    elif aspect_ratio == "16:9":
        return "Landscape composition"
    return f"{aspect_ratio} composition"


def build_narration_prompt(
    project_overview: dict,
    style: str,
    style_description: str,
    characters: dict,
    scenes: dict,
    props: dict,
    segments_md: str,
    supported_durations: list[int] | None = None,
    default_duration: int | None = None,
    aspect_ratio: str = "9:16",
    target_language: str = "English",
) -> str:
    """
    Build Narration Mode Prompt

    Args:
        project_overview: Project overview (synopsis, genre, theme, world_setting)
        style: Visual style tags
        style_description: Style description
        characters: Character dictionary (used to extract name list)
        scenes: Scene dictionary (used to extract name list)
        props: Prop dictionary (used to extract name list)
        segments_md: Step 1 Markdown content
        target_language: Target language for output

    Returns:
        Constructed Prompt string
    """
    character_names = list(characters.keys())
    scene_names = list(scenes.keys())
    prop_names = list(props.keys())

    prompt = f"""Your task is to generate a storyboard script for a short video. Please carefully follow these instructions:

**IMPORTANT: All output content MUST use {target_language}. Only JSON keys and enum values use English.**

1. You will be provided with a story overview, visual style, character list, scene list, prop list, and split novel segments.

2. For each segment, generate:
   - image_prompt: Image generation prompt for the first frame (in {target_language})
   - video_prompt: Video generation prompt for actions and sound effects (in {target_language})

<overview>
{project_overview.get("synopsis", "")}

Genre: {project_overview.get("genre", "")}
Core Theme: {project_overview.get("theme", "")}
World Setting: {project_overview.get("world_setting", "")}
</overview>

<style>
Style: {style}
Description: {style_description}
</style>

<characters>
{_format_character_names(characters)}
</characters>

<scenes>
{_format_asset_names(scenes)}
</scenes>

<props>
{_format_asset_names(props)}
</props>

<segments>
{segments_md}
</segments>

'segments' is the split segment table. Each line is a segment containing:
- Segment ID: Format is E{{Episode}}S{{Sequence}}
- Original Text: Must be preserved exactly as is in the novel_text field
- {_format_duration_constraint(supported_durations or [4, 6, 8], default_duration)}
- Has Dialogue: Used to determine if video_prompt.dialogue needs to be filled
- Is segment_break: Scene transition point, requires segment_break to be true

3. When generating for each segment, follow these 【Cinematic Storyboarding & Camera Rules】:
   - 【180-Degree Rule】: The left/right positioning of characters in dialogue scenes must remain consistent. Do not cross the axis (jump the line) in continuous shots. Reverse shots must be taken over-the-shoulder.
   - 【Psychological Perspective Rule】: When showing a dominant/oppressive/majestic character, use Low Angle; when showing a weak/fearful/small character, use High Angle; use Eye-level for equal dialogue.
   - 【Camera Filming Scope Logic】: Only describe visual elements that the camera can actually see. For Close-ups or single reverse shots, NEVER describe other characters not in the frame in the 'scene' or 'action' fields, to avoid video model hallucinations.
   - 【Creative Match Cut Rule】: For emotional shifts or location changes, intelligently design match cuts (e.g., zoom in to a character's face/object, then cut to a similar shape/object in the next scene, and zoom out).
   - 【Shot Diversity & Coverage】: Ensure high shot diversity within a sequence (Wide establishing shot -> Medium dialogue -> Close-up reactions). Split narrative beats into multiple varied camera angles to maintain cinematic pacing.

a. **novel_text**: Copy the original novel text exactly, without any modifications.

b. **characters_in_segment**: List the names of the characters appearing in this segment.
   - Optional values: [{", ".join(character_names)}]
   - Only include characters explicitly mentioned or clearly implied

c. **scenes**: List the names of the scenes (spatial locations) involved in this segment.
   - Optional values: [{", ".join(scene_names)}]
   - Only include scenes explicitly mentioned or clearly implied

d. **props**: List the names of the props (objects) involved in this segment.
   - Optional values: [{", ".join(prop_names)}]
   - Only include props explicitly mentioned or clearly implied

e. **image_prompt**: Generate an object containing the following fields:
   - scene: Describe in {target_language} the specific scene in the current frame—character positions, postures, expressions, clothing details, and visible environmental elements and objects.
     Focus on the visible picture at the current moment. Only describe specific visual elements that the camera can capture.
     Ensure the description avoids elements outside the current frame. Exclude metaphors, abstract emotional words, subjective evaluations, multi-scene transitions, and other descriptions that cannot be directly rendered.
     The picture should be self-contained, without implying past events or future developments.
   - composition:
     - shot_type: Shot type (Extreme Close-up, Close-up, Medium Close-up, Medium Shot, Medium Long Shot, Long Shot, Extreme Long Shot, Over-the-shoulder, Point-of-view)
     - lighting: Describe the specific light source type, direction, and color temperature in {target_language} (e.g., "warm yellow morning light coming through the left window")
     - ambiance: Describe visible environmental effects in {target_language} (e.g., "misty", "dust flying"), avoid abstract emotional words
     - vfx: Describe any visual effects visible in the frame (e.g., magical glowing, fire, lasers) in {target_language}. If none, leave empty.

f. **video_prompt**: Generate an object containing the following fields:
   - action: Precisely describe in {target_language} the specific actions of the subject during this duration (head, hands, body movements) and micro-expressions.
     Note: Try to use 【Age+Gender】 (e.g., "young woman", "middle-aged man") to refer to the subject character to improve the video model's understanding.
     【Dynamics First Principle】: Purely static descriptions are forbidden! The video cannot be stiff.
     - Micro-expression library (for precise facial generation): tightly furrowed brows, reddened eyes, dilated pupils, raised eyebrows, one corner of mouth raised, tightly pursed lips, dodging gaze, etc. Do not use vague terms (like "serious expression").
     - Character action library: Even in dialogue scenes, micro-actions must be added (nodding, turning head, tapping desk, walking, leaning closer).
     Focus on a single continuous action, ensuring it can be completed within the specified duration. Exclude multi-scene transitions or metaphorical descriptions.
   - camera_motion: Camera movement (Static, Dolly In, Dolly Out, Pan, Tracking, Boom/Crane, Orbit, Snap Zoom, Handheld Shake, Steadicam)
     【Camera Move Selection Rules】:
     - Character moving = MUST use Tracking or Pan, Static is forbidden.
     - Observing environment = Use Pan to simulate gaze.
     - Emotional climax = Dolly In, Orbit, or Snap Zoom (only once).
     - Close-up shots = MUST and CAN ONLY use Static, as movement exposes other parts.
     - Consecutive segments cannot always use the same camera move (especially consecutive Dolly Ins).
   - ambiance_audio: Describe in {target_language} the diegetic sound—ambient sounds, footsteps, object sounds.
     Only describe sounds that genuinely exist within the scene. Exclude music, BGM, narration, voiceovers.
   - dialogue: Array of {{speaker, line}}. Fill in only when there is quoted dialogue in the original text. speaker must come from characters_in_segment.
   - vfx_motion: Describe the dynamic behavior of visual effects (e.g., aura pulsating, explosion expanding) in {target_language}. If none, leave empty.

g. **segment_break**: Set to true if marked as "Yes" in the segment table.

h. **duration_seconds**: Use the duration from the segment table.

i. **transition_to_next**: Default is "cut".

Goal: Create vivid, visually consistent storyboard prompts for AI image and video generation. Keep it creative, specific, and faithful to the original text.
"""
    return prompt


def build_drama_prompt(
    project_overview: dict,
    style: str,
    style_description: str,
    characters: dict,
    scenes: dict,
    props: dict,
    scenes_md: str,
    supported_durations: list[int] | None = None,
    default_duration: int | None = None,
    aspect_ratio: str = "16:9",
    target_language: str = "English",
) -> str:
    """
    Build Drama Animation Mode Prompt

    Args:
        project_overview: Project overview
        style: Visual style tags
        style_description: Style description
        characters: Character dictionary
        scenes: Scene dictionary (project-level scene assets)
        props: Prop dictionary
        scenes_md: Step 1 Markdown storyboard split content
        target_language: Target language for output

    Returns:
        Constructed Prompt string
    """
    character_names = list(characters.keys())
    scene_names = list(scenes.keys())
    prop_names = list(props.keys())

    prompt = f"""Your task is to generate a storyboard script for a drama animation. Please carefully follow these instructions:

**IMPORTANT: All output content MUST use {target_language}. Only JSON keys and enum values use English.**

1. You will be provided with a story overview, visual style, character list, scene list, prop list, and split storyboard shots.

2. For each shot, generate:
   - image_prompt: Image generation prompt for the first frame (in {target_language})
   - video_prompt: Video generation prompt for actions and sound effects (in {target_language})

<overview>
{project_overview.get("synopsis", "")}

Genre: {project_overview.get("genre", "")}
Core Theme: {project_overview.get("theme", "")}
World Setting: {project_overview.get("world_setting", "")}
</overview>

<style>
Style: {style}
Description: {style_description}
</style>

<characters>
{_format_character_names(characters)}
</characters>

<project_scenes>
{_format_asset_names(scenes)}
</project_scenes>

<props>
{_format_asset_names(props)}
</props>

<shots>
{scenes_md}
</shots>

'shots' is the storyboard split table. Each line is a shot containing:
- Shot ID: Format is E{{Episode}}S{{Sequence}}
- Shot Description: Adapted storyboard content from script
- {_format_duration_constraint(supported_durations or [4, 6, 8], default_duration)}
- Scene Type: Plot, Action, Dialogue, etc.
- Is segment_break: Scene transition point, requires segment_break to be true

3. When generating for each shot, follow these 【Cinematic Storyboarding & Camera Rules】:
   - 【180-Degree Rule】: The left/right positioning of characters in dialogue scenes must remain consistent. Do not cross the axis (jump the line) in continuous shots. Reverse shots must be taken over-the-shoulder.
   - 【Psychological Perspective Rule】: When showing a dominant/oppressive/majestic character, use Low Angle; when showing a weak/fearful/small character, use High Angle; use Eye-level for equal dialogue.
   - 【Camera Filming Scope Logic】: Only describe visual elements that the camera can actually see. For Close-ups or single reverse shots, NEVER describe other characters not in the frame in the 'scene' or 'action' fields, to avoid video model hallucinations.
   - 【Creative Match Cut Rule】: For emotional shifts or location changes, intelligently design match cuts (e.g., zoom in to a character's face/object, then cut to a similar shape/object in the next scene, and zoom out).
   - 【Shot Diversity & Coverage】: Ensure high shot diversity within a sequence (Wide establishing shot -> Medium dialogue -> Close-up reactions). Split narrative beats into multiple varied camera angles to maintain cinematic pacing.

a. **characters_in_scene**: List the names of the characters appearing in this shot.
   - Optional values: [{", ".join(character_names)}]
   - Only include characters explicitly mentioned or clearly implied

b. **scenes**: List the names of the scenes (spatial locations) where this shot takes place.
   - Optional values: [{", ".join(scene_names)}]
   - Only include scenes explicitly mentioned or clearly implied

c. **props**: List the names of the props (objects) involved in this shot.
   - Optional values: [{", ".join(prop_names)}]
   - Only include props explicitly mentioned or clearly implied

d. **image_prompt**: Generate an object containing the following fields:
   - scene: Describe in {target_language} the specific scene in the current frame—character positions, postures, expressions, clothing details, and visible environmental elements and objects. {_format_aspect_ratio_desc(aspect_ratio)}.
     Focus on the visible picture at the current moment. Only describe specific visual elements that the camera can capture.
     Ensure the description avoids elements outside the current frame. Exclude metaphors, abstract emotional words, subjective evaluations, multi-scene transitions, and other descriptions that cannot be directly rendered.
     The picture should be self-contained, without implying past events or future developments.
   - composition:
     - shot_type: Shot type (Extreme Close-up, Close-up, Medium Close-up, Medium Shot, Medium Long Shot, Long Shot, Extreme Long Shot, Over-the-shoulder, Point-of-view)
     - lighting: Describe the specific light source type, direction, and color temperature in {target_language} (e.g., "warm yellow morning light coming through the left window")
     - ambiance: Describe visible environmental effects in {target_language} (e.g., "misty", "dust flying"), avoid abstract emotional words
     - vfx: Describe any visual effects visible in the frame (e.g., magical glowing, fire, lasers) in {target_language}. If none, leave empty.

e. **video_prompt**: Generate an object containing the following fields:
   - action: Precisely describe in {target_language} the specific actions of the subject during this duration (head, hands, body movements) and micro-expressions.
     Note: Try to use 【Age+Gender】 (e.g., "young woman", "middle-aged man") to refer to the subject character to improve the video model's understanding.
     【Dynamics First Principle】: Purely static descriptions are forbidden! The video cannot be stiff.
     - Micro-expression library (for precise facial generation): tightly furrowed brows, reddened eyes, dilated pupils, raised eyebrows, one corner of mouth raised, tightly pursed lips, dodging gaze, etc. Do not use vague terms (like "serious expression").
     - Character action library: Even in dialogue scenes, micro-actions must be added (nodding, turning head, tapping desk, walking, leaning closer).
     Focus on a single continuous action, ensuring it can be completed within the specified duration. Exclude multi-scene transitions or metaphorical descriptions.
   - camera_motion: Camera movement (Static, Dolly In, Dolly Out, Pan, Tracking, Boom/Crane, Orbit, Snap Zoom, Handheld Shake, Steadicam)
     【Camera Move Selection Rules】:
     - Character moving = MUST use Tracking or Pan, Static is forbidden.
     - Observing environment = Use Pan to simulate gaze.
     - Emotional climax = Dolly In, Orbit, or Snap Zoom (only once).
     - Close-up shots = MUST and CAN ONLY use Static, as movement exposes other parts.
     - Consecutive segments cannot always use the same camera move (especially consecutive Dolly Ins).
   - ambiance_audio: Describe in {target_language} the diegetic sound—ambient sounds, footsteps, object sounds.
     Only describe sounds that genuinely exist within the scene. Exclude music, BGM, narration, voiceovers.
   - dialogue: Array of {{speaker, line}}. Contains character dialogue. speaker must come from characters_in_scene.
   - vfx_motion: Describe the dynamic behavior of visual effects (e.g., aura pulsating, explosion expanding) in {target_language}. If none, leave empty.

f. **segment_break**: Set to true if marked as "Yes" in the shot table.

g. **duration_seconds**: Use the duration from the shot table.

h. **scene_type**: Use the scene type from the shot table, default is "plot".

i. **transition_to_next**: Default is "cut".

Goal: Create vivid, visually consistent storyboard prompts for AI image and video generation. Keep it creative, specific, and suitable for {_format_aspect_ratio_desc(aspect_ratio)} animation presentation.
"""
    return prompt
