# asset_nav_panel/folder_controller.py
"""
Folder Navigation Controller
Handles all business logic and coordinates between UI and services.
"""

# Qt imports with compatibility
try:
    from PySide6 import QtWidgets, QtCore
except Exception:
    from PySide2 import QtWidgets, QtCore

import os
import traceback
import datetime
import maya.cmds as cmds

from .maya_thumbnail_service import MayaThumbnailService
from .analyze_panel import show_analyze_panel
from .utils import (
    THUMBNAIL_DIR,
    flat_thumbnail_name,
    append_error_report,
    error_report_path
)


class FolderNavController:
    """
    Controller for folder navigation.
    Connects UI signals to business logic.
    """

    def __init__(self, ui):
        """
        Initialize controller with UI widget.
        
        Args:
            ui: FolderNavWidget instance
        """
        self.ui = ui
        self.thumb_service = MayaThumbnailService()
        
        self._connect_signals()

    def _connect_signals(self):
        """Connect UI signals to controller methods"""
        self.ui.generateRequested.connect(self.on_generate_thumbnails)
        self.ui.importRequested.connect(self.on_import_file)
        self.ui.analyzeRequested.connect(self.on_analyze_files)

    # -------------------------
    # Import
    # -------------------------
    def on_import_file(self, file_path):
        """
        Handle file import request.
        
        Args:
            file_path: Path to file to import
        """
        try:
            self.thumb_service.import_file(file_path)
            self.ui.set_status(f"Imported: {os.path.basename(file_path)}")
        except Exception as e:
            self.ui.set_status(f"Import failed: {str(e)}")
            print(f"Import error: {e}")

    # -------------------------
    # Analyze
    # -------------------------
    def on_analyze_files(self, paths):
        """
        Handle analyze request.
        
        Args:
            paths: List of file paths to analyze
        """
        try:
            show_analyze_panel(paths, parent=self.ui)
        except Exception as e:
            self.ui.set_status(f"Analysis failed: {str(e)}")
            print(f"Analysis error: {e}")

    # -------------------------
    # Thumbnail Generation
    # -------------------------
    def on_generate_thumbnails(self, force=False):
        """
        Generate thumbnails for all files in current folder.
        
        Args:
            force: If True, regenerate existing thumbnails
        """
        os.makedirs(THUMBNAIL_DIR, exist_ok=True)
        
        root_index = self.ui.get_root_index()
        if not root_index.isValid():
            self.ui.set_status("No folder selected")
            return
        
        file_model = self.ui.get_file_model()
        row_count = file_model.rowCount(root_index)

        # Progress dialog
        progress = QtWidgets.QProgressDialog(
            "Generating thumbnails...",
            "Cancel",
            0,
            row_count,
            self.ui
        )
        progress.setWindowTitle("Thumbnail Generation")
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        generated = 0
        current_panel = cmds.getPanel(withFocus=True)
        current_widget = QtWidgets.QApplication.focusWidget()

        for row in range(row_count):
            QtWidgets.QApplication.processEvents()
            
            if progress.wasCanceled():
                break

            idx = file_model.index(row, 0, root_index)
            file_path = file_model.filePath(idx)

            if not os.path.isfile(file_path):
                progress.setValue(row + 1)
                continue

            thumb_name = flat_thumbnail_name(file_path)
            thumb_path = os.path.join(THUMBNAIL_DIR, thumb_name)

            if os.path.exists(thumb_path) and not force:
                progress.setValue(row + 1)
                continue

            try:
                # Generate PNG thumbnail
                self.thumb_service.generate_png_thumbnail(
                    model_path=file_path,
                    png_path=thumb_path,
                    size=256
                )
                
                # Generate turntable movie
                self.thumb_service.generate_turntable_movie(
                    model_path=file_path,
                    movie_path=thumb_path + ".avi",
                    size=800,
                    frames=24
                )
                
                generated += 1

            except Exception as e:
                print(f"Thumbnail failed: {file_path} - {e}")
                self._log_thumbnail_error(file_path, thumb_path, e)

            progress.setValue(row + 1)

        # Restore focus
        def restore_focus():
            if current_panel:
                cmds.setFocus(current_panel)
            if current_widget:
                current_widget.setFocus(QtCore.Qt.OtherFocusReason)

        cmds.evalDeferred(restore_focus)
        progress.close()

        self.ui.set_status(f"Generated {generated} thumbnails")
        cmds.file(new=True, force=True)
        self.ui.refresh_icons()

    def _log_thumbnail_error(self, file_path, thumb_path, error):
        """
        Log thumbnail generation error to JSON file.
        
        Args:
            file_path: Source model file
            thumb_path: Intended thumbnail path
            error: Exception that occurred
        """
        error_entry = {
            "maya_version": cmds.about(version=True),
            "batch_mode": cmds.about(batch=True),
            "user": os.getlogin(),
            "model": file_path,
            "png": thumb_path,
            "error": str(error),
            "traceback": traceback.format_exc(),
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        append_error_report(error_report_path, error_entry)