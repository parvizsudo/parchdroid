#!/usr/bin/env python3
"""
Android App Support for Parch Linux
A professional GTK4/Adwaita application for managing Waydroid
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio
import sys
import signal
import os
import gettext
import locale

from core.paths import get_locale_dir
gettext.install('parchdroid', get_locale_dir())

from ui.main_window import MainWindow

class AndroidAppSupportApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id='com.parchlinux.parchdroid',
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.window = None
        
    def do_activate(self):
        """Called when the application is activated"""
        if not self.window:
            self.window = MainWindow(application=self)
        self.window.present()
        
    def do_startup(self):
        """Called on application startup"""
        Adw.Application.do_startup(self)
        
        # Setup keyboard shortcuts
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Ctrl>Q"])

def main():
    """Main entry point"""
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = AndroidAppSupportApp()
    return app.run(sys.argv)

if __name__ == '__main__':
    sys.exit(main())
