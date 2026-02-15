"""
Folder Navigation Widget - UI Only
Emits signals for all actions, no business logic.
"""
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
    from PySide2.QtMultimedia import QMediaPlayer, QMediaContent, QAudioOutput
    from PySide2.QtMultimediaWidgets import QVideoWidget
    IS_PYSIDE2 = True

import os
from .icon import CustomIconProvider
from .utils import flat_thumbnail_name, SUPPORTED_EXT, THUMBNAIL_DIR


class FolderNavWidget(QtWidgets.QWidget):
    """
    UI widget for browsing asset folders.
    Emits signals for all actions - controller handles the logic.
    """

    # Signals
    generateRequested = QtCore.Signal()
    analyzeRequested = QtCore.Signal(list)  # list of file paths
    importRequested = QtCore.Signal(str)    # file path to import

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Asset Folder Navigator")
        self.resize(900, 480)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        """Build and configure all UI elements"""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # Top row: path + buttons
        top_row = QtWidgets.QHBoxLayout()
        
        self.path_edit = QtWidgets.QLineEdit()
        self.path_edit.setPlaceholderText("Select a folder or type a path...")
        
        self.browse_btn = QtWidgets.QPushButton("Browse")
        self.gen_all_btn = QtWidgets.QPushButton("Generate Thumbnails")
        self.analyze_btn = QtWidgets.QPushButton("Analyze")

        top_row.addWidget(self.path_edit)
        top_row.addWidget(self.browse_btn)
        top_row.addWidget(self.gen_all_btn)
        top_row.addWidget(self.analyze_btn)

        # Splitter: directory tree | file list
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # Left: Directory Tree
        self.dir_model = QtWidgets.QFileSystemModel()
        self.dir_model.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.AllDirs)
        self.dir_model.setRootPath(QtCore.QDir.rootPath())

        self.tree_view = QtWidgets.QTreeView()
        self.tree_view.setModel(self.dir_model)
        self.tree_view.setRootIndex(self.dir_model.index(QtCore.QDir.homePath()))
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(12)

        for col in (1, 2, 3):
            self.tree_view.setColumnHidden(col, True)

        splitter.addWidget(self.tree_view)

        # Right: File List
        self.file_model = QtWidgets.QFileSystemModel()
        self._icon_provider = CustomIconProvider(
            thumbnail_root=THUMBNAIL_DIR,
            icon_size=96
        )
        self.file_model.setIconProvider(self._icon_provider)

        name_filters = [f"*{ext}" for ext in SUPPORTED_EXT]
        self.file_model.setNameFilters(name_filters)
        self.file_model.setNameFilterDisables(False)
        self.file_model.setRootPath(QtCore.QDir.rootPath())

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

        # Video preview setup
        self._setup_video_preview()

        # Bottom: status
        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.setSpacing(2)
        bottom_layout.setContentsMargins(2, 0, 2, 0)

        self.selected_label = QtWidgets.QLabel("Selected folder: ")
        self.status = QtWidgets.QLabel("")

        self.selected_label.setSizePolicy(
            QtWidgets.QSizePolicy.Maximum,
            QtWidgets.QSizePolicy.Fixed
        )
        self.status.setSizePolicy(
            QtWidgets.QSizePolicy.Maximum,
            QtWidgets.QSizePolicy.Fixed
        )

        bottom_layout.addWidget(self.selected_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.status)

        # Assemble
        main_layout.addLayout(top_row)
        main_layout.addWidget(splitter)
        main_layout.addLayout(bottom_layout)

        self.splitter = splitter

    def _setup_video_preview(self):
        """Setup video preview components"""
        self._video_widget = QVideoWidget(self)
        self._video_widget.setWindowFlags(
            QtCore.Qt.ToolTip | QtCore.Qt.WindowStaysOnTopHint
        )
        self._video_widget.setFixedSize(256, 256)
        self._video_widget.hide()

        self._media_player = QMediaPlayer(self)

        # Audio handling
        if IS_PYSIDE6:
            try:
                self._audio_output = QAudioOutput(self)
                self._audio_output.setVolume(0.0)
                self._media_player.setAudioOutput(self._audio_output)
            except Exception:
                try:
                    self._media_player.setVolume(0)
                except Exception:
                    pass
        else:
            try:
                self._media_player.setVolume(0)
            except Exception:
                pass

        try:
            self._media_player.setVideoOutput(self._video_widget)
        except Exception:
            pass

        if hasattr(self._media_player, "setLoops"):
            try:
                self._media_player.setLoops(QMediaPlayer.Infinite)
            except Exception:
                pass

        # Hover timer
        self._hover_timer = QtCore.QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(150)
        self._hover_timer.timeout.connect(self._on_hover_timeout)

    def _connect_signals(self):
        """Connect internal UI signals"""
        self.gen_all_btn.clicked.connect(lambda: self.generateRequested.emit())
        self.analyze_btn.clicked.connect(self._on_analyze_clicked)
        self.list_view.doubleClicked.connect(self._on_list_double_clicked)
        self.path_edit.returnPressed.connect(self._on_path_entered)
        self.browse_btn.clicked.connect(self._on_browse)
        self.tree_view.selectionModel().currentChanged.connect(self._on_tree_selection_changed)

    # Public methods for controller
    def set_status(self, text):
        """Set status bar text"""
        self.status.setText(text)

    def refresh_icons(self):
        """Refresh file icons"""
        self.file_model.setIconProvider(self._icon_provider)
        self.list_view.viewport().update()

    def get_root_index(self):
        """Get current root index"""
        return self.list_view.rootIndex()

    def get_file_model(self):
        """Get file model"""
        return self.file_model

    def set_folder(self, folder_path):
        """Set current browsing folder"""
        self.path_edit.setText(folder_path)
        self.selected_label.setText(f"Selected folder: {folder_path}")
        
        index = self.dir_model.index(folder_path)
        if index.isValid():
            self.tree_view.setCurrentIndex(index)
            self.tree_view.scrollTo(index)
        
        file_index = self.file_model.index(folder_path)
        if file_index.isValid():
            self.list_view.setRootIndex(file_index)
        
        self.status.setText(f"Found: {self._count_files(folder_path)} files")

    def get_selected_files(self):
        """Get list of selected file paths"""
        paths = []
        for idx in self.list_view.selectedIndexes():
            paths.append(self.file_model.filePath(idx))
        return paths

    # Internal slots
    def _on_browse(self):
        """Handle browse button"""
        start = self.path_edit.text() or QtCore.QDir.homePath()
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Folder", start
        )
        if folder:
            self.set_folder(folder)

    def _on_path_entered(self):
        """Handle path entry"""
        path = self.path_edit.text().strip()
        if os.path.isdir(path):
            self.set_folder(path)
        else:
            self.status.setText(f"Invalid folder: {path}")

    def _on_tree_selection_changed(self, current, previous):
        """Handle tree selection change"""
        path = self.dir_model.filePath(current)
        if path:
            self.set_folder(path)

    def _on_analyze_clicked(self):
        """Handle analyze button"""
        paths = self.get_selected_files()
        if not paths:
            QtWidgets.QMessageBox.information(
                self, "Analyze", "No assets selected."
            )
            return
        self.analyzeRequested.emit(paths)

    def _on_list_double_clicked(self, index):
        """Handle file double-click"""
        path = self.file_model.filePath(index)
        self.status.setText(f"Double-clicked: {os.path.basename(path)}")
        self.importRequested.emit(path)

    def _count_files(self, folder):
        """Count supported files in folder"""
        try:
            files = [
                f for f in os.listdir(folder)
                if os.path.isfile(os.path.join(folder, f))
            ]
            files = [
                f for f in files
                if os.path.splitext(f)[1].lower() in SUPPORTED_EXT
            ]
            return len(files)
        except Exception:
            return 0

    # Video preview methods
    def eventFilter(self, obj, event):
        """Event filter for hover preview"""
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

        return super().eventFilter(obj, event)

    def _on_hover_timeout(self):
        """Timer callback for hover"""
        idx = getattr(self, "_hover_index", None)
        if not idx or not idx.isValid():
            return

        rect = self.list_view.visualRect(idx)
        if not rect.contains(self._last_hover_pos):
            self._hide_video_preview()
            return

        self._show_video_preview(idx)

    def _show_video_preview(self, index):
        """Show video preview"""
        file_path = self.file_model.filePath(index)
        if not os.path.isfile(file_path):
            self._hide_video_preview()
            return

        thumb_name = flat_thumbnail_name(file_path)
        avi_path = os.path.join(THUMBNAIL_DIR, thumb_name) + ".avi"

        if not os.path.exists(avi_path):
            self._hide_video_preview()
            return

        global_pos = self.list_view.viewport().mapToGlobal(self._last_hover_pos)
        self._video_widget.move(global_pos + QtCore.QPoint(16, 16))

        try:
            self._media_player.stop()
        except Exception:
            pass

        try:
            if hasattr(self._media_player, "setSource"):
                self._media_player.setSource(QtCore.QUrl.fromLocalFile(avi_path))
            else:
                try:
                    self._media_player.setMedia(
                        QMediaContent(QtCore.QUrl.fromLocalFile(avi_path))
                    )
                except Exception:
                    try:
                        self._media_player.setMedia(None)
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            self._media_player.play()
            self._video_widget.show()
        except Exception:
            pass

    def _hide_video_preview(self):
        """Hide video preview"""
        try:
            self._media_player.stop()
        except Exception:
            pass

        try:
            if hasattr(self._media_player, "setSource"):
                self._media_player.setSource(QtCore.QUrl())
            else:
                try:
                    self._media_player.setMedia(QMediaContent())
                except Exception:
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