import sys
import importlib

DEV_SRC = r"C:/Users/Geri/Documents/Projects/CG/Asset-Import-Tool/src"
if DEV_SRC not in sys.path:
    sys.path.append(DEV_SRC)

import asset_nav_panel
import asset_nav_panel.panel
import asset_nav_panel.thumbnails
import asset_nav_panel.icon
import asset_nav_panel.utils

importlib.reload(asset_nav_panel.icon)
importlib.reload(asset_nav_panel.thumbnails)
importlib.reload(asset_nav_panel.utils)
importlib.reload(asset_nav_panel.panel)
importlib.reload(asset_nav_panel)

asset_nav_panel.show()
