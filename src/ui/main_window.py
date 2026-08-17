"""
Main Window - Modular GTK4/Libadwaita Waydroid Management Window
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
import threading
from gettext import gettext as _

from core.paths import get_ui_path
from core.system_check import SystemChecker
from core.installer import WaydroidInstaller
from core.waydroid_manager import WaydroidManager

from ui.views.checking_view import CheckingView
from ui.views.welcome_view import WelcomeView
from ui.views.manage_view import ManageView
from ui.views.operation_view import OperationView
from ui.dialogs.about_dialog import show_about_dialog
from ui.dialogs.gapps_dialog import GappsRegistrationDialog
from ui.dialogs.auth_dialog import prompt_auth_password

class MainWindow(Adw.ApplicationWindow):
    """Main application window managing navigation and asynchronous operations."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_default_size(920, 720)
        self.set_title(_("Android App Support"))
        self.set_icon_name("phone-symbolic")

        # Business Logic
        self.system_checker = SystemChecker()
        self.installer = None
        self.manager = None
        self.manager_signals_connected = False

        # Load Template
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_ui_path("window.ui"))

        self.toast_overlay = self.builder.get_object("toast_overlay")
        self.view_stack = self.builder.get_object("view_stack")
        self.refresh_button = self.builder.get_object("refresh_button")

        if self.toast_overlay:
            self.set_content(self.toast_overlay)

        # Setup Views
        self.checking_view = CheckingView()
        self.welcome_view = WelcomeView(on_install_callback=self.on_install_clicked)
        self.manage_view = ManageView(delegate=self)
        self.operation_view = OperationView(
            on_cancel_callback=self.on_operation_cancel,
            on_done_callback=self.on_operation_done
        )

        self.view_stack.add_named(self.checking_view, "checking")
        self.view_stack.add_named(self.welcome_view, "welcome")
        self.view_stack.add_named(self.manage_view, "manage")
        self.view_stack.add_named(self.operation_view, "operation")

        self.setup_actions()
        self.setup_signals()

        # Initial check
        self.view_stack.set_visible_child_name("checking")
        GLib.timeout_add(100, self.perform_system_check)

    def setup_actions(self):
        """Setup GActions for window and application menu."""
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", lambda a, p: show_about_dialog(self))
        self.add_action(about_action)

    def setup_signals(self):
        if self.refresh_button:
            self.refresh_button.connect("clicked", lambda b: self.perform_system_check())

    def show_toast(self, message: str):
        """Display a toast notification."""
        if self.toast_overlay:
            toast = Adw.Toast.new(message)
            toast.set_timeout(3)
            self.toast_overlay.add_toast(toast)

    def ensure_manager(self):
        """Instantiate WaydroidManager and connect signals once."""
        if not self.manager:
            self.manager = WaydroidManager()
        if not self.manager_signals_connected:
            self.manager.connect('output', self.on_operation_output)
            self.manager.connect('status', self.on_operation_status)
            self.manager.connect('progress', self.on_operation_progress)
            self.manager.connect('completed', self.on_operation_completed)
            self.manager.connect('password-required', self.on_password_required)
            self.manager_signals_connected = True

    # ----------------------------- System Checking -----------------------------
    def perform_system_check(self):
        """Run system inspection in a background thread."""
        def check_thread():
            result = self.system_checker.check_all()
            multi_win = False
            status = {}
            if result['waydroid_installed']:
                self.ensure_manager()
                status = self.manager.get_status()
                multi_win = self.manager.get_multi_window_enabled()
            GLib.idle_add(self.on_system_check_complete, result, status, multi_win)

        threading.Thread(target=check_thread, daemon=True).start()
        return False

    def on_system_check_complete(self, result: dict, status: dict, multi_win: bool):
        """Update active view after system check."""
        if result['waydroid_installed']:
            self.manage_view.update_status(status, multi_win)
            self.view_stack.set_visible_child_name("manage")
        else:
            self.welcome_view.update_status(result)
            self.view_stack.set_visible_child_name("welcome")

    # ----------------------------- Operations & Tasks -----------------------------
    def on_install_clicked(self):
        """Confirm and start Waydroid package installation."""
        result = self.system_checker.get_last_result()
        if not result or not result.get('system_compatible'):
            self.show_toast(_("No installation source available for this system."))
            return

        if hasattr(Adw, "AlertDialog"):
            dialog = Adw.AlertDialog()
            dialog.set_heading(_("Install Waydroid?"))
            dialog.set_body(_("Waydroid will be installed from system repositories.\n\nThis process may take a few minutes."))
            dialog.add_response("cancel", _("Cancel"))
            dialog.add_response("install", _("Install"))
            dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
            dialog.set_default_response("install")
            dialog.set_close_response("cancel")
            dialog.connect("response", lambda d, r: self.start_installation() if r == "install" else None)
            dialog.present(self)
        else:
            dialog = Adw.MessageDialog(transient_for=self)
            dialog.set_heading(_("Install Waydroid?"))
            dialog.set_body(_("Waydroid will be installed from system repositories.\n\nThis process may take a few minutes."))
            dialog.add_response("cancel", _("Cancel"))
            dialog.add_response("install", _("Install"))
            dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
            dialog.set_default_response("install")
            dialog.set_close_response("cancel")
            dialog.connect("response", lambda d, r: self.start_installation() if r == "install" else None)
            dialog.present()

    def start_installation(self):
        self.view_stack.set_visible_child_name("operation")
        self.operation_view.prepare_operation(_("Installing Waydroid…"))

        self.installer = WaydroidInstaller()
        self.installer.connect('output', self.on_operation_output)
        self.installer.connect('status', self.on_operation_status)
        self.installer.connect('progress', self.on_operation_progress)
        self.installer.connect('completed', self.on_installation_completed)
        self.installer.connect('password-required', self.on_password_required)

        threading.Thread(target=self.installer.install, args=('extra',), daemon=True).start()

    def on_launch_clicked(self):
        self.ensure_manager()
        if self.manager.launch_ui():
            self.show_toast(_("Waydroid launched"))
        else:
            self.show_toast(_("Failed to launch Waydroid"))

    def on_session_toggled(self, is_active: bool):
        self.ensure_manager()
        if is_active:
            self.view_stack.set_visible_child_name("operation")
            self.operation_view.prepare_operation(_("Starting Waydroid Session…"))
            threading.Thread(target=self.manager.start_session, daemon=True).start()
        else:
            def stop_thread():
                success = self.manager.stop_session()
                GLib.idle_add(lambda: self.show_toast(_("Waydroid stopped") if success else _("Failed to stop Waydroid")))
                GLib.idle_add(self.perform_system_check)
            threading.Thread(target=stop_thread, daemon=True).start()

    def on_restart_clicked(self):
        if hasattr(Adw, "AlertDialog"):
            dialog = Adw.AlertDialog()
            dialog.set_heading(_("Restart Waydroid Session?"))
            dialog.set_body(_("This will restart the Waydroid container and active display session."))
            dialog.add_response("cancel", _("Cancel"))
            dialog.add_response("restart", _("Restart"))
            dialog.set_response_appearance("restart", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_default_response("restart")
            dialog.set_close_response("cancel")
            dialog.connect("response", lambda d, r: self.start_restart_session() if r == "restart" else None)
            dialog.present(self)
        else:
            dialog = Adw.MessageDialog(transient_for=self)
            dialog.set_heading(_("Restart Waydroid Session?"))
            dialog.set_body(_("This will restart the Waydroid container and active display session."))
            dialog.add_response("cancel", _("Cancel"))
            dialog.add_response("restart", _("Restart"))
            dialog.set_response_appearance("restart", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_default_response("restart")
            dialog.set_close_response("cancel")
            dialog.connect("response", lambda d, r: self.start_restart_session() if r == "restart" else None)
            dialog.present()

    def start_restart_session(self):
        self.ensure_manager()
        self.view_stack.set_visible_child_name("operation")
        self.operation_view.prepare_operation(_("Restarting Waydroid Session…"))
        threading.Thread(target=self.manager.restart_session, daemon=True).start()

    def on_toggle_multi_window(self, enabled: bool):
        self.ensure_manager()
        def toggle_task():
            success = self.manager.set_multi_window_enabled(enabled)
            GLib.idle_add(lambda: self.show_toast(_("Multi-window updated. Restart session to apply.") if success else _("Failed to update setting")))
        threading.Thread(target=toggle_task, daemon=True).start()

    def on_install_apk_clicked(self):
        dialog = Gtk.FileDialog()
        dialog.set_title(_("Select APK File"))

        apk_filter = Gtk.FileFilter()
        apk_filter.set_name(_("Android APK files"))
        apk_filter.add_pattern("*.apk")

        all_filter = Gtk.FileFilter()
        all_filter.set_name(_("All files"))
        all_filter.add_pattern("*")

        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        filter_list.append(apk_filter)
        filter_list.append(all_filter)

        dialog.set_filters(filter_list)
        dialog.set_default_filter(apk_filter)
        dialog.open(self, None, self.on_apk_file_selected)

    def on_apk_file_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                apk_path = file.get_path()
                self.start_apk_install(apk_path)
        except Exception as e:
            if "dismissed" not in str(e).lower():
                self.show_toast(f"{_('Error selecting file:')} {e}")

    def start_apk_install(self, apk_path: str):
        self.ensure_manager()
        self.view_stack.set_visible_child_name("operation")
        self.operation_view.prepare_operation(_("Installing APK…"))
        threading.Thread(target=self.manager.install_apk, args=(apk_path,), daemon=True).start()

    def on_init_clicked(self, image_type: str):
        self.ensure_manager()
        status = self.manager.get_status()
        if status.get('initialized'):
            # Confirm overwrite
            if hasattr(Adw, "AlertDialog"):
                dialog = Adw.AlertDialog()
                dialog.set_heading(_("Reinitialize Waydroid?"))
                dialog.set_body(_(f"This will download fresh {image_type} images and replace existing container data.\n\nAll Android data will be reset."))
                dialog.add_response("cancel", _("Cancel"))
                dialog.add_response("reinit", _("Reinitialize"))
                dialog.set_response_appearance("reinit", Adw.ResponseAppearance.DESTRUCTIVE)
                dialog.set_default_response("cancel")
                dialog.set_close_response("cancel")
                dialog.connect("response", lambda d, r: self.start_initialization(image_type, True) if r == "reinit" else None)
                dialog.present(self)
            else:
                dialog = Adw.MessageDialog(transient_for=self)
                dialog.set_heading(_("Reinitialize Waydroid?"))
                dialog.set_body(_(f"This will download fresh {image_type} images and replace existing container data.\n\nAll Android data will be reset."))
                dialog.add_response("cancel", _("Cancel"))
                dialog.add_response("reinit", _("Reinitialize"))
                dialog.set_response_appearance("reinit", Adw.ResponseAppearance.DESTRUCTIVE)
                dialog.set_default_response("cancel")
                dialog.set_close_response("cancel")
                dialog.connect("response", lambda d, r: self.start_initialization(image_type, True) if r == "reinit" else None)
                dialog.present()
        else:
            self.start_initialization(image_type, False)

    def start_initialization(self, image_type: str, force: bool):
        self.ensure_manager()
        self.view_stack.set_visible_child_name("operation")
        self.operation_view.prepare_operation(_(f"Initializing Waydroid ({image_type})…"))
        threading.Thread(target=self.manager.initialize, args=(image_type, force), daemon=True).start()

    def on_reset_clicked(self):
        type_row = Adw.ComboRow()
        type_row.set_title(_("Image Variant"))
        model = Gio.ListStore.new(Gtk.StringObject)
        model.append(Gtk.StringObject.new("vanilla"))
        model.append(Gtk.StringObject.new("gapps"))
        type_row.set_model(model)
        type_row.set_selected(0)

        if hasattr(Adw, "AlertDialog"):
            dialog = Adw.AlertDialog()
            dialog.set_heading(_("Reset Waydroid?"))
            dialog.set_body(_("This will delete all container data and reinitialize with new system images."))
            dialog.set_extra_child(type_row)
            dialog.add_response("cancel", _("Cancel"))
            dialog.add_response("reset", _("Reset Data"))
            dialog.set_response_appearance("reset", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_default_response("cancel")
            dialog.set_close_response("cancel")
            dialog.connect("response", lambda d, r: self.start_initialization(type_row.get_selected_item().get_string(), True) if r == "reset" else None)
            dialog.present(self)
        else:
            dialog = Adw.MessageDialog(transient_for=self)
            dialog.set_heading(_("Reset Waydroid?"))
            dialog.set_body(_("This will delete all container data and reinitialize with new system images."))
            dialog.set_extra_child(type_row)
            dialog.add_response("cancel", _("Cancel"))
            dialog.add_response("reset", _("Reset Data"))
            dialog.set_response_appearance("reset", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_default_response("cancel")
            dialog.set_close_response("cancel")
            dialog.connect("response", lambda d, r: self.start_initialization(type_row.get_selected_item().get_string(), True) if r == "reset" else None)
            dialog.present()

    def on_show_gapps_cert(self):
        self.ensure_manager()
        dialog = GappsRegistrationDialog(self, self.manager)
        dialog.present()

    # ----------------------------- Signal Handlers -----------------------------
    def on_operation_output(self, source, text: str):
        GLib.idle_add(self.operation_view.append_output, text)

    def on_operation_status(self, source, status: str):
        GLib.idle_add(self.operation_view.set_status_text, status)

    def on_operation_progress(self, source, fraction: float):
        GLib.idle_add(self.operation_view.set_progress, fraction)

    def on_operation_completed(self, source, success: bool):
        GLib.idle_add(self.operation_view.finish_operation, success)

    def on_installation_completed(self, installer, success: bool):
        def finalize():
            self.operation_view.finish_operation(
                success,
                _("✓ Installation Complete!") if success else _("✗ Installation Failed")
            )
            self.show_toast(_("Waydroid installed successfully") if success else _("Installation failed"))
        GLib.idle_add(finalize)

    def on_password_required(self, source):
        def ask():
            prompt_auth_password(
                self,
                on_authenticated=lambda pwd: self.provide_password(pwd),
                on_cancelled=self.on_operation_cancel
            )
        GLib.idle_add(ask)

    def provide_password(self, password: str):
        if self.installer:
            self.installer.provide_password(password)
        if self.manager:
            self.manager.provide_password(password)

    def on_operation_cancel(self):
        if self.installer:
            self.installer.cancel()
        if self.manager:
            self.manager.cancel()

    def on_operation_done(self):
        self.view_stack.set_visible_child_name("checking")
        GLib.timeout_add(300, self.perform_system_check)
