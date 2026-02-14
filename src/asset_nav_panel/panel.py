# panel.py (compatible with PySide2 and PySide6)
import os
import traceback
import datetime
import maya.cmds as cmds

# Qt imports with compatibility
IS_PYSIDE6 = False
IS_PYSIDE2 = False
try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PySide6.QtMultimediaWidgets import QVideoWidget
    IS_PYSIDE6 = True
except Exception:
    from PySide2 import QtWidgets, QtCore, QtGui
    from PySide2.QtMultimedia import QMediaPlayer, QMediaContent, QAudioOutput  # QAudioOutput exists but constructor differs
    from PySide2.QtMultimediaWidgets import QVideoWidget
    IS_PYSIDE2 = True

from .icon import CustomIconProvider
from .utils import flat_thumbnail_name, append_error_report, SUPPORTED_EXT, THUMBNAIL_DIR, error_report_path
from .thumbnails import save_gif_thumbnail, save_thumbnail_png
from .analyze_panel import show_analyze_panel

class FolderNavWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(FolderNavWidget, self).__init__(parent)
        self.setWindowTitle("Asset Folder Navigator")
        self.resize(900, 480)

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # Top row: path field + browse + buttons
        top_row = QtWidgets.QHBoxLayout()
        self.path_edit = QtWidgets.QLineEdit()
        self.path_edit.setPlaceholderText("Select a folder or type a path...")
        self.browse_btn = QtWidgets.QPushButton("Browse")
        top_row.addWidget(self.path_edit)
        top_row.addWidget(self.browse_btn)

        self.gen_all_btn = QtWidgets.QPushButton("Generate Thumbnails")
        top_row.addWidget(self.gen_all_btn)

        self.analyze_btn = QtWidgets.QPushButton("Analyze")
        top_row.addWidget(self.analyze_btn)

        # Splitter: directory tree | file list
        splitter = QtWidgets.QSplitter()
        splitter.setOrientation(QtCore.Qt.Horizontal)

        # Left: directory tree
        self.dir_model = QtWidgets.QFileSystemModel()
        self.dir_model.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.AllDirs)
        self.dir_model.setRootPath(QtCore.QDir.rootPath())

        self.tree_view = QtWidgets.QTreeView()
        self.tree_view.setModel(self.dir_model)
        self.tree_view.setRootIndex(self.dir_model.index(QtCore.QDir.homePath()))
        self.tree_view.setColumnHidden(1, True)
        self.tree_view.setColumnHidden(2, True)
        self.tree_view.setColumnHidden(3, True)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(12)
        splitter.addWidget(self.tree_view)

        # Right: file list
        self.file_model = QtWidgets.QFileSystemModel()
        self._icon_provider = CustomIconProvider(
            thumbnail_root=THUMBNAIL_DIR,
            icon_size=96
        )
        self.file_model.setIconProvider(self._icon_provider)

        name_filters = ["*{}".format(ext) for ext in SUPPORTED_EXT]
        self.file_model.setNameFilters(name_filters)
        self.file_model.setNameFilterDisables(False)
        self.file_model.setRootPath(QtCore.QDir.rootPath())

        # Video preview widget (hover)
        self._video_widget = QVideoWidget(self)
        self._video_widget.setWindowFlags(QtCore.Qt.ToolTip | QtCore.Qt.WindowStaysOnTopHint)
        self._video_widget.setFixedSize(256, 256)
        self._video_widget.hide()

        # media player
        self._media_player = QMediaPlayer(self)

        # audio handling: different APIs between PySide2/PySide6
        if IS_PYSIDE6:
            # PySide6: use QAudioOutput
            try:
                self._audio_output = QAudioOutput(self)
                self._audio_output.setVolume(0.0)
                self._media_player.setAudioOutput(self._audio_output)
            except Exception:
                # if QAudioOutput construction fails, fallback to mute via player
                try:
                    self._media_player.setVolume(0)
                except Exception:
                    pass
        else:
            # PySide2: setVolume on QMediaPlayer
            try:
                self._media_player.setVolume(0)
            except Exception:
                pass

        # video output
        try:
            self._media_player.setVideoOutput(self._video_widget)
        except Exception:
            # some older combinations  ignore if fails
            pass

        # loop if supported (PySide6 has setLoops)
        if hasattr(self._media_player, "setLoops"):
            try:
                self._media_player.setLoops(QMediaPlayer.Infinite)
            except Exception:
                pass

        # hover timer (connect once)
        self._hover_timer = QtCore.QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(150)
        self._hover_timer.timeout.connect(self._on_hover_timeout)

        # List view
        self.list_view = QtWidgets.QListView()
        self.list_view.setModel(self.file_model)
        self.list_view.setViewMode(QtWidgets.QListView.IconMode)
        self.list_view.setIconSize(QtCore.QSize(96, 96))
        self.list_view.setResizeMode(QtWidgets.QListView.Adjust)
        self.list_view.setSpacing(8)
        self.list_view.setWordWrap(True)
        self.list_view.setGridSize(QtCore.QSize(120, 140))
        self.list_view.setMovement(QtWidgets.QListView.Static)
        self.list_view.setMouseTracking(True)
        self.list_view.viewport().installEventFilter(self)

        splitter.addWidget(self.list_view)

        # Bottom: status / selected path (compact)
        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.setSpacing(2)
        bottom_layout.setContentsMargins(2, 0, 2, 0)

        self.selected_label = QtWidgets.QLabel("Selected folder: ")
        self.status = QtWidgets.QLabel("")

        bottom_layout.addWidget(self.selected_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.status)

        self.selected_label.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        self.status.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)

        # assemble layout
        main_layout.addLayout(top_row)
        main_layout.addWidget(splitter)
        main_layout.addLayout(bottom_layout)

        # expose
        self.splitter = splitter

    # event filter: no connect/disconnect inside, just set hover index and start timer
    def eventFilter(self, obj, event):
        if obj is self.list_view.viewport():
            if event.type() == QtCore.QEvent.MouseMove:
                idx = self.list_view.indexAt(event.pos())
                self._last_hover_pos = event.pos()
                self._hover_timer.stop()
                if idx.isValid():
                    self._hover_index = idx
                    self._hover_timer.start()
                else:
                    self._hover_index = None
                    self._hide_video_preview()

            elif event.type() in (QtCore.QEvent.Leave, QtCore.QEvent.FocusOut):
                self._hover_timer.stop()
                self._hover_index = None
                self._hide_video_preview()

        return super(FolderNavWidget, self).eventFilter(obj, event)

    def _hide_video_preview(self):
        try:
            self._media_player.stop()
        except Exception:
            pass

        # Clear media safely across PySide versions
        try:
            if hasattr(self._media_player, "setSource"):
                # PySide6
                self._media_player.setSource(QtCore.QUrl())
            else:
                # PySide2: QMediaContent is in QtMultimedia
                try:
                    # QMediaContent was imported above for PySide2
                    self._media_player.setMedia(QMediaContent())
                except Exception:
                    # last-resort: set an empty url via setMedia if signature allows
                    try:
                        self._media_player.setMedia(None)
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            self._video_widget.hide()
        except Exception:
            pass


    def _on_hover_timeout(self):
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
        avi_path = os.path.join(THUMBNAIL_DIR, thumb_name) + ".avi"

        if not os.path.exists(avi_path):
            self._hide_video_preview()
            return

        # Position near mouse
        global_pos = self.list_view.viewport().mapToGlobal(self._last_hover_pos)
        self._video_widget.move(global_pos + QtCore.QPoint(16, 16))

        # Load & play (use API appropriate method)
        try:
            self._media_player.stop()
        except Exception:
            pass

        try:
            if hasattr(self._media_player, "setSource"):
                # PySide6
                self._media_player.setSource(QtCore.QUrl.fromLocalFile(avi_path))
            else:
                # PySide2: wrap in QMediaContent
                try:
                    self._media_player.setMedia(QMediaContent(QtCore.QUrl.fromLocalFile(avi_path)))
                except Exception:
                    # fallback: try setMedia with None then setMedia with QUrl if supported
                    try:
                        self._media_player.setMedia(None)
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            self._media_player.play()
        except Exception:
            pass

        try:
            self._video_widget.show()
        except Exception:
            pass

    def _connect_signals(self):
        self.browse_btn.clicked.connect(self.on_browse)
        self.tree_view.selectionModel().currentChanged.connect(self.on_tree_selection_changed)
        self.path_edit.returnPressed.connect(self.on_path_entered)
        self.list_view.doubleClicked.connect(self.on_file_double_click)
        self.gen_all_btn.clicked.connect(self.generate_all_thumbnails_flat)
        self.analyze_btn.clicked.connect(self.on_analyze_clicked)

    # Slots and other methods kept largely unchanged (trimmed here for brevity)
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
    # 
    def set_folder(self, folder_path):
        self.path_edit.setText(folder_path)
        self.selected_label.setText("Selected folder: {}".format(folder_path))
        index = self.dir_model.index(folder_path)
        if index.isValid():
            self.tree_view.setCurrentIndex(index)
            self.tree_view.scrollTo(index)
        file_index = self.file_model.index(folder_path)
        if file_index.isValid():
            self.list_view.setRootIndex(file_index)
        self.status.setText("Found: {} files".format(self._count_files(folder_path)))

    # refresh the file icons
    def refresh_icon(self):
        self.file_model.setIconProvider(self._icon_provider)
        self.list_view.viewport().update()

    def on_analyze_clicked(self):
        paths = []
        # prefer a selected_list if you have one, otherwise current selection
        for idx in self.list_view.selectedIndexes():
            paths.append(self.file_model.filePath(idx))
        if not paths:
            QtWidgets.QMessageBox.information(self, "Analyze", "No assets selected.")
            return
        print("ANALYZE", paths)
        show_analyze_panel(paths, parent=self)


    # Genereta GIF and PNG thumbnail
    def generate_all_thumbnails_flat(self, force=False):
        os.makedirs(THUMBNAIL_DIR, exist_ok=True)
        root_index = self.list_view.rootIndex()
        if not root_index.isValid():
            return
        model = self.file_model
        row_count = model.rowCount(root_index)

        progress = QtWidgets.QProgressDialog("Generating thumbnails...", "Cancel", 0, row_count, self)
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
            idx = model.index(row, 0, root_index)
            file_path = model.filePath(idx)
            if not os.path.isfile(file_path):
                progress.setValue(row + 1)
                continue
            thumb_name = flat_thumbnail_name(file_path)
            thumb_path = os.path.join(THUMBNAIL_DIR, thumb_name)
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
                    "created_at": datetime.datetime.utcnow().isoformat() + "Z"
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
        cmds.file(new=True, force=True)
        self.refresh_icon()

    def on_tree_selection_changed(self, current):
        path = self.dir_model.filePath(current)
        if path:
            self.set_folder(path)

    def on_file_double_click(self, index):
        file_path = self.file_model.filePath(index)
        print("Double-clicked file:", file_path)
        self.status.setText("Double-clicked: {}".format(os.path.basename(file_path)))
        cmds.file(file_path, i=True, ignoreVersion=True)
        cmds.select(all=True)
        cmds.displaySurface(all=True)

    def _count_files(self, folder):
        try:
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            files = [f for f in files if os.path.splitext(f)[1].lower() in SUPPORTED_EXT]
            return len(files)
        except Exception:
            return 0


_panel_instance = None


def show():
    global _panel_instance
    if _panel_instance:
        try:
            _panel_instance.deleteLater()
        except Exception:
            pass
        _panel_instance = None

    _panel_instance = FolderNavWidget()
    _panel_instance.show()
    return _panel_instance
