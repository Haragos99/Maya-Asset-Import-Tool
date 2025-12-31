import datetime
from .utils import error_report_path
import traceback
import maya.cmds as cmds
import json
import os

def save_thumbnail_png(model_path, png_path, size=256):
    """
    Import a model and save a single PNG thumbnail.

    :param model_path: path to .obj / .fbx / .ma
    :param png_path: output .png path
    :param size: width/height of thumbnail
    """
    try:
        # New clean scene 
        cmds.file(new=True, force=True)

        ext = os.path.splitext(model_path)[1].lower()
        if ext == ".fbx":
            try:
                cmds.loadPlugin("fbxmaya", quiet=True)
            except Exception:
                pass

        # Import model
        cmds.file(model_path, i=True, ignoreVersion=True)

        # Get geometry
        meshes = cmds.ls(type="mesh")
        if not meshes:
            raise RuntimeError("No geometry found")

        transform = cmds.listRelatives(meshes[0], parent=True)[0]

        # Frame object
        cmds.select(transform)
        cmds.viewFit()

        # Find a model panel
        panel = cmds.getPanel(type="modelPanel")[0]
        cmds.modelEditor(panel, e=True, grid=False)

        # Playblast single frame
        cmds.playblast(
            completeFilename=png_path,
            format="image",
            width=size,
            height=size,
            showOrnaments=False,
            viewer=False,
            offScreen=True,
            forceOverwrite=True
        )    
        print("Saved thumbnail:", png_path)

    except Exception as e:
        error_entry = {
            "maya_version": cmds.about(version=True),
            "batch_mode": cmds.about(batch=True),
            "user": os.getlogin(),
            "model": model_path,
            "png": png_path,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "created_at": datetime.utcnow().isoformat() + "Z"
        }

        append_error_report(error_report_path, error_entry)
        print("Thumbnail failed:", model_path)



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
