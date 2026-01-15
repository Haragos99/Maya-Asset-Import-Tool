
try:    # older DCC versions
    from PySide2 import QtWidgets, QtCore
    from PySide2.QtMultimedia import QMediaPlayer, QAudioOutput
    from PySide2.QtMultimediaWidgets import QVideoWidget
except: # newer DCC versions
    from PySide6 import QtWidgets, QtCore
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PySide6.QtMultimediaWidgets import QVideoWidget

from .icon import CustomIconProvider
from .utils import flat_thumbnail_name, append_error_report, SUPPORTED_EXT, thumbnail_path, error_report_path
from .thumbnails import save_gif_thumbnail, save_thumbnail_png 
import os
import traceback
import datetime
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
import maya.cmds as cmds

class FolderNavWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(FolderNavWidget, self).__init__(parent)
        self.setWindowTitle("Asset Folder Navigator")
        self.resize(900, 480)
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint
        )
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(6,6,6,6)
        main_layout.setSpacing(6)

        # Top row: path field + browse
        top_row = QtWidgets.QHBoxLayout()
        self.path_edit = QtWidgets.QLineEdit()
        self.path_edit.setPlaceholderText("Select a folder or type a path...")
        self.browse_btn = QtWidgets.QPushButton("Browse")
        top_row.addWidget(self.path_edit)
        top_row.addWidget(self.browse_btn)

        self.gen_all_btn = QtWidgets.QPushButton("Generate Thumbnails")
        top_row.addWidget(self.gen_all_btn)

        # Splitter: directory tree | file list
        splitter = QtWidgets.QSplitter()
        splitter.setOrientation(QtCore.Qt.Horizontal)

        # Left: directory tree (QFileSystemModel showing only directories)
        self.dir_model = QtWidgets.QFileSystemModel()
        self.dir_model.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.AllDirs)
        # set root path to filesystem root
        self.dir_model.setRootPath(QtCore.QDir.rootPath())

        self.tree_view = QtWidgets.QTreeView()
        self.tree_view.setModel(self.dir_model)
        self.tree_view.setRootIndex(self.dir_model.index(QtCore.QDir.homePath()))
        # hide unnecessary columns
        self.tree_view.setColumnHidden(1, True)  # Size
        self.tree_view.setColumnHidden(2, True)  # Type
        self.tree_view.setColumnHidden(3, True)  # Date Modified
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(12)
        splitter.addWidget(self.tree_view)

        # Right: file list (QFileSystemModel showing files)
        self.file_model = QtWidgets.QFileSystemModel()
        # after creating self.file_model:
        self._icon_provider = CustomIconProvider(
            thumbnail_root=thumbnail_path,
            icon_size=96
        )
        self.file_model.setIconProvider(self._icon_provider)
        #self.file_model.setFilter(QtCore.QDir.Files | QtCore.QDir.NoDotAndDotDot)


        # Video preview widget (AVI hover preview) 
        self._video_widget = QVideoWidget(self)
        self._video_widget.setWindowFlags(
            QtCore.Qt.ToolTip | QtCore.Qt.WindowStaysOnTopHint
        )
        self._video_widget.setFixedSize(502, 502)
        self._video_widget.hide()

        self._media_player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._audio_output.setVolume(0.0)  # mute
        self._media_player.setAudioOutput(self._audio_output)
        self._media_player.setVideoOutput(self._video_widget)
        self._media_player.setLoops(QMediaPlayer.Infinite)

        # hover timer to avoid flicker
        self._hover_timer = QtCore.QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(100)  # ms delay before showing preview
        self._hover_timer.timeout.connect(self._on_hover_timeout)


        # apply name filter for supported extensions
        name_filters = ["*{}".format(ext) for ext in SUPPORTED_EXT]
        self.file_model.setNameFilters(name_filters)
        self.file_model.setNameFilterDisables(False)
        self.file_model.setRootPath(QtCore.QDir.rootPath())

        self.list_view = QtWidgets.QListView()
        self.list_view.setModel(self.file_model)
        self.list_view.setViewMode(QtWidgets.QListView.IconMode)
        self.list_view.setIconSize(QtCore.QSize(96,96))
        self.list_view.setResizeMode(QtWidgets.QListView.Adjust)
        self.list_view.setSpacing(8)
        self.list_view.setWordWrap(True)
        self.list_view.setGridSize(QtCore.QSize(120, 140))

        self.list_view.setMovement(QtWidgets.QListView.Static)
        # install event filter on the list view viewport
        self.list_view.setMouseTracking(True)
        self.list_view.viewport().installEventFilter(self)
        splitter.addWidget(self.list_view)

        # Bottom: status / selected path
        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.setSpacing(2)                 # space between widgets
        bottom_layout.setContentsMargins(2, 0, 2, 0) # left, top, right, bottom

        self.selected_label = QtWidgets.QLabel("Selected folder: ")
        self.status = QtWidgets.QLabel("")

        bottom_layout.addWidget(self.selected_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.status)


        self.selected_label.setSizePolicy(
            QtWidgets.QSizePolicy.Maximum,
            QtWidgets.QSizePolicy.Fixed
        )
        self.status.setSizePolicy(
            QtWidgets.QSizePolicy.Maximum,
            QtWidgets.QSizePolicy.Fixed
        )


        main_layout.addLayout(top_row)
        main_layout.addWidget(splitter)
        main_layout.addLayout(bottom_layout)

        # expose splitter children for later use
        self.splitter = splitter


    def eventFilter(self, obj, event):
      
        if obj is self.list_view.viewport():
            if event.type() == QtCore.QEvent.MouseMove:
                idx = self.list_view.indexAt(event.pos())
                self._last_hover_pos = event.pos()
                self._hover_timer.stop()
                if idx.isValid():
                    try:
                        self._hover_timer.timeout.disconnect()
                    except TypeError:
                        pass
                    # Store current index
                    self._hover_index = idx

                    self._hover_timer.timeout.connect(self._on_hover_timeout)
                    self._hover_timer.start()
                else:
                    self._hide_video_preview()

            elif event.type() in (QtCore.QEvent.Leave, QtCore.QEvent.FocusOut):
                self._hover_timer.stop()
                self._hide_video_preview()

        return super().eventFilter(obj, event)



    def _hide_video_preview(self):
        self._media_player.stop()
        self._media_player.setSource(QtCore.QUrl())  # clears the source
        self._video_widget.hide()


    def _on_hover_timeout(self):
        # Ensure index still valid and mouse is still over it
        idx = getattr(self, "_hover_index", None)
        if not idx or not idx.isValid():
            return

        rect = self.list_view.visualRect(idx)
        if not rect.contains(self._last_hover_pos):
            self._hide_video_preview()
            return

        self._show_video_preview(idx)


    def _show_video_preview(self, index):
        file_path = self.file_model.filePath(index)
        if not os.path.isfile(file_path):
            self._hide_video_preview()
            return


        thumb_name = flat_thumbnail_name(file_path)
        avi_path = os.path.join(thumbnail_path, thumb_name) + ".avi"

        if not os.path.exists(avi_path):
            self._hide_video_preview()
            return

        # Position near mouse
        global_pos = self.list_view.viewport().mapToGlobal(self._last_hover_pos)
        self._video_widget.move(global_pos + QtCore.QPoint(16, 16))

        # Load & play
        self._media_player.stop()
        self._media_player.setSource(QtCore.QUrl.fromLocalFile(avi_path))
        self._media_player.play()

        self._video_widget.show()


    def _connect_signals(self):
        # Browse button
        self.browse_btn.clicked.connect(self.on_browse)
        # When user clicks a folder in tree, update file list
        self.tree_view.selectionModel().currentChanged.connect(self.on_tree_selection_changed)
        # When user edits path and presses Enter
        self.path_edit.returnPressed.connect(self.on_path_entered)
        # Double-click file (future: import)
        self.list_view.doubleClicked.connect(self.on_file_double_click)
        # Generate all thumbnails button
        self.gen_all_btn.clicked.connect(self.generate_all_thumbnails_flat)
   

    # Slots 
    def on_browse(self):
        start = self.path_edit.text() or QtCore.QDir.homePath()
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder", start)
        if folder:
            self.set_folder(folder)


    def on_path_entered(self):
        path = self.path_edit.text().strip()
        if os.path.isdir(path):
            self.set_folder(path)
        else:
            self.status.setText("Invalid folder: {}".format(path))

    def set_folder(self, folder_path):
        # set path field and select matching index in tree; update file list root
        self.path_edit.setText(folder_path)
        self.selected_label.setText("Selected folder: {}".format(folder_path))
        # find index in dir_model and expand/select it
        index = self.dir_model.index(folder_path)
        if index.isValid():
            self.tree_view.setCurrentIndex(index)
            self.tree_view.scrollTo(index)
        # set file model root to this folder
        file_index = self.file_model.index(folder_path)
        print(file_index.isValid())
        if file_index.isValid():
            self.list_view.setRootIndex(file_index)
        self.status.setText("Found: {} files".format(self._count_files(folder_path)))


    def refresh_icon(self):
        self.file_model.setIconProvider(self._icon_provider)
        self.list_view.viewport().update()


    def generate_all_thumbnails_flat(self, force=False):
        """
        Generate thumbnails for all files in the currently selected folder
        and store them in a flat thumbnail directory.
        """
        os.makedirs(thumbnail_path, exist_ok=True)

        root_index = self.list_view.rootIndex()
        if not root_index.isValid():
            return

        model = self.file_model
        row_count = model.rowCount(root_index)

        # Progress dialog 
        progress = QtWidgets.QProgressDialog(
            "Generating thumbnails...",
            "Cancel",
            0,
            row_count,
            self
        )
        progress.setWindowTitle("Thumbnail Generation")
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.setMinimumDuration(0)  # show immediately
        progress.setValue(0)

        generated = 0
        current_panel = cmds.getPanel(withFocus=True)
        current_widget = QtWidgets.QApplication.focusWidget()
        for row in range(row_count):
            # Allow UI updates + cancel
            QtWidgets.QApplication.processEvents()
            if progress.wasCanceled():
                break

            idx = model.index(row, 0, root_index)
            file_path = model.filePath(idx)
            if not os.path.isfile(file_path):
                progress.setValue(row + 1)
                continue

            thumb_name = flat_thumbnail_name(file_path)
            thumb_path = os.path.join(thumbnail_path, thumb_name)

            if os.path.exists(thumb_path) and not force:
                progress.setValue(row + 1)
                continue

            try:
                save_thumbnail_png(file_path, thumb_path)
                save_gif_thumbnail(file_path, thumb_path + ".avi")
                generated += 1
            except Exception as e:
                print("Thumbnail failed:", file_path, e)
                error_entry = {
                    "maya_version": cmds.about(version=True),
                    "batch_mode": cmds.about(batch=True),
                    "user": os.getlogin(),
                    "model": file_path,
                    "png": thumb_path,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "created_at": datetime.utcnow().isoformat() + "Z"
                }

                append_error_report(error_report_path, error_entry)

            progress.setValue(row + 1)

            def restore_focus():
                if current_panel:
                    cmds.setFocus(current_panel)
                if current_widget:
                    current_widget.setFocus(QtCore.Qt.OtherFocusReason)

        cmds.evalDeferred(restore_focus)

        progress.close()
        self.status.setText("Generated {} thumbnails".format(generated))

        # Clear scene after thumbnail generation
        cmds.file(new=True, force=True)
        self.refresh_icon()


    def on_tree_selection_changed(self, current, previous):
        # current is QModelIndex from dir_model; map to path and update file list view
        path = self.dir_model.filePath(current)
        if path:
            self.set_folder(path)

    def on_file_double_click(self, index):
        # full path of double-clicked file
        file_path = self.file_model.filePath(index)
        print("Double-clicked file:", file_path)
        self.status.setText("Double-clicked: {}".format(os.path.basename(file_path)))
        
        # Smooth shaded view
        cmds.file(file_path, i=True, ignoreVersion=True)
        cmds.select(all=True)
        cmds.displaySurface(all=True)


    def _count_files(self, folder):
        try:
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            # apply extension filter
            files = [f for f in files if os.path.splitext(f)[1].lower() in SUPPORTED_EXT]
            return len(files)
        except Exception:
            return 0


_panel_instance = None

def show():
    global _panel_instance
    try:
        if _panel_instance:
            _panel_instance.close()
    except Exception:
        pass

    _panel_instance = FolderNavWidget()
    _panel_instance.show()
    return _panel_instance