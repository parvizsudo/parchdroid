"""
Operation View - Real-time terminal output, progress tracking, and operation feedback
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

try:
    gi.require_version('Vte', '3.91')
    from gi.repository import Vte, Pango
    HAS_VTE = True
except (ValueError, ImportError):
    try:
        gi.require_version('Vte', '2.91')
        from gi.repository import Vte, Pango
        HAS_VTE = True
    except (ValueError, ImportError):
        HAS_VTE = False

from gi.repository import Gtk, Adw, GLib
from gettext import gettext as _
from core.paths import get_ui_path

class OperationView(Adw.Bin):
    """View managing live terminal output and progress for async tasks."""

    def __init__(self, on_cancel_callback, on_done_callback):
        super().__init__()
        self.on_cancel_callback = on_cancel_callback
        self.on_done_callback = on_done_callback

        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_ui_path("view_operation.ui"))

        root = None
        for obj in self.builder.get_objects():
            if isinstance(obj, Adw.Clamp):
                root = obj
                break
        self.set_child(root)

        self.status_spinner = self.builder.get_object("status_spinner")
        self.status_label = self.builder.get_object("status_label")
        self.progress_bar = self.builder.get_object("progress_bar")
        self.terminal_frame = self.builder.get_object("terminal_frame")
        self.cancel_button = self.builder.get_object("cancel_button")
        self.done_button = self.builder.get_object("done_button")

        self.setup_terminal()
        self.setup_signals()

    def setup_terminal(self):
        """Setup VTE terminal or GtkTextView fallback."""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        if HAS_VTE:
            self.terminal = Vte.Terminal()
            self.terminal.set_font(Pango.FontDescription("Monospace 11"))
            self.terminal.set_scroll_on_output(True)
            self.terminal.set_scrollback_lines(10000)
            scrolled.set_child(self.terminal)
            self.text_view = None
            self.text_buffer = None
        else:
            self.terminal = None
            self.text_view = Gtk.TextView()
            self.text_view.set_editable(False)
            self.text_view.set_monospace(True)
            self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
            self.text_view.set_left_margin(12)
            self.text_view.set_right_margin(12)
            self.text_view.set_top_margin(12)
            self.text_view.set_bottom_margin(12)
            self.text_buffer = self.text_view.get_buffer()
            scrolled.set_child(self.text_view)

        self.terminal_frame.set_child(scrolled)

    def setup_signals(self):
        if self.cancel_button:
            self.cancel_button.connect("clicked", lambda b: self.on_cancel_callback())
        if self.done_button:
            self.done_button.connect("clicked", lambda b: self.on_done_callback())

    def prepare_operation(self, title: str):
        """Reset terminal and progress indicators for a new operation."""
        if HAS_VTE and self.terminal:
            self.terminal.reset(True, True)
        elif self.text_buffer:
            self.text_buffer.set_text("")

        self.status_label.set_text(title)
        self.status_spinner.set_visible(True)
        self.status_spinner.start()
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_show_text(False)
        self.progress_bar.pulse()
        self.cancel_button.set_visible(True)
        self.done_button.set_visible(False)

    def append_output(self, text: str):
        """Append output line to terminal/console."""
        if HAS_VTE and self.terminal:
            self.terminal.feed(text.encode('utf-8'))
        elif self.text_buffer and self.text_view:
            end_iter = self.text_buffer.get_end_iter()
            self.text_buffer.insert(end_iter, text)
            mark = self.text_buffer.get_insert()
            self.text_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)

    def set_status_text(self, status: str):
        """Update operation title text."""
        self.status_label.set_text(status)

    def set_progress(self, fraction: float):
        """Update progress bar fraction or pulse."""
        if fraction < 0:
            self.progress_bar.pulse()
        else:
            self.progress_bar.set_fraction(fraction)
            self.progress_bar.set_show_text(True)

    def finish_operation(self, success: bool, message: str = None):
        """Mark operation as completed or failed."""
        self.status_spinner.stop()
        self.status_spinner.set_visible(False)
        self.cancel_button.set_visible(False)
        self.done_button.set_visible(True)

        if success:
            self.progress_bar.set_fraction(1.0)
            status_text = message or _("✓ Operation Complete!")
        else:
            status_text = message or _("✗ Operation Failed")

        self.status_label.set_text(status_text)
