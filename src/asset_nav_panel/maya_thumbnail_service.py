"""
Maya Thumbnail Service
Handles all Maya operations for thumbnail generation.
"""

import maya.cmds as cmds
import os


class MayaThumbnailService:
    """
    Service responsible for generating thumbnails inside Maya.
    
    Responsibilities:
        - Scene reset
        - Model import
        - Camera framing
        - Viewport setup
        - PNG thumbnail generation
        - Turntable movie generation
    """

    def reset_scene(self):
        """Create a new empty scene"""
        cmds.file(new=True, force=True)

    def import_model(self, model_path):
        """Import a 3D model into the scene"""
        ext = os.path.splitext(model_path)[1].lower()

        # Load FBX plugin if needed
        if ext == ".fbx":
            try:
                cmds.loadPlugin("fbxmaya", quiet=True)
            except Exception:
                pass

        cmds.file(model_path, i=True, ignoreVersion=True)

    def find_main_transform(self):
        """Find the main transform node in the scene"""
        meshes = cmds.ls(type="mesh")
        if not meshes:
            raise RuntimeError("No geometry found")

        transform = cmds.listRelatives(meshes[0], parent=True)[0]
        return transform

    def frame_object(self, transform):
        """Frame the object in the viewport"""
        cmds.select(transform)
        cmds.viewFit()
        cmds.select(clear=True)

    def setup_viewport(self):
        """Setup viewport for thumbnail rendering"""
        panels = cmds.getPanel(type="modelPanel")
        if not panels:
            raise RuntimeError("No model panel found")

        panel = panels[0]
        cmds.modelEditor(panel, e=True, grid=False)

    def render_image(self, output_path, size):
        """Render a single frame image"""
        cmds.playblast(
            completeFilename=output_path,
            format="image",
            width=size,
            height=size,
            showOrnaments=False,
            viewer=False,
            offScreen=True,
            forceOverwrite=True
        )

    def render_turntable(self, output_path, size, frames):
        """Render a turntable animation"""
        transform = self.find_main_transform()

        # Set keyframes for rotation
        cmds.currentTime(1)
        cmds.setKeyframe(transform, attribute="rotateY", value=0)
        cmds.currentTime(frames)
        cmds.setKeyframe(transform, attribute="rotateY", value=360)

        # Render movie
        cmds.playblast(
            filename=output_path,
            format="avi",
            compression="none",
            startTime=1,
            endTime=frames,
            width=size,
            height=size,
            viewer=False,
            offScreen=True,
            forceOverwrite=True,
            showOrnaments=False
        )

    # Public API
    def generate_png_thumbnail(self, model_path, png_path, size=256):
        """Generate a PNG thumbnail for a model"""
        self.reset_scene()
        self.import_model(model_path)

        transform = self.find_main_transform()
        self.frame_object(transform)
        self.setup_viewport()

        self.render_image(png_path, size)

    def generate_turntable_movie(self, model_path, movie_path, size=256, frames=24):
        """Generate a turntable movie for a model"""
        self.reset_scene()
        self.import_model(model_path)

        transform = self.find_main_transform()
        self.frame_object(transform)
        self.setup_viewport()

        self.render_turntable(movie_path, size, frames)
    
    def import_file(self, file_path):
        """Import a file into the current scene (for double-click import)"""
        self.import_model(file_path)
  