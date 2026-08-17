"""
Management View - Complete Waydroid Runtime, Session, and Settings Controls
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from gettext import gettext as _
from core.paths import get_ui_path

class ManageView(Adw.Bin):
    """View providing all controls for an installed Waydroid instance."""

    def __init__(self, delegate):
        super().__init__()
        self.delegate = delegate
        self.updating_ui = False
        self.gapps_info_button = None

        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_ui_path("view_manage.ui"))

        root = None
        for obj in self.builder.get_objects():
            if isinstance(obj, Gtk.ScrolledWindow):
                root = obj
                break
        self.set_child(root)

        # Get Widgets
        self.status_banner = self.builder.get_object("status_banner")
        self.launch_row = self.builder.get_object("launch_row")
        self.launch_button = self.builder.get_object("launch_button")
        self.session_switch_row = self.builder.get_object("session_switch_row")
        self.restart_row = self.builder.get_object("restart_row")
        self.restart_button = self.builder.get_object("restart_button")
        self.multi_window_row = self.builder.get_object("multi_window_row")
        self.install_apk_row = self.builder.get_object("install_apk_row")
        self.install_apk_button = self.builder.get_object("install_apk_button")
        self.vanilla_row = self.builder.get_object("vanilla_row")
        self.vanilla_button = self.builder.get_object("vanilla_button")
        self.gapps_row = self.builder.get_object("gapps_row")
        self.gapps_button = self.builder.get_object("gapps_button")
        self.info_session_row = self.builder.get_object("info_session_row")
        self.info_container_row = self.builder.get_object("info_container_row")
        self.info_version_row = self.builder.get_object("info_version_row")
        self.info_gapps_row = self.builder.get_object("info_gapps_row")
        self.info_ip_row = self.builder.get_object("info_ip_row")
        self.reset_row = self.builder.get_object("reset_row")
        self.reset_button = self.builder.get_object("reset_button")

        self.setup_signals()

    def setup_signals(self):
        # Quick launch
        if self.launch_button:
            self.launch_button.connect("clicked", lambda b: self.delegate.on_launch_clicked())
        if self.launch_row:
            self.launch_row.set_activatable_widget(self.launch_button)

        # Session Switch
        if self.session_switch_row:
            self.session_switch_row.connect("notify::active", self.on_session_switch_toggled)

        # Restart
        if self.restart_button:
            self.restart_button.connect("clicked", lambda b: self.delegate.on_restart_clicked())
        if self.restart_row:
            self.restart_row.set_activatable_widget(self.restart_button)

        # Multi-Window Switch
        if self.multi_window_row:
            self.multi_window_row.connect("notify::active", self.on_multi_window_toggled)

        # APK Install
        if self.install_apk_button:
            self.install_apk_button.connect("clicked", lambda b: self.delegate.on_install_apk_clicked())
        if self.install_apk_row:
            self.install_apk_row.set_activatable_widget(self.install_apk_button)

        # Image downloads
        if self.vanilla_button:
            self.vanilla_button.connect("clicked", lambda b: self.delegate.on_init_clicked('vanilla'))
        if self.gapps_button:
            self.gapps_button.connect("clicked", lambda b: self.delegate.on_init_clicked('gapps'))

        # Reset
        if self.reset_button:
            self.reset_button.connect("clicked", lambda b: self.delegate.on_reset_clicked())
        if self.reset_row:
            self.reset_row.set_activatable_widget(self.reset_button)

        # Status Banner button
        if self.status_banner:
            self.status_banner.connect("button-clicked", lambda b: self.delegate.on_init_clicked('vanilla'))

    def on_session_switch_toggled(self, row, param):
        if self.updating_ui:
            return
        is_active = row.get_active()
        self.delegate.on_session_toggled(is_active)

    def on_multi_window_toggled(self, row, param):
        if self.updating_ui:
            return
        enabled = row.get_active()
        self.delegate.on_multi_window_toggled(enabled)

    def update_status(self, status: dict, multi_window_enabled: bool = False):
        """Update all UI rows with live status data."""
        self.updating_ui = True
        try:
            # Session running state
            session_running = status.get('session_running', False)
            container_running = status.get('container_running', False)
            initialized = status.get('initialized', False)
            has_gapps = status.get('has_gapps', False)

            # Session Switch
            self.session_switch_row.set_active(session_running)
            self.session_switch_row.set_subtitle(
                _("Running (Container Active)") if session_running else _("Stopped")
            )
            self.restart_button.set_sensitive(session_running)
            self.launch_button.set_sensitive(session_running)

            # Multi-window state
            self.multi_window_row.set_active(multi_window_enabled)

            # Banner & Image state
            if initialized:
                self.status_banner.set_revealed(False)
            else:
                self.status_banner.set_title(_("System images not downloaded yet"))
                self.status_banner.set_button_label(_("Download Images"))
                self.status_banner.set_revealed(True)
                self.launch_button.set_sensitive(False)

            # Image download buttons
            self.vanilla_button.set_label(_("Download"))
            self.gapps_button.set_label(_("Download"))
            self.vanilla_button.set_sensitive(True)
            self.gapps_button.set_sensitive(True)

            if initialized:
                if has_gapps:
                    self.gapps_button.set_label(_("Installed"))
                    self.gapps_button.set_sensitive(False)
                    self.vanilla_button.set_label(_("Switch to Vanilla"))
                    self.vanilla_button.set_sensitive(True)
                else:
                    self.vanilla_button.set_label(_("Installed"))
                    self.vanilla_button.set_sensitive(False)
                    self.gapps_button.set_label(_("Switch to GApps"))
                    self.gapps_button.set_sensitive(True)

            # Info Details
            self.info_session_row.set_subtitle(_("Active") if session_running else _("Stopped"))
            self.info_container_row.set_subtitle(_("Active") if container_running else _("Inactive"))
            self.info_version_row.set_subtitle(
                f"Android {status.get('android_version', 'Unknown')}" if initialized else _("Not initialized")
            )
            self.info_ip_row.set_subtitle(status.get('ip_address', 'Not available'))

            if has_gapps:
                self.info_gapps_row.set_subtitle(_("Installed (Google Play Certification)"))
                if self.gapps_info_button is None:
                    self.gapps_info_button = Gtk.Button()
                    self.gapps_info_button.set_icon_name("dialog-information-symbolic")
                    self.gapps_info_button.set_valign(Gtk.Align.CENTER)
                    self.gapps_info_button.add_css_class("flat")
                    self.gapps_info_button.set_tooltip_text(_("Open Google Play Certification Assistant"))
                    self.gapps_info_button.connect("clicked", lambda b: self.delegate.on_show_gapps_cert())
                    self.info_gapps_row.add_suffix(self.gapps_info_button)
            else:
                self.info_gapps_row.set_subtitle(_("Not installed"))
                if self.gapps_info_button is not None:
                    self.info_gapps_row.remove(self.gapps_info_button)
                    self.gapps_info_button = None

        finally:
            self.updating_ui = False
