try:    # older DCC versions
    from PySide2 import QtWidgets, QtCore, QtGui
except: # newer DCC versions
    from PySide6 import QtWidgets, QtCore, QtGui
import os
from .utils import flat_thumbnail_name



class CustomIconProvider(QtWidgets.QFileIconProvider):
    """
    Custom file icon provider that replaces default file icons
    with thumbnail images when available.
    
    Parameters:
        thumbnail_root (str): Directory containing generated thumbnails.
        icon_size (int): Target size (width/height) for displayed icons.
    """
    def __init__(self, thumbnail_root, icon_size=96):
        super().__init__()
        self.thumbnail_root = thumbnail_root
        self.icon_size = icon_size

    def icon(self, fileInfo):
        """
        Returns a QIcon for the given QFileInfo.
        If a matching thumbnail exists, it is loaded and scaled.
        Otherwise, falls back to the default icon provider.
        """

        # Ensure we are handling a file (not a directory)
        if  isinstance(fileInfo, QtCore.QFileInfo) and fileInfo.isFile():
            file_path = fileInfo.absoluteFilePath()
            name = flat_thumbnail_name(file_path)
            thumb_path = os.path.join(self.thumbnail_root, name)
            
            # Check if thumbnail file exists
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
                
        # Fallback to default icon behavior
        return super().icon(fileInfo)
