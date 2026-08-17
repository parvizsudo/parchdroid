"""
Authentication Dialog for requesting administrative privileges
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from gettext import gettext as _

def prompt_auth_password(parent_window, on_authenticated, on_cancelled):
    """Prompt user for root/sudo password."""
    entry = Adw.PasswordEntryRow()
    entry.set_title(_("Password"))
    
    if hasattr(Adw, "AlertDialog"):
        dialog = Adw.AlertDialog()
        dialog.set_heading(_("Authentication Required"))
        dialog.set_body(_("Administrator privileges are required to perform this action."))
        dialog.set_extra_child(entry)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("auth", _("Authenticate"))
        dialog.set_response_appearance("auth", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("auth")
        dialog.set_close_response("cancel")
        
        def on_response(d, response):
            if response == "auth":
                on_authenticated(entry.get_text())
            else:
                on_cancelled()
                
        dialog.connect("response", on_response)
        entry.connect("activate", lambda e: dialog.response("auth"))
        dialog.present(parent_window)
    else:
        dialog = Adw.MessageDialog(transient_for=parent_window)
        dialog.set_heading(_("Authentication Required"))
        dialog.set_body(_("Administrator privileges are required to perform this action."))
        dialog.set_extra_child(entry)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("auth", _("Authenticate"))
        dialog.set_response_appearance("auth", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("auth")
        dialog.set_close_response("cancel")
        
        def on_response(d, response):
            if response == "auth":
                on_authenticated(entry.get_text())
            else:
                on_cancelled()
                
        dialog.connect("response", on_response)
        entry.connect("activate", lambda e: dialog.response("auth"))
        dialog.present()
