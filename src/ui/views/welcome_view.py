"""
Welcome View - Displayed when Waydroid is not yet installed on the system
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from gettext import gettext as _
from core.paths import get_ui_path

class WelcomeView(Adw.Bin):
    """View shown for initial onboarding and Waydroid installation."""

    def __init__(self, on_install_callback):
        super().__init__()
        self.on_install_callback = on_install_callback

        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_ui_path("view_welcome.ui"))

        # Find the root ScrolledWindow or StatusPage
        root = None
        for obj in self.builder.get_objects():
            if isinstance(obj, Gtk.ScrolledWindow):
                root = obj
                break
        if not root:
            root = self.builder.get_object("status_page")

        self.set_child(root)

        self.repo_row = self.builder.get_object("repo_row")
        self.kernel_row = self.builder.get_object("kernel_row")
        self.install_button = self.builder.get_object("install_button")
        self.install_row = self.builder.get_object("install_row")

        if self.install_button:
            self.install_button.connect("clicked", lambda b: self.on_install_callback())
        if self.install_row:
            self.install_row.set_activatable_widget(self.install_button)

    def update_status(self, result: dict):
        """Update rows based on SystemChecker results."""
        if result.get('system_compatible'):
            self.repo_row.set_subtitle(_("Arch Linux Extra / Official Repository (Ready)"))
            self.install_button.set_sensitive(True)
        else:
            self.repo_row.set_subtitle(_("Non-Arch system detected. Installation not supported."))
            self.install_button.set_sensitive(False)

        if result.get('kernel_modules_ok'):
            self.kernel_row.set_subtitle(_("binder and ashmem kernel modules are available"))
        else:
            self.kernel_row.set_subtitle(_("Missing binder/ashmem kernel modules. Waydroid may require kernel support."))
