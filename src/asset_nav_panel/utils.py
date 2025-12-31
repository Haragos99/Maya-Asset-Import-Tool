
import asset_nav_panel
import os

def flat_thumbnail_name(file_path):
        safe = file_path.replace(":", "").replace("\\", "__").replace("/", "__")
        return safe + ".png"

SUPPORTED_EXT = [".obj", ".fbx", ".ma"]

PROJECT_ROOT = os.path.dirname(os.path.abspath(asset_nav_panel.__file__))
THUMBNAIL_DIR = os.path.join(PROJECT_ROOT, "thumbnails")

print("Project root:", PROJECT_ROOT)
print("Thumbnail folder:", THUMBNAIL_DIR)


thumbnail_path = r"C:/Users/Geri/Documents/Projects/CG/Asset-Import-Tool/thumbnails"
error_report_path = "thumbnail_errors.json"