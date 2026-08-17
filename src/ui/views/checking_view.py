"""
Checking View - Displayed during system hardware and prerequisite scanning
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from core.paths import get_ui_path

class CheckingView(Adw.Bin):
    """View showing system inspection spinner and message."""

    def __init__(self):
        super().__init__()
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_ui_path("view_checking.ui"))
        
        root = None
        for obj in self.builder.get_objects():
            if isinstance(obj, Adw.StatusPage):
                root = obj
                break
        if not root:
            root = self.builder.get_object("status_page")
            
        self.set_child(root)
