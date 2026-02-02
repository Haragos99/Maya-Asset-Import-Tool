import sys
import importlib

DEV_SRC = r"PATH_TO_YOUR_DEV_SRC_DIRECTORY"
""" 
This is run only in development environment Open in Maya's script editor and run this file to reload the src files
"""

# Adjust the path to your local src folder
if DEV_SRC not in sys.path:
    sys.path.append(DEV_SRC)

import asset_nav_panel
import asset_nav_panel.panel
import asset_nav_panel.thumbnails
import asset_nav_panel.icon
import asset_nav_panel.utils
import asset_nav_panel.analyze_panel
import asset_nav_panel.analysis


importlib.reload(asset_nav_panel.icon)
importlib.reload(asset_nav_panel.thumbnails)
importlib.reload(asset_nav_panel.utils)
importlib.reload(asset_nav_panel.panel)
importlib.reload(asset_nav_panel)
importlib.reload(asset_nav_panel.analysis)
importlib.reload(asset_nav_panel.analyze_panel)

asset_nav_panel.show()
