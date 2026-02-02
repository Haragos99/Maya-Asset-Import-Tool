import asset_nav_panel
from pathlib import Path
import json
import os

def flat_thumbnail_name(file_path):
        safe = file_path.replace(":", "").replace("\\", "__").replace("/", "__")
        return safe 


def append_error_report(report_path, entry):
    # Create file if missing
    if not os.path.exists(report_path):
        with open(report_path, "w") as f:
            json.dump([], f, indent=4)

    # Load existing data
    with open(report_path, "r") as f:
        data = json.load(f)

    # Append new entry
    data.append(entry)

    # Write back
    with open(report_path, "w") as f:
        json.dump(data, f, indent=4)


SUPPORTED_EXT = [".obj", ".fbx", ".ma", ".usd"]

PROJECT_ROOT = Path(asset_nav_panel.__file__).resolve().parents[2]
THUMBNAIL_DIR = os.path.join(PROJECT_ROOT, "thumbnails")

print("Project root:", PROJECT_ROOT)
print("Thumbnail folder:", THUMBNAIL_DIR)

error_report_path = PROJECT_ROOT / "thumbnail_errors.json"