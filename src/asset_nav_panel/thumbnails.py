import maya.cmds as cmds
import os

def save_thumbnail_png(model_path, png_path, size=256):
    """
    Import a model and save a single PNG thumbnail.

    :param model_path: path to .obj / .fbx / .ma
    :param png_path: output .png path
    :param size: width/height of thumbnail
    """

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
    cmds.select(clear=True)
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



def playblast_movie(movie_path, size=256, start=1, end=24):
    cmds.playblast(
        filename=movie_path,
        format="avi",
        compression="none",
        startTime=start,
        endTime=end,
        width=size,
        height=size,
        viewer=False,
        offScreen=True,
        forceOverwrite=True,
        showOrnaments=False
    )


def save_gif_thumbnail(
    model_path,
    gif_path,
    size= 800,
    frames=24
):
    """
    Import a model and save a single GIF thumbnail.

    :param model_path: path to .obj / .fbx / .ma
    :param gif_path: output .png path
    :param size: width/height of thumbnail
    :param frames: frames of  thr gif
    """
    temp_movie = gif_path
    cmds.file(new=True, force=True)
    cmds.file(model_path, i=True, ignoreVersion=True)

    meshes = cmds.ls(type="mesh")
    if not meshes:
        raise RuntimeError("No geometry found")

    transform = cmds.listRelatives(meshes[0], parent=True)[0]

    cmds.select(transform)
    cmds.viewFit()

    # Turntable
    cmds.currentTime(1)
    cmds.setKeyframe(transform, attribute="rotateY", value=0)
    cmds.currentTime(frames)
    cmds.setKeyframe(transform, attribute="rotateY", value=360)
    cmds.select(clear=True)
    # Movie
    playblast_movie(temp_movie, size, 1, frames)

