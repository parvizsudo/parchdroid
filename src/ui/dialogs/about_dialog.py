"""
About Dialog for Parchdroid
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from gettext import gettext as _

def show_about_dialog(parent_window):
    """Present the About dialog/window according to Libadwaita version."""
    if hasattr(Adw, "AboutDialog"):
        dialog = Adw.AboutDialog()
        dialog.set_application_name(_("Android App Support"))
        dialog.set_application_icon("com.parchlinux.parchdroid")
        dialog.set_developer_name(_("Parch Linux"))
        dialog.set_version("1.1.0")
        dialog.set_comments(_("Waydroid manager and Android runtime support for Parch Linux"))
        dialog.set_website("https://parchlinux.com")
        dialog.set_license_type(Gtk.License.AGPL_3_0)
        dialog.add_credit_section(_("Developers"), ["Parch Linux Team", "Sohi"])
        dialog.add_link("Waydroid Documentation", "https://docs.waydro.id/")
        dialog.present(parent_window)
    else:
        about = Adw.AboutWindow(transient_for=parent_window)
        about.set_application_name(_("Android App Support"))
        about.set_application_icon("com.parchlinux.parchdroid")
        about.set_developer_name(_("Parch Linux"))
        about.set_version("1.1.0")
        about.set_comments(_("Waydroid manager and Android runtime support for Parch Linux"))
        about.set_website("https://parchlinux.com")
        about.set_license_type(Gtk.License.AGPL_3_0)
        about.add_credit_section(_("Developers"), ["Parch Linux Team", "Sohi"])
        about.add_link("Waydroid Documentation", "https://docs.waydro.id/")
        about.present()
