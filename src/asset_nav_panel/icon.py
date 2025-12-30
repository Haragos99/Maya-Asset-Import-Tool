try:    # older DCC versions
    from PySide2 import QtWidgets, QtCore, QtGui
except: # newer DCC versions
    from PySide6 import QtWidgets, QtCore, QtGui
import os
from .utils import flat_thumbnail_name

class CustomIconProvider(QtWidgets.QFileIconProvider):
    def __init__(self, thumbnail_root, icon_size=96):
        super().__init__()
        self.thumbnail_root = thumbnail_root
        self.icon_size = icon_size

    def icon(self, fileInfo):
        if  isinstance(fileInfo, QtCore.QFileInfo) and fileInfo.isFile():
            file_path = fileInfo.absoluteFilePath()
            name = flat_thumbnail_name(file_path)
            thumb_path = os.path.join(self.thumbnail_root, name)
            
            if os.path.exists(thumb_path):
                pix = QtGui.QPixmap(thumb_path)
                if not pix.isNull():
                    pix = pix.scaled(
                        self.icon_size,
                        self.icon_size,
                        QtCore.Qt.KeepAspectRatio,
                        QtCore.Qt.SmoothTransformation
                    )
                    return QtGui.QIcon(pix)

        return super().icon(fileInfo)
