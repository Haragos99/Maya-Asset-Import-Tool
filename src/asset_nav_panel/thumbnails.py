import maya.cmds as cmds
import os

def save_thumbnail_png(model_path, png_path, size=256):
    """
    Import a model and save a single PNG thumbnail.

    :param model_path: path to .obj / .fbx / .ma
    :param png_path: output .png path
    :param size: width/height of thumbnail
    """

    current_panel = cmds.getPanel(withFocus=True)
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
    cmds.setFocus(current_panel)
    print("Saved thumbnail:", png_path)
