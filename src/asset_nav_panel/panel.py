from .folder_nav import FolderNavWidget
from .folder_controller import FolderNavController


# Module-level instance
_panel_instance = None
_controller_instance = None


def show():
    """
    Show the asset navigation panel.
    Creates UI widget and controller.
    
    Returns:
        FolderNavWidget instance
    """
    global _panel_instance, _controller_instance
    
    # Clean up existing instances
    if _panel_instance:
        try:
            _panel_instance.deleteLater()
        except Exception:
            pass
        _panel_instance = None
        _controller_instance = None

    # Create UI
    _panel_instance = FolderNavWidget()
    
    # Create controller and connect to UI
    _controller_instance = FolderNavController(ui=_panel_instance)
    
    # Show panel
    _panel_instance.show()
    
    return _panel_instance
