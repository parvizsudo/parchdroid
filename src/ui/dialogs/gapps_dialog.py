"""
Google Play Services Certification Assistant Dialog
"""
import webbrowser
import threading
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, GLib
from gettext import gettext as _
from core.paths import get_ui_path

class GappsRegistrationDialog:
    """Handles Google Play certification and automated Android ID extraction."""

    def __init__(self, parent_window, waydroid_manager):
        self.parent_window = parent_window
        self.manager = waydroid_manager

        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_ui_path("dialog_gapps.ui"))
        self.dialog = self.builder.get_object("ParchdroidGappsDialog")
        if self.dialog is None:
            # Fallback if class template isn't automatically bound as an instance
            objects = self.builder.get_objects()
            for obj in objects:
                if isinstance(obj, Adw.Dialog):
                    self.dialog = obj
                    break

        self.copy_id_button = self.builder.get_object("copy_id_button")
        self.open_portal_button = self.builder.get_object("open_portal_button")
        self.docs_button = self.builder.get_object("docs_button")
        self.id_row = self.builder.get_object("id_row")

        self.setup_signals()

    def setup_signals(self):
        if self.copy_id_button:
            self.copy_id_button.connect("clicked", self.on_copy_id_clicked)
        if self.open_portal_button:
            self.open_portal_button.connect("clicked", self.on_open_portal_clicked)
        if self.docs_button:
            self.docs_button.connect("clicked", self.on_docs_clicked)

    def on_copy_id_clicked(self, button):
        """Extract Android ID in background and copy to clipboard."""
        self.copy_id_button.set_sensitive(False)
        if self.id_row:
            self.id_row.set_subtitle(_("Querying Android database…"))

        def extract_task():
            android_id = self.manager.get_android_id() if self.manager else None
            GLib.idle_add(self.on_id_extracted, android_id)

        threading.Thread(target=extract_task, daemon=True).start()

    def on_id_extracted(self, android_id):
        self.copy_id_button.set_sensitive(True)
        if android_id:
            # Copy to clipboard
            clipboard = Gdk.Display.get_default().get_clipboard()
            clipboard.set(str(android_id))
            if self.id_row:
                self.id_row.set_subtitle(f"{_('Copied to clipboard:')} {android_id}")
            self.parent_window.show_toast(_("Android ID copied to clipboard!"))
        else:
            if self.id_row:
                self.id_row.set_subtitle(_("Could not fetch ID. Ensure Waydroid session is running."))
            self.parent_window.show_toast(_("Failed to fetch Android ID. Is Waydroid running?"))

    def on_open_portal_clicked(self, button):
        webbrowser.open("https://www.google.com/android/uncertified/")
        self.parent_window.show_toast(_("Opening Google registration page…"))

    def on_docs_clicked(self, button):
        webbrowser.open("https://docs.waydro.id/faq/google-play-certification")
        self.parent_window.show_toast(_("Opening Waydroid documentation…"))

    def present(self):
        if self.dialog:
            self.dialog.present(self.parent_window)
