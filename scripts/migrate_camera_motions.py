import json
import os
import sys
from pathlib import Path

# Mapping of legacy Chinese Camera Motions to English Cinematic Terms
MOTION_MAP = {
    "静止": "Static",
    "推镜头": "Dolly In",
    "拉镜头": "Dolly Out",
    "左平移": "Pan",
    "右平移": "Pan",
    "推平移": "Pan",
    "上摇": "Boom/Crane",
    "下摇": "Boom/Crane",
    "升降": "Boom/Crane",
    "环绕": "Orbit",
    "跟随": "Tracking",
    "跟随平移": "Tracking",
    "推拉变焦": "Snap Zoom",
    "手持": "Handheld Shake",
    "无人机": "Boom/Crane",
    "复杂运动": "Steadicam",
}

# Mapping of legacy Chinese Shot Types to English Cinematic Terms
SHOT_MAP = {
    "特写": "Close-up",
    "大特写": "Extreme Close-up",
    "近景": "Medium Close-up",
    "中景": "Medium Shot",
    "中远景": "Medium Long Shot",
    "远景": "Long Shot",
    "大远景": "Extreme Long Shot",
    "全景": "Long Shot", # Approximate
    "过肩镜头": "Over-the-shoulder",
    "主观镜头": "Point-of-view",
}


def migrate_script_file(filepath: Path) -> bool:
    """Migrate a single script JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False

    changed = False

    # Check for narration mode segments
    if "segments" in data:
        for segment in data["segments"]:
            if "video_prompt" in segment:
                vp = segment["video_prompt"]
                
                # Check camera_motion
                if "camera_motion" in vp:
                    old_motion = vp["camera_motion"]
                    if old_motion in MOTION_MAP:
                        vp["camera_motion"] = MOTION_MAP[old_motion]
                        changed = True
                
                # Check shot_type
                if "shot_type" in vp:
                    old_shot = vp["shot_type"]
                    if old_shot in SHOT_MAP:
                        vp["shot_type"] = SHOT_MAP[old_shot]
                        changed = True

    # Check for drama mode scenes
    if "scenes" in data:
        for scene in data["scenes"]:
            if "video_prompt" in scene:
                vp = scene["video_prompt"]
                
                # Check camera_motion
                if "camera_motion" in vp:
                    old_motion = vp["camera_motion"]
                    if old_motion in MOTION_MAP:
                        vp["camera_motion"] = MOTION_MAP[old_motion]
                        changed = True
                
                # Check shot_type
                if "shot_type" in vp:
                    old_shot = vp["shot_type"]
                    if old_shot in SHOT_MAP:
                        vp["shot_type"] = SHOT_MAP[old_shot]
                        changed = True

    if changed:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ Migrated: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error writing {filepath}: {e}")
            return False
    else:
        print(f"⏭️ Skipped (already migrated or no matches): {filepath}")
        return False


def main():
    # Detect projects directory
    project_root = Path(__file__).parent.parent
    projects_dir = project_root / "projects"
    
    if not projects_dir.exists():
        print(f"Projects directory not found at {projects_dir}")
        sys.exit(1)

    print(f"Scanning for JSON scripts in {projects_dir}...")
    
    migrated_count = 0
    total_count = 0

    for root, dirs, files in os.walk(projects_dir):
        if "scripts" in root:
            for file in files:
                if file.endswith(".json"):
                    filepath = Path(root) / file
                    total_count += 1
                    if migrate_script_file(filepath):
                        migrated_count += 1

    print(f"\nMigration Complete! Migrated {migrated_count} of {total_count} files.")


if __name__ == "__main__":
    main()
